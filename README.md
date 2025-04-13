# RAG Application

This is a Retrieval-Augmented Generation (RAG) application with a Python backend and React frontend.

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
   python rag_api.py
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