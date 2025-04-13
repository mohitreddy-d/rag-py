# RAG System with Redis Vector Store

## Redis Setup

### Using Docker

To set up Redis with vector similarity search capabilities, run the following command:

```bash
docker run -d --name redis-stack \
    -p 6379:6379 -p 8001:8001 \
    -e REDIS_ARGS="--requirepass mypassword" \
    redis/redis-stack:latest
```

This command:
- Creates a Redis Stack container with vector search capabilities
- Exposes Redis on port 6379
- Exposes RedisInsight (GUI) on port 8001
- Sets a password for security

### Environment Configuration

Create a `.env` file with the following variables:

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=mypassword
OPENAI_API_KEY=your_openai_api_key
```

## Usage

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Process and store documents:
```python
from redis_embedding_store import store_document

# Store a document
store_document('path/to/your/document.txt')
```

3. Access RedisInsight:
- Open http://localhost:8001 in your browser
- Connect using the configured password

## Features

- Document chunking with configurable size and overlap
- Vector embeddings using OpenAI's text-embedding-3-small model
- Vector similarity search using Redis Stack
- Efficient document storage and retrieval

## Notes

- The system uses Redis Stack which includes RediSearch for vector similarity operations
- Default chunk size is 500 tokens with 50 token overlap
- Embeddings are 1536-dimensional vectors
- Vector similarity uses cosine distance metric

## Project Structure

```
├── Backend (Python)
│   ├── create_index.py
│   ├── create_vector_index.py
│   ├── embedding_store.py
│   └── rag_api.py
└── Frontend (React)
    └── ui/
```

## Prerequisites

- Python 3.x
- Node.js and npm
- MongoDB instance
- OpenAI API key

## Backend Setup

1. Create and activate Python virtual environment:
   ```bash
   python3 -m venv rag-env
   source rag-env/bin/activate  # On Windows: .\rag-env\Scripts\activate
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update the following variables in `.env`:
     - `MONGODB_URI`: Your MongoDB connection string
     - `OPENAI_API_KEY`: Your OpenAI API key

4. Run the backend server:
   ```bash
   python redis_rag_api.py
   ```

## Frontend Setup

1. Navigate to the UI directory:
   ```bash
   cd ui
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser and navigate to `http://localhost:5173`

## Development

- Backend API will be available at `http://localhost:8000`
- Frontend development server runs at `http://localhost:5173`

## Notes

- Make sure both backend and frontend servers are running simultaneously for the application to work
- Keep your `.env` file secure and never commit it to version control
- The application uses MongoDB for storing vector embeddings and OpenAI's API for generating responses