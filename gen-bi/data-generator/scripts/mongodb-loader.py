import asyncio
import json
from typing import Dict, List, Any
from datetime import datetime

import motor.motor_asyncio
from pymongo import IndexModel, ASCENDING, TEXT
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

class SalesDataLoader:
    def __init__(
        self,
        mongodb_uri: str = "mongodb://localhost:27017",
        database_name: str = "sales_rag_db"
    ):
        # Initialize MongoDB client
        self.client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
        self.db = self.client[database_name]
        
        # Initialize sentence transformer for embeddings
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Define collections
        self.collections = {
            "salesPeople": self.db.sales_people,
            "customers": self.db.customers,
            "opportunities": self.db.opportunities,
            "interactions": self.db.interactions,
            "products": self.db.products,
            "embeddings": self.db.embeddings
        }

    async def create_indexes(self):
        """Create necessary indexes for efficient querying"""
        # Sales People indexes
        await self.collections["salesPeople"].create_indexes([
            IndexModel([("territories", ASCENDING)]),
            IndexModel([("expertise", ASCENDING)]),
            IndexModel([("demographics.languages", ASCENDING)]),
            IndexModel([("salesMetrics.quotaAttainment", ASCENDING)])
        ])

        # Customers indexes
        await self.collections["customers"].create_indexes([
            IndexModel([("industry", ASCENDING)]),
            IndexModel([("size", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("location.country", ASCENDING)]),
            # Text index for search
            IndexModel([
                ("company", TEXT),
                ("industry", TEXT)
            ])
        ])

        # Opportunities indexes
        await self.collections["opportunities"].create_indexes([
            IndexModel([("customerId", ASCENDING)]),
            IndexModel([("salesPersonId", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("value", ASCENDING)]),
            IndexModel([("expectedCloseDate", ASCENDING)])
        ])

        # Interactions indexes
        await self.collections["interactions"].create_indexes([
            IndexModel([("customerId", ASCENDING)]),
            IndexModel([("salesPersonId", ASCENDING)]),
            IndexModel([("type", ASCENDING)]),
            IndexModel([("timestamp", ASCENDING)]),
            IndexModel([("sentiment", ASCENDING)]),
            # Text index for search
            IndexModel([
                ("notes", TEXT),
                ("topics", TEXT)
            ])
        ])

        # Products indexes
        await self.collections["products"].create_indexes([
            IndexModel([("category", ASCENDING)]),
            IndexModel([("price", ASCENDING)])
        ])

        # Embeddings indexes
        await self.collections["embeddings"].create_indexes([
            IndexModel([("source_type", ASCENDING)]),
            IndexModel([("source_id", ASCENDING)]),
            # Index for vector similarity search
            IndexModel([("embedding", "vector")], 
                      **{"dense_vectors_dimensions": 384})
        ])

    async def generate_and_store_embeddings(
        self,
        document: Dict[str, Any],
        source_type: str,
        source_id: str
    ):
        """Generate and store embeddings for text content"""
        # Combine relevant text fields based on document type
        text_content = ""
        
        if source_type == "interaction":
            text_content = f"{document.get('notes', '')} {' '.join(document.get('topics', []))}"
        elif source_type == "opportunity":
            text_content = f"{document.get('lossReason', '')} {document.get('competitorInvolved', '')}"
        elif source_type == "customer":
            text_content = f"{document.get('company', '')} {document.get('industry', '')}"
        
        if text_content.strip():
            # Generate embedding
            embedding = self.encoder.encode(text_content).tolist()
            
            # Store embedding
            await self.collections["embeddings"].insert_one({
                "source_type": source_type,
                "source_id": source_id,
                "embedding": embedding,
                "text_content": text_content,
                "created_at": datetime.utcnow()
            })

    async def load_data(self, dataset: Dict[str, List[Dict]]):
        """Load data into MongoDB with embeddings"""
        # Clear existing data
        await asyncio.gather(*[
            collection.delete_many({})
            for collection in self.collections.values()
        ])

        # Create indexes
        await self.create_indexes()

        # Load data and generate embeddings
        for collection_name, data in dataset.items():
            if collection_name not in self.collections:
                continue

            # Insert data
            if data:
                await self.collections[collection_name].insert_many(data)
                
                # Generate embeddings for relevant collections
                if collection_name in ["interactions", "opportunities", "customers"]:
                    for document in tqdm(
                        data,
                        desc=f"Generating embeddings for {collection_name}"
                    ):
                        await self.generate_and_store_embeddings(
                            document,
                            collection_name.rstrip('s'),
                            document['id']
                        )

    async def create_example_queries(self):
        """Create example queries to demonstrate RAG capabilities"""
        
        # Similar customer search
        async def find_similar_customers(company_id: str, limit: int = 5):
            # Get company embeddings
            company_embedding = await self.collections["embeddings"].find_one(
                {"source_type": "customer", "source_id": company_id}
            )
            
            if company_embedding:
                # Find similar companies using vector similarity
                similar = await self.collections["embeddings"].aggregate([
                    {
                        "$vectorSearch": {
                            "queryVector": company_embedding["embedding"],
                            "path": "embedding",
                            "numCandidates": 100,
                            "limit": limit + 1,  # +1 to exclude self
                            "index": "vector_index",
                        }
                    },
                    {
                        "$match": {
                            "source_type": "customer",
                            "source_id": {"$ne": company_id}
                        }
                    }
                ]).to_list(length=limit)
                
                return similar

        # Successful sales pattern analysis
        async def analyze_successful_patterns(
            opportunity_id: str,
            limit: int = 5
        ):
            # Get opportunity details
            opportunity = await self.collections["opportunities"].find_one(
                {"id": opportunity_id}
            )
            
            if opportunity:
                # Find similar successful opportunities
                similar_successful = await self.collections["opportunities"].find({
                    "status": "won",
                    "value": {
                        "$gte": opportunity["value"] * 0.8,
                        "$lte": opportunity["value"] * 1.2
                    },
                    "id": {"$ne": opportunity_id}
                }).limit(limit).to_list(length=limit)
                
                # Analyze interaction patterns
                for opp in similar_successful:
                    opp["interactions"] = await self.collections["interactions"].find({
                        "customerId": opp["customerId"]
                    }).sort("timestamp", 1).to_list(length=None)
                
                return similar_successful

        return {
            "find_similar_customers": find_similar_customers,
            "analyze_successful_patterns": analyze_successful_patterns
        }

    async def setup_rag_queries(self):
        """Set up common RAG queries"""
        
        async def semantic_search(
            query: str,
            collection_type: str = None,
            limit: int = 5
        ):
            """Search across embeddings using semantic similarity"""
            query_embedding = self.encoder.encode(query).tolist()
            
            match_stage = (
                {"source_type": collection_type}
                if collection_type
                else {}
            )
            
            results = await self.collections["embeddings"].aggregate([
                {
                    "$vectorSearch": {
                        "queryVector": query_embedding,
                        "path": "embedding",
                        "numCandidates": 100,
                        "limit": limit,
                        "index": "vector_index",
                    }
                },
                {"$match": match_stage},
                {
                    "$lookup": {
                        "from": f"{collection_type}s",
                        "localField": "source_id",
                        "foreignField": "id",
                        "as": "source_document"
                    }
                }
            ]).to_list(length=limit)
            
            return results

        async def contextual_search(
            query: str,
            customer_id: str = None,
            date_range: tuple = None,
            limit: int = 5
        ):
            """Search with additional context filters"""
            base_query = await semantic_search(query, limit=limit * 2)
            
            filtered_results = []
            for result in base_query:
                if customer_id and result.get("customerId") != customer_id:
                    continue
                    
                if date_range:
                    start_date, end_date = date_range
                    doc_date = datetime.fromisoformat(
                        result.get("timestamp", "").replace("Z", "+00:00")
                    )
                    if not (start_date <= doc_date <= end_date):
                        continue
                        
                filtered_results.append(result)
                if len(filtered_results) >= limit:
                    break
            
            return filtered_results

        return {
            "semantic_search": semantic_search,
            "contextual_search": contextual_search
        }

async def main():
    # Initialize loader
    loader = SalesDataLoader()
    
    # Load sample data
    with open("sales_data.json", "r") as f:
        dataset = json.load(f)
    
    # Load data and create embeddings
    await loader.load_data(dataset)
    
    # Set up example queries
    example_queries = await loader.create_example_queries()
    rag_queries = await loader.setup_rag_queries()
    
    # Example usage
    customer_id = dataset["customers"][0]["id"]
    similar_customers = await example_queries["find_similar_customers"](
        customer_id
    )
    
    opportunity_id = dataset["opportunities"][0]["id"]
    success_patterns = await example_queries["analyze_successful_patterns"](
        opportunity_id
    )
    
    # Example RAG queries
    semantic_results = await rag_queries["semantic_search"](
        "customer interested in cloud solutions",
        collection_type="interaction"
    )
    
    contextual_results = await rag_queries["contextual_search"](
        "pricing concerns",
        customer_id=customer_id,
        date_range=(
            datetime.now() - timedelta(days=30),
            datetime.now()
        )
    )

if __name__ == "__main__":
    asyncio.run(main())
