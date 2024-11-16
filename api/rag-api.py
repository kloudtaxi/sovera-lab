from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

import asyncpg
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

app = FastAPI(
    title="Sales RAG API",
    description="REST API for Sales RAG System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models for request/response
class SearchResult(BaseModel):
    source_type: str
    source_id: UUID
    content: str
    similarity: float
    metadata: Dict[str, Any]
    
class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    query: str
    
class ContextFilter(BaseModel):
    customer_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source_types: Optional[List[str]] = None
    min_similarity: Optional[float] = Field(default=0.5, ge=0, le=1)

class CustomerContext(BaseModel):
    recent_interactions: List[Dict[str, Any]]
    active_opportunities: List[Dict[str, Any]]
    company_info: Dict[str, Any]

# Database and embedding configuration
class RAGConfig:
    def __init__(self):
        self.db_url = "postgresql://postgres:postgres@localhost:5432/sales_rag_db"
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.pool: Optional[asyncpg.Pool] = None

    async def get_pool(self) -> asyncpg.Pool:
        if not self.pool:
            self.pool = await asyncpg.create_pool(self.db_url)
        return self.pool

    async def get_embedding(self, text: str) -> List[float]:
        return self.encoder.encode(text).tolist()

config = RAGConfig()

# Dependency for database connection
async def get_db():
    pool = await config.get_pool()
    return pool

@app.post("/search/semantic", response_model=SearchResponse)
async def semantic_search(
    query: str,
    source_type: Optional[str] = None,
    limit: int = Query(default=5, ge=1, le=50),
    min_similarity: float = Query(default=0.5, ge=0, le=1),
    pool: asyncpg.Pool = Depends(get_db)
):
    """
    Perform semantic search across documents
    
    - **query**: Search query text
    - **source_type**: Filter by document type (customer, interaction, opportunity)
    - **limit**: Maximum number of results
    - **min_similarity**: Minimum similarity threshold
    """
    try:
        query_embedding = await config.get_embedding(query)
        
        where_clauses = ["1 - (embedding <=> $1::vector) >= $2"]
        params = [query_embedding, min_similarity]
        param_idx = 3
        
        if source_type:
            where_clauses.append(f"source_type = ${param_idx}")
            params.append(source_type)
        
        results = await pool.fetch(f"""
            SELECT 
                source_type,
                source_id,
                content,
                metadata,
                1 - (embedding <=> $1::vector) as similarity
            FROM document_embeddings
            WHERE {' AND '.join(where_clauses)}
            ORDER BY similarity DESC
            LIMIT {limit}
        """, *params)
        
        return SearchResponse(
            results=[SearchResult(**dict(r)) for r in results],
            total=len(results),
            query=query
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search/contextual", response_model=SearchResponse)
async def contextual_search(
    query: str,
    context: ContextFilter,
    limit: int = Query(default=5, ge=1, le=50),
    pool: asyncpg.Pool = Depends(get_db)
):
    """
    Perform contextual search with filters
    
    - **query**: Search query text
    - **context**: Filtering options (customer, date range, source types)
    - **limit**: Maximum number of results
    """
    try:
        query_embedding = await config.get_embedding(query)
        
        where_clauses = [
            "1 - (embedding <=> $1::vector) >= $2"
        ]
        params = [query_embedding, context.min_similarity]
        param_idx = 3
        
        if context.customer_id:
            where_clauses.append(f"source_id = ${param_idx}")
            params.append(context.customer_id)
            param_idx += 1
            
        if context.start_date and context.end_date:
            where_clauses.append(
                f"created_at BETWEEN ${param_idx} AND ${param_idx+1}"
            )
            params.extend([context.start_date, context.end_date])
            param_idx += 2
            
        if context.source_types:
            where_clauses.append(
                f"source_type = ANY(${param_idx}::text[])"
            )
            params.append(context.source_types)
            
        results = await pool.fetch(f"""
            SELECT 
                source_type,
                source_id,
                content,
                metadata,
                1 - (embedding <=> $1::vector) as similarity
            FROM document_embeddings
            WHERE {' AND '.join(where_clauses)}
            ORDER BY similarity DESC
            LIMIT {limit}
        """, *params)
        
        return SearchResponse(
            results=[SearchResult(**dict(r)) for r in results],
            total=len(results),
            query=query
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/context/customer/{customer_id}", response_model=CustomerContext)
async def get_customer_context(
    customer_id: UUID,
    pool: asyncpg.Pool = Depends(get_db)
):
    """
    Get comprehensive customer context
    
    - **customer_id**: UUID of the customer
    Returns recent interactions, opportunities, and company info
    """
    try:
        # Get customer info
        customer = await pool.fetchrow("""
            SELECT * FROM customers WHERE id = $1
        """, customer_id)
        
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Get recent interactions
        interactions = await pool.fetch("""
            SELECT 
                i.*,
                sp.name as sales_person_name
            FROM interactions i
            JOIN sales_people sp ON i.sales_person_id = sp.id
            WHERE i.customer_id = $1
            ORDER BY i.created_at DESC
            LIMIT 5
        """, customer_id)
        
        # Get active opportunities
        opportunities = await pool.fetch("""
            SELECT * FROM opportunities
            WHERE customer_id = $1
            AND status NOT IN ('won', 'lost')
            ORDER BY created_at DESC
        """, customer_id)
        
        return CustomerContext(
            recent_interactions=[dict(i) for i in interactions],
            active_opportunities=[dict(o) for o in opportunities],
            company_info=dict(customer)
        )
        
    except asyncpg.PostgresError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/similar/customers/{customer_id}", response_model=List[Dict[str, Any]])
async def find_similar_customers(
    customer_id: UUID,
    limit: int = Query(default=5, ge=1, le=20),
    min_similarity: float = Query(default=0.5, ge=0, le=1),
    pool: asyncpg.Pool = Depends(get_db)
):
    """
    Find similar customers based on embeddings
    
    - **customer_id**: UUID of the reference customer
    - **limit**: Maximum number of similar customers to return
    - **min_similarity**: Minimum similarity threshold
    """
    try:
        # Get reference customer embedding
        reference = await pool.fetchrow("""
            SELECT embedding
            FROM document_embeddings
            WHERE source_type = 'customer'
            AND source_id = $1
        """, customer_id)
        
        if not reference:
            raise HTTPException(
                status_code=404,
                detail="Reference customer not found"
            )
        
        # Find similar customers
        similar = await pool.fetch("""
            WITH similar_customers AS (
                SELECT 
                    source_id,
                    1 - (embedding <=> $1::vector) as similarity
                FROM document_embeddings
                WHERE source_type = 'customer'
                AND source_id != $2
                AND 1 - (embedding <=> $1::vector) >= $3
                ORDER BY similarity DESC
                LIMIT $4
            )
            SELECT 
                c.*,
                sc.similarity
            FROM similar_customers sc
            JOIN customers c ON c.id = sc.source_id
            ORDER BY sc.similarity DESC
        """, reference['embedding'], customer_id, min_similarity, limit)
        
        return [dict(r) for r in similar]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
