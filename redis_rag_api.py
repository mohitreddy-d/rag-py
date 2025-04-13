import os
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis import Redis
from redis.commands.search.query import Query as RedisQuery
import numpy as np

# Load environment variables
load_dotenv()

# Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6380))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INDEX_NAME = "doc_index"

# Initialize clients and FastAPI app
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="RAG API Service")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React app's URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize Redis client
redis_client = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True
)

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

class Query(BaseModel):
    question: str
    top_k: int = 3

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

def create_query_embedding(text: str) -> List[float]:
    """Create embedding for the query text."""
    print("hi")
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    print(len(response.data[0].embedding))
    return response.data[0].embedding

def find_similar_chunks(query_embedding: List[float], top_k: int) -> List[Dict]:
    """Find similar chunks using vector similarity search."""
    try:
        # Ensure index exists
        # create_index_if_not_exists()
        
        # Prepare the query with proper vector search syntax
        base_query = f'*=>[KNN {top_k} @embedding $vec_param AS vector_score]'
        query = RedisQuery(base_query)\
            .sort_by('vector_score')\
            .return_fields('chunk', 'filename', 'filepath', 'chunk_index', 'vector_score')\
            .dialect(2)
        
        # Prepare query parameters with proper vector format
        query_params = {'vec_param': np.array(query_embedding, dtype=np.float32).tobytes()}
        
        # Execute the query with error handling
        results = redis_client.ft(INDEX_NAME).search(query, query_params)
        
        if not results.docs:
            print("No matching documents found")
            return []
        
        # Format results
        similar_chunks = [{
            'chunk': doc.chunk,
            'filename': doc.filename,
            'filepath': doc.filepath,
            'chunk_index': doc.chunk_index,
            'score': float(doc.vector_score)
        } for doc in results.docs]
        
        return similar_chunks
        
    except Exception as e:
        print(f"Error in vector search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}")

def generate_response(question: str, context_chunks: List[Dict]) -> str:
    """Generate response using OpenAI with retrieved context."""
    # Prepare context from retrieved chunks
    context = "\n\n".join([chunk["chunk"] for chunk in context_chunks])
    
    # Create prompt with context and question
    prompt = f"""Context information is below:
    {context}
    
    Given the context information and no prior knowledge, answer the following question:
    {question}
    
    Only if the answer cannot be found in the context, say "I don't have enough information to answer this question.
    Try to give as much info as possible. Also add propper line breaks i.e. 'slash n' to the output according to the meaning."""
    
    # Generate response using OpenAI
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    return response.choices[0].message.content

@app.post("/query")
async def query_documents(query: Query):
    print("got request..")
    try:
        # Ensure index exists
        create_index_if_not_exists()
        
        # Create embedding for the query
        query_embedding = create_query_embedding(query.question)
        print(len(query_embedding))
        
        # Find similar chunks
        similar_chunks = find_similar_chunks(query_embedding, query.top_k)
        
        if not similar_chunks:
            raise HTTPException(status_code=404, detail="No relevant documents found")
        
        # Generate response using context
        response = generate_response(query.question, similar_chunks)
        
        return {
            "answer": response,
            "source_chunks": similar_chunks
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)