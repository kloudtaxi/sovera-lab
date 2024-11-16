import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Any

import asyncpg
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PostgresRAGLoader:
    def __init__(
        self,
        db_url: str = None,
        embedding_dim: int = None
    ):
        # Construct database URL from environment variables if not provided
        self.db_url = db_url or f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        self.embedding_dim = embedding_dim or int(os.getenv('EMBEDDING_DIMENSION', 384))
        self.encoder = SentenceTransformer(os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2'))
        self.default_search_limit = int(os.getenv('DEFAULT_SEARCH_LIMIT', 5))
        self.vector_index_lists = int(os.getenv('VECTOR_INDEX_LISTS', 100))

    async def init_db(self, pool: asyncpg.Pool):
        """Initialize database with required extensions and tables"""
        async with pool.acquire() as conn:
            # Enable required extensions
            await conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
            
            # Create tables
            await conn.execute(f"""
                -- Base tables for sales data
                CREATE TABLE IF NOT EXISTS customers (
                    id UUID PRIMARY KEY,
                    company_name TEXT NOT NULL,
                    industry TEXT,
                    size TEXT,
                    status TEXT,
                    annual_revenue NUMERIC,
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS sales_people (
                    id UUID PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    territories TEXT[],
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS interactions (
                    id UUID PRIMARY KEY,
                    customer_id UUID REFERENCES customers(id),
                    sales_person_id UUID REFERENCES sales_people(id),
                    type TEXT,
                    notes TEXT,
                    sentiment TEXT,
                    topics TEXT[],
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS opportunities (
                    id UUID PRIMARY KEY,
                    customer_id UUID REFERENCES customers(id),
                    sales_person_id UUID REFERENCES sales_people(id),
                    status TEXT,
                    value NUMERIC,
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );

                -- Vector storage for RAG
                CREATE TABLE IF NOT EXISTS document_embeddings (
                    id UUID PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    source_id UUID NOT NULL,
                    content TEXT,
                    embedding vector({self.embedding_dim}),
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)

            # Create indexes
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_customers_industry ON customers(industry);
                CREATE INDEX IF NOT EXISTS idx_interactions_customer ON interactions(customer_id);
                CREATE INDEX IF NOT EXISTS idx_opportunities_status ON opportunities(status);
                CREATE INDEX IF NOT EXISTS idx_embeddings_source ON document_embeddings(source_type, source_id);
                CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON document_embeddings 
                    USING ivfflat (embedding vector_cosine_ops) WITH (lists = {self.vector_index_lists});
            """)

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        return self.encoder.encode(text).tolist()

    async def store_document_with_embedding(
        self,
        pool: asyncpg.Pool,
        source_type: str,
        source_id: str,
        content: str,
        metadata: Dict = None
    ):
        """Store document with its embedding"""
        embedding = await self.generate_embedding(content)
        
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO document_embeddings 
                    (id, source_type, source_id, content, embedding, metadata)
                VALUES 
                    (gen_random_uuid(), $1, $2, $3, $4, $5)
            """, source_type, source_id, content, embedding, json.dumps(metadata or {}))

    async def load_data(self, dataset: Dict[str, List[Dict]]):
        """Load sales data and generate embeddings"""
        pool = None
        try:
            pool = await asyncpg.create_pool(self.db_url)
            
            # Initialize database
            await self.init_db(pool)
            
            async with pool.acquire() as conn:
                # Load customers
                for customer in tqdm(dataset["customers"], desc="Loading customers"):
                    await conn.execute("""
                        INSERT INTO customers 
                            (id, company_name, industry, size, status, 
                             annual_revenue, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, 
                        customer["id"], 
                        customer["company"],
                        customer["industry"],
                        customer["size"],
                        customer["status"],
                        customer["annualRevenue"],
                        json.dumps({"contacts": customer["contacts"]})
                    )
                    
                    # Generate embedding for customer
                    content = f"{customer['company']} {customer['industry']}"
                    await self.store_document_with_embedding(
                        pool, 
                        "customer",
                        customer["id"],
                        content,
                        {"size": customer["size"]}
                    )

                # Load interactions with embeddings
                for interaction in tqdm(dataset["interactions"], desc="Loading interactions"):
                    await conn.execute("""
                        INSERT INTO interactions 
                            (id, customer_id, sales_person_id, type, 
                             notes, sentiment, topics, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                        interaction["id"],
                        interaction["customerId"],
                        interaction["salesPersonId"],
                        interaction["type"],
                        interaction["notes"],
                        interaction["sentiment"],
                        interaction["topics"],
                        json.dumps({"outcome": interaction["outcome"]})
                    )
                    
                    # Generate embedding for interaction
                    content = f"{interaction['notes']} {' '.join(interaction['topics'])}"
                    await self.store_document_with_embedding(
                        pool,
                        "interaction",
                        interaction["id"],
                        content,
                        {"type": interaction["type"], "sentiment": interaction["sentiment"]}
                    )
        finally:
            if pool:
                await pool.close()

    async def semantic_search(
        self,
        query: str,
        source_type: str = None,
        limit: int = None
    ) -> List[Dict]:
        """Perform semantic search across documents"""
        pool = None
        try:
            pool = await asyncpg.create_pool(self.db_url)
            query_embedding = await self.generate_embedding(query)
            limit = limit or self.default_search_limit
            
            async with pool.acquire() as conn:
                # Build query
                where_clause = "WHERE source_type = $3" if source_type else ""
                params = [query_embedding, limit]
                if source_type:
                    params.append(source_type)
                
                # Execute search
                results = await conn.fetch(f"""
                    SELECT 
                        source_type,
                        source_id,
                        content,
                        metadata,
                        1 - (embedding <=> $1::vector) as similarity
                    FROM document_embeddings
                    {where_clause}
                    ORDER BY similarity DESC
                    LIMIT $2
                """, *params)
                
                return [dict(r) for r in results]
        finally:
            if pool:
                await pool.close()

    async def contextual_search(
        self,
        query: str,
        customer_id: str = None,
        date_range: tuple = None,
        limit: int = None
    ) -> List[Dict]:
        """Perform contextual search with filters"""
        pool = None
        try:
            pool = await asyncpg.create_pool(self.db_url)
            query_embedding = await self.generate_embedding(query)
            limit = limit or self.default_search_limit
            
            async with pool.acquire() as conn:
                # Build query conditions
                conditions = []
                params = [query_embedding, limit]
                param_idx = 3
                
                if customer_id:
                    conditions.append(f"source_id = ${param_idx}")
                    params.append(customer_id)
                    param_idx += 1
                
                if date_range:
                    start_date, end_date = date_range
                    conditions.append(
                        f"created_at BETWEEN ${param_idx} AND ${param_idx+1}"
                    )
                    params.extend([start_date, end_date])
                    param_idx += 2
                
                where_clause = (
                    "WHERE " + " AND ".join(conditions)
                    if conditions
                    else ""
                )
                
                # Execute search
                results = await conn.fetch(f"""
                    SELECT 
                        source_type,
                        source_id,
                        content,
                        metadata,
                        1 - (embedding <=> $1::vector) as similarity
                    FROM document_embeddings
                    {where_clause}
                    ORDER BY similarity DESC
                    LIMIT $2
                """, *params)
                
                return [dict(r) for r in results]
        finally:
            if pool:
                await pool.close()

async def main():
    # Example usage
    loader = PostgresRAGLoader()
    
    # Load sample data
    with open("sales_data.json", "r") as f:
        dataset = json.load(f)
    
    # Load data and create embeddings
    await loader.load_data(dataset)
    
    # Example searches
    results = await loader.semantic_search(
        "customer interested in cloud solutions",
        source_type="interaction"
    )
    
    contextual_results = await loader.contextual_search(
        "pricing discussion",
        customer_id="some-uuid",
        date_range=(
            datetime.now().replace(month=1),
            datetime.now()
        )
    )

if __name__ == "__main__":
    asyncio.run(main())
