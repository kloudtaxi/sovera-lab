# Add these new endpoints to the previous FastAPI app

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from uuid import UUID
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

# New Models
class InteractionType(str, Enum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    DEMO = "demo"

class ConversationTurn(BaseModel):
    speaker: str
    content: str
    timestamp: datetime
    sentiment: Optional[str]
    
class SalesPattern(BaseModel):
    pattern_type: str
    frequency: int
    avg_success_rate: float
    example_interactions: List[Dict[str, Any]]

class ObjectionResponse(BaseModel):
    objection_type: str
    successful_responses: List[Dict[str, Any]]
    success_rate: float
    recommended_approach: str

class CompetitorMention(BaseModel):
    competitor_name: str
    mention_count: int
    context: List[Dict[str, Any]]
    sentiment_distribution: Dict[str, float]

# Create a router for new endpoints
router = APIRouter(prefix="/retrieval", tags=["Advanced Retrieval"])

@router.get("/conversation-history/{customer_id}", response_model=List[ConversationTurn])
async def get_conversation_history(
    customer_id: UUID,
    days: int = Query(default=30, ge=1, le=365),
    interaction_types: Optional[List[InteractionType]] = Query(default=None),
    pool: asyncpg.Pool = Depends(get_db)
):
    """
    Retrieve conversation history with sentiment analysis
    
    - **customer_id**: Target customer UUID
    - **days**: Number of days to look back
    - **interaction_types**: Filter by specific interaction types
    """
    try:
        where_clauses = ["customer_id = $1"]
        params = [customer_id]
        param_idx = 2
        
        if interaction_types:
            where_clauses.append(f"type = ANY(${param_idx}::text[])")
            params.append([t.value for t in interaction_types])
            param_idx += 1
        
        cutoff_date = datetime.now() - timedelta(days=days)
        where_clauses.append(f"created_at >= ${param_idx}")
        params.append(cutoff_date)
        
        conversations = await pool.fetch(f"""
            WITH RECURSIVE conversation_thread AS (
                SELECT 
                    i.id,
                    i.type,
                    i.notes as content,
                    i.created_at as timestamp,
                    i.sentiment,
                    sp.name as sales_person,
                    ROW_NUMBER() OVER (
                        PARTITION BY DATE(i.created_at) 
                        ORDER BY i.created_at
                    ) as turn_number
                FROM interactions i
                JOIN sales_people sp ON i.sales_person_id = sp.id
                WHERE {' AND '.join(where_clauses)}
            )
            SELECT 
                CASE 
                    WHEN turn_number % 2 = 1 THEN 'sales_person'
                    ELSE 'customer'
                END as speaker,
                content,
                timestamp,
                sentiment,
                type
            FROM conversation_thread
            ORDER BY timestamp ASC
        """, *params)
        
        return [
            ConversationTurn(
                speaker=conv['speaker'],
                content=conv['content'],
                timestamp=conv['timestamp'],
                sentiment=conv['sentiment']
            ) for conv in conversations
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/successful-patterns/{industry}", response_model=List[SalesPattern])
async def get_successful_patterns(
    industry: str,
    min_success_rate: float = Query(default=0.6, ge=0, le=1),
    days: int = Query(default=90, ge=1, le=365),
    pool: asyncpg.Pool = Depends(get_db)
):
    """
    Identify successful sales patterns for a specific industry
    
    - **industry**: Target industry
    - **min_success_rate**: Minimum success rate threshold
    - **days**: Analysis timeframe in days
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        patterns = await pool.fetch("""
            WITH successful_interactions AS (
                SELECT 
                    i.type,
                    i.notes,
                    i.topics,
                    i.sentiment,
                    o.status as outcome,
                    COUNT(*) as frequency,
                    AVG(CASE WHEN o.status = 'won' THEN 1 ELSE 0 END) as success_rate
                FROM interactions i
                JOIN opportunities o ON i.customer_id = o.customer_id
                JOIN customers c ON i.customer_id = c.id
                WHERE 
                    c.industry = $1
                    AND i.created_at >= $2
                GROUP BY 
                    i.type,
                    i.notes,
                    i.topics,
                    i.sentiment,
                    o.status
                HAVING 
                    AVG(CASE WHEN o.status = 'won' THEN 1 ELSE 0 END) >= $3
            )
            SELECT 
                type as pattern_type,
                COUNT(*) as frequency,
                AVG(success_rate) as avg_success_rate,
                ARRAY_AGG(
                    jsonb_build_object(
                        'notes', notes,
                        'topics', topics,
                        'sentiment', sentiment
                    )
                ) as example_interactions
            FROM successful_interactions
            GROUP BY type
            ORDER BY frequency DESC
        """, industry, cutoff_date, min_success_rate)
        
        return [SalesPattern(**pattern) for pattern in patterns]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/objection-handling/{objection_type}", response_model=ObjectionResponse)
async def get_objection_handling(
    objection_type: str = Query(
        ...,
        description="Type of objection (e.g., pricing, timeline, technical)"
    ),
    pool: asyncpg.Pool = Depends(get_db)
):
    """
    Retrieve successful responses to common sales objections
    
    - **objection_type**: Category of objection
    Returns successful handling approaches with success rates
    """
    try:
        responses = await pool.fetchrow("""
            WITH objection_responses AS (
                SELECT 
                    i.notes,
                    i.next_steps,
                    i.sentiment,
                    o.status as outcome,
                    COUNT(*) as frequency
                FROM interactions i
                JOIN opportunities o ON i.customer_id = o.customer_id
                WHERE 
                    $1 = ANY(i.topics)
                    AND o.status IN ('won', 'lost')
                GROUP BY 
                    i.notes,
                    i.next_steps,
                    i.sentiment,
                    o.status
            )
            SELECT 
                $1 as objection_type,
                jsonb_agg(
                    jsonb_build_object(
                        'response', notes,
                        'next_steps', next_steps,
                        'sentiment', sentiment
                    )
                ) FILTER (WHERE outcome = 'won') as successful_responses,
                AVG(CASE WHEN outcome = 'won' THEN 1 ELSE 0 END) as success_rate,
                MODE() WITHIN GROUP (ORDER BY notes) FILTER (WHERE outcome = 'won') 
                    as recommended_approach
            FROM objection_responses
        """, objection_type)
        
        if not responses:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for objection type: {objection_type}"
            )
        
        return ObjectionResponse(**dict(responses))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/competitor-analysis/{customer_id}", response_model=List[CompetitorMention])
async def analyze_competitor_mentions(
    customer_id: UUID,
    days: int = Query(default=90, ge=1, le=365),
    min_mentions: int = Query(default=2, ge=1),
    pool: asyncpg.Pool = Depends(get_db)
):
    """
    Analyze competitor mentions in customer interactions
    
    - **customer_id**: Target customer UUID
    - **days**: Analysis timeframe in days
    - **min_mentions**: Minimum mentions threshold
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        competitor_analysis = await pool.fetch("""
            WITH competitor_mentions AS (
                SELECT 
                    e.metadata->>'competitor' as competitor_name,
                    e.content,
                    e.similarity,
                    i.sentiment,
                    i.created_at
                FROM document_embeddings e
                JOIN interactions i ON e.source_id = i.id
                WHERE 
                    i.customer_id = $1
                    AND i.created_at >= $2
                    AND e.metadata->>'competitor' IS NOT NULL
            )
            SELECT 
                competitor_name,
                COUNT(*) as mention_count,
                jsonb_agg(
                    jsonb_build_object(
                        'content', content,
                        'sentiment', sentiment,
                        'date', created_at
                    )
                ) as context,
                jsonb_object_agg(
                    sentiment,
                    ROUND(
                        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (
                            PARTITION BY competitor_name
                        ),
                        2
                    )
                ) as sentiment_distribution
            FROM competitor_mentions
            GROUP BY competitor_name
            HAVING COUNT(*) >= $3
            ORDER BY mention_count DESC
        """, customer_id, cutoff_date, min_mentions)
        
        return [CompetitorMention(**analysis) for analysis in competitor_analysis]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add a route for retrieving contextual sales suggestions
@router.get("/sales-suggestions/{opportunity_id}")
async def get_sales_suggestions(
    opportunity_id: UUID,
    pool: asyncpg.Pool = Depends(get_db)
):
    """
    Get AI-powered sales suggestions based on opportunity context
    
    - **opportunity_id**: Target opportunity UUID
    Returns personalized suggestions for next steps
    """
    try:
        context = await pool.fetchrow("""
            WITH opportunity_context AS (
                SELECT 
                    o.*,
                    c.industry,
                    c.size,
                    jsonb_agg(
                        DISTINCT jsonb_build_object(
                            'type', i.type,
                            'sentiment', i.sentiment,
                            'topics', i.topics
                        )
                    ) as recent_interactions
                FROM opportunities o
                JOIN customers c ON o.customer_id = c.id
                LEFT JOIN interactions i ON o.customer_id = i.customer_id
                WHERE o.id = $1
                GROUP BY o.id, c.id
            )
            SELECT 
                oc.*,
                (
                    SELECT jsonb_agg(
                        jsonb_build_object(
                            'status', so.status,
                            'value', so.value,
                            'next_steps', si.next_steps
                        )
                    )
                    FROM opportunities so
                    JOIN interactions si ON so.customer_id = si.customer_id
                    WHERE 
                        so.status = 'won'
                        AND so.id != $1
                        AND so.value BETWEEN oc.value * 0.8 AND oc.value * 1.2
                    LIMIT 5
                ) as similar_successful_deals
            FROM opportunity_context oc
        """, opportunity_id)
        
        if not context:
            raise HTTPException(
                status_code=404,
                detail="Opportunity not found"
            )
            
        # Analyze context and generate suggestions
        suggestions = {
            "next_steps": [],
            "talking_points": [],
            "risk_factors": [],
            "recommended_content": []
        }
        
        # Add suggestion logic based on context patterns
        recent_sentiments = [
            i['sentiment'] 
            for i in context['recent_interactions']
        ]
        recent_topics = [
            topic
            for i in context['recent_interactions']
            for topic in i['topics']
        ]
        
        # Example suggestion generation
        if 'negative' in recent_sentiments:
            suggestions['next_steps'].append(
                "Schedule follow-up meeting to address concerns"
            )
            
        if 'pricing' in recent_topics:
            suggestions['talking_points'].extend([
                "Emphasize ROI calculations",
                "Share relevant case studies",
                "Discuss flexible payment options"
            ])
            
        if context['value'] > 100000:
            suggestions['risk_factors'].append(
                "High-value deal - ensure executive sponsorship"
            )
            
        # Add similar successful deals analysis
        if context['similar_successful_deals']:
            common_next_steps = [
                deal['next_steps']
                for deal in context['similar_successful_deals']
                if deal['next_steps']
            ]
            suggestions['next_steps'].extend(common_next_steps)
        
        return suggestions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add to the main FastAPI app
app.include_router(router)
