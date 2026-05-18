from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Enable CORS for the frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    text: str
    followups: list[str]

responses = [
    {
        "keywords": ['rag', 'pipeline', 'retrieval', 'augment', 'generation'],
        "text": "This system uses the RAG pattern. Instead of relying purely on a model's training data, it first retrieves relevant chunks from your personal documents via vector similarity search, then injects that context into the LLM prompt. The result is factually grounded, personalized answers — not hallucinations.",
        "followups": ['How are documents indexed?', 'What embedding model is used?', 'Show me the retrieval pipeline']
    },
    {
        "keywords": ['vector', 'embedding', 'search', 'similarity'],
        "text": "Vector search converts your documents into numerical arrays (embeddings) using a local sentence-transformer model. Each chunk is mapped to a position in vector space — similar concepts end up geometrically close. When you ask a question, it gets embedded the same way and we find the nearest chunks via cosine similarity.",
        "followups": ['How does ChromaDB work?', 'How large are the vectors?', 'Can I add more documents?']
    },
    {
        "keywords": ['chromadb', 'chroma', 'vector store', 'vector database'],
        "text": "ChromaDB is an open-source vector database that stores and indexes your document embeddings locally on disk. When a query comes in, ChromaDB performs fast approximate nearest neighbor (ANN) search to find the most semantically similar chunks. It persists the vectors to disk so your index survives restarts — no cloud, no network calls, fully private.",
        "followups": ['What embedding model is used?', 'Explain the RAG pipeline', 'How are documents indexed?']
    },
    {
        "keywords": ['privacy', 'offline', 'local', 'data', 'private'],
        "text": "Every operation — ingestion, embedding, retrieval, and generation — runs on your local machine using Ollama and ChromaDB. No data ever leaves your device. No API calls, no cloud uploads. Your personal knowledge stays completely under your control.",
        "followups": ['What are the system requirements?', 'How fast is retrieval?', 'Can it handle large files?']
    },
    {
        "keywords": ['summarize', 'summary', 'documents', 'docs'],
        "text": "Based on your indexed documents, the system can generate summaries by retrieving the most representative chunks and synthesizing them through the local LLM. For best results, try asking about specific topics in your documents.",
        "followups": ['Explain the semantic search loop', 'Tell me about the architecture', 'What models are used?']
    },
    {
        "keywords": ['ollama', 'llm', 'model', 'mistral', 'llama'],
        "text": "The system uses Ollama to serve a quantized local LLM — by default Mistral 7B or LLaMA 3. The model handles answer synthesis while the vector search engine handles retrieval. This hybrid approach gives fast, accurate answers while keeping everything private.",
        "followups": ['Can I switch models?', 'How much RAM is needed?', 'What is RAG?']
    },
    {
        "keywords": ['chunk', 'split', 'ingest', 'pdf', 'file', 'document'],
        "text": "Documents are split into overlapping chunks of ~500 tokens with a 50-token overlap. Each chunk is embedded and stored in ChromaDB with source metadata. The system supports PDFs, .txt, .md, and .docx files — all processed entirely offline.",
        "followups": ['What file formats are supported?', 'How are embeddings stored?', 'Can I delete documents?']
    },
    {
        "keywords": ['architecture', 'system', 'structure', 'how does it work'],
        "text": "The system has 4 layers: (1) Ingestion Layer — processes PDFs, notes and text files; (2) Vector Store — ChromaDB for local persistence; (3) Retrieval Engine — matches queries via cosine similarity; (4) Local LLM — Ollama generates context-aware answers. All 100% offline.",
        "followups": ['Tell me about the ingestion layer', 'How is privacy maintained?', 'What is the retrieval engine?']
    },
    {
        "keywords": [],
        "text": "I've processed your query against the active knowledge base. Based on the indexed documents and local vector embeddings, I can retrieve, summarize and cross-reference your personal data entirely offline. What specific component would you like to explore?",
        "followups": ['Explain the RAG pipeline', 'Summarize my documents', 'How does vector search work?']
    }
]

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if len(request.message) > 2000:
        raise HTTPException(status_code=400, detail="Message too long")
    q = request.message.lower().strip()
    if not q:
        return ChatResponse(text=responses[-1]["text"], followups=responses[-1]["followups"])
    for r in responses:
        if any(k in q for k in r["keywords"]):
            return ChatResponse(text=r["text"], followups=r["followups"])
    
    return ChatResponse(text=responses[-1]["text"], followups=responses[-1]["followups"])
