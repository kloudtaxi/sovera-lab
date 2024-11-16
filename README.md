

# Context

This project is a synthetic data generator to showcase capabilities and pre-train models for a RAG use case

**Use Case**: Outbound Sales Company  

Use data that includes, customer, sales person, products purchased, phone, and email history, plus any notes and information about the customer and salesperson (nationality, language, etc...).  This would then allow at a variety of levels to let AI identify patterns, commonalities, outliers that are substantial, and infer a variety of findings.  And then based on this AI can suggest or execute actions that are appropriate, decide who should be called when, what should be offered, generate emails, adjust offers or discounts.  Realize the person being spoken to is not the right contact within the company and the sales person should reach out to someone else.

# Sales RAG System

A Retrieval-Augmented Generation (RAG) system specifically designed for sales intelligence and customer interaction analysis. The system provides advanced retrieval patterns for sales conversations, competitive analysis, and intelligent recommendations.

## 🌟 Features

### Core Functionality
- Semantic search across sales interactions
- Conversation history analysis with sentiment tracking
- Successful sales pattern identification
- Intelligent objection handling suggestions
- Competitor mention analysis
- AI-powered sales recommendations

### Technical Highlights
- Vector similarity search using pgvector
- Async API implementation with FastAPI
- PostgreSQL for robust data storage
- Sentence transformers for semantic embedding
- OpenAPI documentation
- Comprehensive error handling

## 🚀 Getting Started

### Prerequisites

```bash
# Python 3.8+
python --version

# PostgreSQL with vector search capability
postgres --version

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Unix
.\venv\Scripts\activate   # Windows
```

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-repo/sales-rag-system.git
cd sales-rag-system
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up PostgreSQL**
```sql
CREATE DATABASE sales_rag_db;
CREATE EXTENSION IF NOT EXISTS vector;
```

4. **Environment configuration**
```bash
# Create .env file
cp .env.example .env

# Update with your configurations
DATABASE_URL=postgresql://user:password@localhost:5432/sales_rag_db
MODEL_NAME=all-MiniLM-L6-v2
API_KEY=your_api_key
```

### Running the Application

1. **Initialize the database**
```bash
python scripts/init_db.py
```

2. **Start the API server**
```bash
uvicorn app.main:app --reload
```

3. **Access the documentation**
```
API Documentation: http://localhost:8000/docs
OpenAPI Spec: http://localhost:8000/openapi.json
```

## 📚 API Usage

### Basic Examples

1. **Retrieve Conversation History**
```python
import requests

response = requests.get(
    "http://localhost:8000/retrieval/conversation-history/customer-uuid",
    params={
        "days": 30,
        "interaction_types": ["call", "meeting"]
    }
)
```

2. **Get Sales Suggestions**
```python
response = requests.get(
    "http://localhost:8000/retrieval/sales-suggestions/opportunity-uuid"
)
```

3. **Analyze Competitor Mentions**
```python
response = requests.get(
    "http://localhost:8000/retrieval/competitor-analysis/customer-uuid",
    params={
        "days": 90,
        "min_mentions": 2
    }
)
```

### Advanced Usage

```python
# Bulk Analysis Example
response = requests.post(
    "http://localhost:8000/retrieval/bulk-analysis",
    json={
        "customer_ids": ["id1", "id2"],
        "analysis_types": ["conversation", "competitor"],
        "date_range": {
            "start": "2024-01-01T00:00:00Z",
            "end": "2024-03-01T00:00:00Z"
        }
    }
)
```

## 🏗️ Project Structure

```
sales-rag-system/
├── app/
│   ├── main.py            # FastAPI application
│   ├── database.py        # Database configuration
│   ├── models/            # Pydantic models
│   ├── routes/            # API endpoints
│   └── services/          # Business logic
├── scripts/
│   ├── init_db.py         # Database initialization
│   └── generate_data.py   # Sample data generation
├── tests/
│   ├── test_api.py        # API tests
│   └── test_services.py   # Service tests
├── docs/
│   └── openapi.yaml       # OpenAPI specification
├── requirements.txt       # Project dependencies
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | postgresql://localhost:5432/sales_rag_db |
| MODEL_NAME | Sentence transformer model | all-MiniLM-L6-v2 |
| API_KEY | API authentication key | None |
| LOG_LEVEL | Logging level | INFO |

### Database Indexes

The system creates necessary indexes for efficient vector search:
```sql
CREATE INDEX idx_embeddings_vector ON embeddings 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/test_api.py
pytest tests/test_services.py

# Run with coverage
pytest --cov=app tests/
```

## 📈 Performance Considerations

- Use connection pooling for database operations
- Implement caching for frequent queries
- Consider batch processing for bulk operations
- Monitor vector index performance
- Use async operations for I/O-bound tasks

## 🔒 Security

- API authentication using Bearer tokens
- Input validation using Pydantic models
- SQL injection prevention through parameterized queries
- Rate limiting on sensitive endpoints
- CORS configuration for frontend integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📧 Contact

Your Name - your.email@example.com
Project Link: https://github.com/your-repo/sales-rag-system

## 🙏 Acknowledgments

- [Sentence Transformers](https://www.sbert.net/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [pgvector](https://github.com/pgvector/pgvector)
