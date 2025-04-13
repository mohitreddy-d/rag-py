from pymongo import MongoClient
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Configuration
MONGODB_URI = os.getenv('MONGODB_URI')
DB_NAME = 'rag'
COLLECTION_NAME = 'documents'

# Connect to MongoDB Atlas
client = MongoClient(MONGODB_URI)
database = client[DB_NAME]
collection = database[COLLECTION_NAME]

# Generate a unique index name using timestamp
index_name = f"vector_index_{int(time.time())}"

from pymongo.operations import SearchIndexModel

# Create vector search index model
search_index_model = SearchIndexModel(
    name=index_name,
    definition={
        "fields": [{
            "type": "vector",
            "path": "embedding",
            "numDimensions": 1536,
            "similarity": "dotProduct",
            "quantization": "scalar"
        }]
    },
    type="vectorSearch"
)

try:
    # Create the search index
    result = collection.create_search_index(model=search_index_model)
    print("Created new vector search index")
    
    # Wait for the index to be ready
    print("Waiting for index to be ready...")
    while True:
        indexes = list(collection.list_search_indexes())
        if indexes and indexes[0].get("status") == "READY":
            break
        time.sleep(5)
    
    print("✅ Vector search index is ready!")

except Exception as e:
    print(f"Error creating index: {e}")

client.close()