import os
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from pymongo import MongoClient
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_NAME = "rag"
COLLECTION_NAME = "documents"

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

mongo_client = MongoClient(MONGODB_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]
openai_client = OpenAI(api_key=OPENAI_API_KEY)

class Query(BaseModel):
    question: str
    top_k: int = 3

def create_query_embedding(text: str) -> List[float]:
    """Create embedding for the query text."""
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def find_similar_chunks(query_embedding: List[float], top_k: int) -> List[Dict]:
    """Find similar chunks using vector similarity search."""
    indexes = collection.list_indexes()
    for index in indexes:
        print(index)
    print(len(query_embedding))
    similar_chunks = collection.aggregate([
        {
            "$vectorSearch": {
                "index": "vector_index_1744572369",
                "queryVector": query_embedding,
                "path": "embedding",
                "numCandidates": top_k * 10,
                "limit": top_k
            }
        },
        {
            "$project": {
                "_id": 0,
                "chunk": "$chunk",
                "filename": "$filename",
                "filepath": "$filepath",
                "chunk_index": "$chunk_index",
                "score": {"$meta": "searchScore"}
            }
        }
    ])
    # print(list(similar_chunks))
    return list(similar_chunks)

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
    try:
        # Create embedding for the query
        query_embedding = create_query_embedding(query.question)
        
        # Find similar chunks
        similar_chunks = find_similar_chunks(query_embedding, query.top_k)
        # print("----------", similar_chunks)
        
        if not similar_chunks:
            raise HTTPException(status_code=404, detail="No relevant documents found")
        
        # Generate response using context
        response = generate_response(query.question, similar_chunks)
        print(response)
        
        return {
            "answer": response,
            "source_chunks": similar_chunks
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)