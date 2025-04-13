import os
from typing import List
from dotenv import load_dotenv
from pymongo import MongoClient
from openai import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()

# Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_NAME = "rag"
COLLECTION_NAME = "documents"

# Initialize clients
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]
openai_client = OpenAI(api_key=OPENAI_API_KEY)

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
    """Process document, create embeddings, and store in MongoDB."""
    # Create vector index if it doesn't exist
    try:
        if "embedding_cosine" not in collection.index_information():
            collection.create_index(
                [("embedding", "vectorSearch")],
                name="embedding_cosine",
                **{
                    "vectorSearch": {
                        "numDimensions": 1536,
                        "similarity": "cosine"
                    }
                }
            )
    except Exception as e:
        print(f"Index creation error: {e}")
    
    # Process document into chunks
    chunks = process_document(file_path)
    
    # Create and store embeddings for each chunk
    for chunk in chunks:
        embedding = create_embedding(chunk)
        
        # Store in MongoDB
        doc = {
            "chunk": chunk,
            "embedding": embedding,
            "filename": os.path.basename(file_path),
            "filepath": file_path,
            "chunk_index": chunks.index(chunk)
        }
        collection.insert_one(doc)
        print(f"Stored chunk with {len(embedding)} dimensional embedding")

if __name__ == "__main__":
    # Example usage
    file_path = "path/to/your/document.txt"
    if os.path.exists(file_path):
        store_document(file_path)
        print("✅ Document processed and stored successfully!")
    else:
        print("❌ Please provide a valid file path.")