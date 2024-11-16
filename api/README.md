## FastAPI-based REST API



This API provides the following key endpoints:

1. **Semantic Search** (`POST /search/semantic`):
   - Search across all documents using semantic similarity
   - Filter by document type
   - Configurable similarity threshold
   - Paginated results

2. **Contextual Search** (`POST /search/contextual`):
   - Search with additional context filters
   - Customer-specific searches
   - Date range filtering
   - Source type filtering

3. **Customer Context** (`GET /context/customer/{customer_id}`):
   - Retrieve comprehensive customer context
   - Recent interactions
   - Active opportunities
   - Company information

4. **Similar Customers** (`GET /similar/customers/{customer_id}`):
   - Find similar customers using embedding similarity
   - Configurable similarity threshold
   - Excludes reference customer

To use this API:

1. Install requirements:
```bash
pip install fastapi uvicorn asyncpg sentence-transformers
```

2. Run the API:
```bash
uvicorn rag_api:app --reload
```

3. Example usage:
```python
import requests

# Semantic search
response = requests.post(
    "http://localhost:8000/search/semantic",
    json={
        "query": "cloud migration concerns",
        "source_type": "interaction",
        "limit": 5
    }
)

# Contextual search
response = requests.post(
    "http://localhost:8000/search/contextual",
    json={
        "query": "pricing discussion",
        "context": {
            "customer_id": "uuid-here",
            "source_types": ["interaction", "opportunity"],
            "start_date": "2024-01-01T00:00:00Z"
        }
    }
)
```



---



## Retrieval patterns— sales-specific capabilities:

1. **Conversation History**

   ```
   (GET /retrieval/conversation-history/{customer_id}):
   ```

   - Chronological interaction history
   - Sentiment analysis over time
   - Speaker identification
   - Interaction type filtering

   

2. **Successful Patterns**

   ```
   (GET /retrieval/successful-patterns/{industry}):
   ```

   - Industry-specific success patterns

   - Statistical analysis of winning approaches

   - Example interactions for each pattern

   - Success rate calculations

     

3. Objection Handling

   ```
   (GET /retrieval/objection-handling/{objection_type}):
   ```

   - Common objection responses
   - Success rates for different approaches
   - Recommended handling strategies
   - Context-aware suggestions

   

4. Competitor Analysis

   ```
   (GET /retrieval/competitor-analysis/{customer_id}):
   ```

   - Competitor mention tracking

   - Sentiment analysis by competitor

   - Historical context

   - Frequency analysis

     

5. **Sales Suggestions**

   ```
   (GET /retrieval/sales-suggestions/{opportunity_id}):
   ```

   - Context-aware recommendations
   - Similar successful deals analysis
   - Risk factors identification
   - Next steps suggestions



