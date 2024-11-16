# How to Use postgres-loader.py

## Prerequisites
1. PostgreSQL database server running
2. Python with required packages (install using `pip install -r requirements.txt`):
   - asyncpg
   - sentence_transformers
   - numpy
   - tqdm
   - python-dotenv
   - pandas
   - faker

## Configuration

### Environment Variables
Create a `.env` file in the root directory with the following configurations:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sales_rag_db
DB_USER=postgres
DB_PASSWORD=postgres

# Model Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Search Configuration
DEFAULT_SEARCH_LIMIT=5
VECTOR_INDEX_LISTS=100
```

These variables can be customized based on your needs:
- `DB_*`: Database connection settings
- `EMBEDDING_MODEL`: The SentenceTransformer model to use for generating embeddings
- `EMBEDDING_DIMENSION`: Dimension of the embedding vectors
- `DEFAULT_SEARCH_LIMIT`: Default number of results to return in searches
- `VECTOR_INDEX_LISTS`: Number of lists for the IVFFLAT index (affects search performance)

## Setup and Usage Guide

### 1. Initialize the Loader
```python
from scripts.postgres_loader import PostgresRAGLoader

# Create loader instance (will use environment variables)
loader = PostgresRAGLoader()

# Or override environment variables with custom settings
loader = PostgresRAGLoader(
    db_url="postgresql://custom_user:custom_pass@custom_host:5432/custom_db",
    embedding_dim=512
)
```

### 2. Using with Synthetic Data Generator

You can use the `SalesDataGenerator` class to generate synthetic data for testing and development:

```python
import asyncio
from scripts.data_generator import SalesDataGenerator
from scripts.postgres_loader import PostgresRAGLoader

async def load_synthetic_data():
    # Initialize the data generator (optionally with a seed for reproducibility)
    generator = SalesDataGenerator(seed=42)
    
    # Generate synthetic dataset
    dataset = generator.generate_dataset(
        num_customers=100,    # Generate 100 customers
        num_sales_people=10   # Generate 10 sales people
    )
    
    # Initialize the PostgresRAGLoader
    loader = PostgresRAGLoader()
    
    # Load the synthetic data into PostgreSQL
    await loader.load_data(dataset)
    
    print("Synthetic data loaded successfully!")

# Run the data loading process
if __name__ == "__main__":
    asyncio.run(load_synthetic_data())
```

This will:
1. Generate a realistic synthetic dataset including:
   - Customer profiles
   - Sales people with performance metrics
   - Interactions and communications
   - Sales opportunities
   - Product catalog
2. Automatically create embeddings for:
   - Customer information (company + industry)
   - Interaction content (notes + topics)
3. Store everything in PostgreSQL with vector search capabilities

### 3. Perform Searches

#### Semantic Search
```python
async def search_documents():
    # Basic semantic search
    results = await loader.semantic_search(
        query="customer interested in cloud solutions",
        source_type="interaction",  # Optional: filter by source type
        limit=5  # Optional: override DEFAULT_SEARCH_LIMIT
    )
    
    for result in results:
        print(f"Content: {result['content']}")
        print(f"Similarity: {result['similarity']}")
        print(f"Metadata: {result['metadata']}")

asyncio.run(search_documents())
```

#### Contextual Search
```python
from datetime import datetime

async def contextual_search():
    # Search with context filters
    results = await loader.contextual_search(
        query="pricing discussion",
        customer_id="uuid-1",  # Optional: filter by customer
        date_range=(  # Optional: filter by date range
            datetime(2024, 1, 1),
            datetime(2024, 12, 31)
        ),
        limit=5  # Optional: override DEFAULT_SEARCH_LIMIT
    )
    
    for result in results:
        print(f"Content: {result['content']}")
        print(f"Similarity: {result['similarity']}")
        print(f"Source Type: {result['source_type']}")

asyncio.run(contextual_search())
```

The script automatically handles:
- Database initialization
- Vector embedding generation
- Data storage
- Efficient similarity searches

Each search returns relevant documents with similarity scores, allowing you to build powerful search functionality into your sales management system.
