import os
from typing import List
from dotenv import load_dotenv
from redis import Redis
from openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

# Load environment variables
load_dotenv()

# Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INDEX_NAME = "doc_index"

# Initialize clients
redis_client = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def create_index_if_not_exists():
    """Create Redis search index if it doesn't exist."""
    try:
        # Check if index exists
        redis_client.ft(INDEX_NAME).info()
    except:
        # Create the index with vector similarity scoring
        schema = (
            TextField("chunk"),
            TextField("filename"),
            TextField("filepath"),
            TextField("chunk_index"),
            VectorField("embedding",
                       "FLAT",
                       {"TYPE": "FLOAT32",
                        "DIM": 1536,
                        "DISTANCE_METRIC": "COSINE"})
        )
        
        # Create the index
        redis_client.ft(INDEX_NAME).create_index(
            fields=schema,
            definition=IndexDefinition(prefix=["doc:"], index_type=IndexType.HASH)
        )

def process_document(file_path: str) -> List[str]:
    """Process document and split into chunks."""
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    return text_splitter.split_text(text)

def create_embedding(text: str) -> List[float]:
    """Create embedding for a text chunk using OpenAI."""
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def store_document(file_path: str):
    """Process document, create embeddings, and store in Redis."""
    # Ensure index exists
    create_index_if_not_exists()
    
    # Process document into chunks
    chunks = process_document(file_path)
    
    # Create and store embeddings for each chunk
    for i, chunk in enumerate(chunks):
        embedding = create_embedding(chunk)
        
        # Create a unique key for this document chunk
        doc_key = f"doc:{os.path.basename(file_path)}:{i}"
        
        # Store in Redis as a hash
        doc_data = {
            "chunk": chunk,
            "embedding": embedding,
            "filename": os.path.basename(file_path),
            "filepath": file_path,
            "chunk_index": str(i)
        }
        
        redis_client.hset(doc_key, mapping=doc_data)
        print(f"Stored chunk {i} with {len(embedding)} dimensional embedding")

if __name__ == "__main__":
    # Example usage
    file_path = "path/to/your/document.txt"
    if os.path.exists(file_path):
        store_document(file_path)
        print("✅ Document processed and stored successfully!")
    else:
        print("❌ Please provide a valid file path.")