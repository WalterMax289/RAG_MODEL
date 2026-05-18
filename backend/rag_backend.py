import os
import json
import shutil
import tempfile
from pathlib import Path
from typing import Optional
import mimetypes

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import chromadb
from chromadb.config import Settings

# Import DuckDuckGo Search capabilities
try:
    from models.ddgs import perform_web_search, format_web_search_context
except ImportError:
    try:
        from backend.models.ddgs import perform_web_search, format_web_search_context
    except ImportError:
        perform_web_search = None
        format_web_search_context = None

try:
    import ollama
except ImportError:
    ollama = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
CHROMA_DIR = BASE_DIR / "chroma_db"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)

COLLECTION_NAME = "documents"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
OLLAMA_MODEL = "llama2:7b"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

app = FastAPI(title="RAG Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_embedder = None
_chroma_client = None
_collection = None

FALLBACK_RESPONSES = [
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
    }
]


def get_embedder():
    global _embedder
    if _embedder is None and SentenceTransformer is not None:
        _embedder = SentenceTransformer(EMBED_MODEL_NAME)
    return _embedder


def get_chroma():
    global _chroma_client, _collection
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
    if _collection is None:
        _collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def embed_texts(texts):
    embedder = get_embedder()
    if embedder is None:
        raise HTTPException(status_code=500, detail="sentence-transformers not installed")
    return embedder.encode(texts, show_progress_bar=False).tolist()


def chunk_text(text, filename):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + CHUNK_SIZE
        chunk_words = words[start:end]
        chunk_str = " ".join(chunk_words)
        if chunk_str.strip():
            chunks.append((chunk_str, filename))
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def extract_text_from_file(filepath):
    ext = Path(filepath).suffix.lower()
    if ext == ".pdf":
        if PdfReader is None:
            raise HTTPException(status_code=500, detail="PyPDF2 not installed")
        text = ""
        reader = PdfReader(filepath)
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    elif ext == ".docx":
        if Document is None:
            raise HTTPException(status_code=500, detail="python-docx not installed")
        doc = Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs)
    elif ext == ".md":
        return Path(filepath).read_text(encoding="utf-8")
    elif ext == ".txt":
        return Path(filepath).read_text(encoding="utf-8")
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")


def query_ollama(prompt, context, model=None):
    system_prompt = (
        "You are a helpful AI assistant that answers questions based on the provided document context. "
        "Formulate your answers using clean markdown, lists, or code blocks where appropriate. "
        "Strictly base your answers on the provided context. If the context does not contain enough information to answer, say so clearly. "
        "Do not make up information. Be concise and direct."
    )
    full_prompt = f"Context from user's documents:\n{context}\n\nQuestion: {prompt}\n\nAnswer:"

    # True Online Mode routing
    if model == 'online':
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                generation_model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction=system_prompt
                )
                response = generation_model.generate_content(full_prompt)
                return response.text
            except Exception as e:
                print(f"Gemini API error, falling back to local: {e}")
                # Fallback to local will happen below

    # Offline / Local Mode routing
    if ollama is None:
        return "Ollama is not installed. Please install it with `pip install ollama` and run `ollama serve`."

    model_name = OLLAMA_MODEL
    if model and model != 'online' and model != 'offline':
        model_name = model

    # Dynamic self-healing: Auto-detect installed models to prevent model-not-found crashes
    try:
        models_response = ollama.list()
        installed_models = [m.get('name', '') or m.get('model', '') for m in models_response.get('models', [])]
        if installed_models:
            # If default/requested model is not installed, switch to the first available local model
            if model_name not in installed_models and f"{model_name}:latest" not in installed_models:
                # Clean clean match
                clean_installed = [m for m in installed_models if m]
                if clean_installed:
                    model_name = clean_installed[0]
    except Exception as e:
        print(f"Ollama model check error: {e}")

    try:
        response = ollama.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_prompt},
            ],
        )
        banner = ""
        if model == 'online' and not os.environ.get("GEMINI_API_KEY"):
            banner = "💡 *[Online mode fallback to local LLM: Set GEMINI_API_KEY env var to activate Gemini]*\n\n"

        if hasattr(response, 'message'):
            return banner + response.message.content
        return banner + response["message"]["content"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama error: {str(e)} (Tried model '{model_name}')")


class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = None


class ChatResponse(BaseModel):
    text: str
    followups: list[str]


@app.get("/")
async def serve_frontend():
    index_path = FRONTEND_DIR / "copy.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"error": "Frontend not found"}


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if len(request.message) > 2000:
        raise HTTPException(status_code=400, detail="Message too long")
    query = request.message.strip()
    if not query:
        return ChatResponse(text="Please ask a question.", followups=["Upload a document", "Explain RAG", "How does this work?"])

    collection = get_chroma()
    count = collection.count()
    q_lower = query.lower()

    # Pre-check: If user is asking general questions, check pre-programmed fallbacks first
    for r in FALLBACK_RESPONSES:
        if any(k in q_lower for k in r["keywords"]):
            return ChatResponse(text=r["text"], followups=r["followups"])

    is_online_mode = (request.model == 'online')

    if count == 0:
        if is_online_mode and perform_web_search is not None:
            # Perform live Web Search instead of saying empty database
            search_results = perform_web_search(query, max_results=4)
            if search_results:
                context = format_web_search_context(search_results)
                sources = list(set(r["href"] for r in search_results if r.get("href")))
                source_info = f"\n\n_Web Sources: {', '.join(sources[:2])}_" if sources else ""
                
                answer = query_ollama(query, context, request.model)
                answer += source_info
                
                followups = [
                    "Tell me more about these web results.",
                    "Can you find other sources?",
                    "Summarize the web results."
                ]
                return ChatResponse(text=answer, followups=followups)

        return ChatResponse(
            text="No documents have been uploaded yet. Please upload a document (PDF, TXT, MD, or DOCX) using the attachment icon (📎) so I can answer questions about your data. Alternatively, switch to **Online** mode in the header to search the live web!",
            followups=["Upload a document", "Explain the RAG pipeline", "How does vector search work?"],
        )

    query_embedding = embed_texts([query])[0]
    n_results = min(5, count)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )

    retrieved_chunks = results["documents"][0] if results["documents"] else []
    metadatas = results["metadatas"][0] if results["metadatas"] else []
    distances = results["distances"][0] if (results.get("distances") and results["distances"]) else []

    # If the matches are very weak (Cosine distance > 0.70) and Online mode is active, do a web search fallback!
    is_weak_match = len(distances) > 0 and distances[0] > 0.70

    if (not retrieved_chunks or is_weak_match) and is_online_mode and perform_web_search is not None:
        search_results = perform_web_search(query, max_results=4)
        if search_results:
            context = format_web_search_context(search_results)
            sources = list(set(r["href"] for r in search_results if r.get("href")))
            source_info = f"\n\n_Web Sources: {', '.join(sources[:2])}_" if sources else ""
            
            answer = query_ollama(query, context, request.model)
            answer += source_info
            
            followups = [
                "Tell me more about these web results.",
                "Can you find other sources?",
                "How does this compare to local documents?"
            ]
            return ChatResponse(text=answer, followups=followups)

    if not retrieved_chunks:
        return ChatResponse(
            text="I searched your documents but couldn't find any relevant context to answer your question. Try rephrasing, uploading more files, or switching to **Online** mode in the header to search the live web!",
            followups=["Upload more documents", "Summarize my documents", "Explain the RAG pipeline"],
        )

    context = "\n\n---\n\n".join(retrieved_chunks)
    sources = list(set(m.get("source", "unknown") for m in metadatas if m.get("source")))
    source_info = f"\n\n_Sources: {', '.join(sources)}_" if sources else ""

    answer = query_ollama(query, context, request.model)
    answer += source_info

    # Dynamic context-aware follow-up generator
    if "vector" in q_lower or "embedding" in q_lower or "similarity" in q_lower:
        followups = [
            "How does cosine similarity measure similarity?",
            "What embedding model is used to map these documents?",
            "How can I adjust the vector search similarity threshold?"
        ]
    elif "privacy" in q_lower or "local" in q_lower or "offline" in q_lower:
        followups = [
            "Are my document files encrypted on local disk?",
            "Can I completely turn off network access and still chat?",
            "What local models offer the best compromise between speed and RAM?"
        ]
    elif "chromadb" in q_lower or "database" in q_lower or "store" in q_lower:
        followups = [
            "Where is ChromaDB data saved on my machine?",
            "Can I query ChromaDB metadata directly?",
            "How does indexing speed scale with document size?"
        ]
    elif "summary" in q_lower or "summarize" in q_lower:
        followups = [
            "What are the main takeaways from the retrieved sections?",
            "Can you synthesize a list of action items from these sources?",
            "How can I download this summary as markdown?"
        ]
    else:
        source_name = sources[0] if sources else "my documents"
        followups = [
            f"Can you explain what {source_name} says about this in detail?",
            "What are other related sections in this document?",
            "Summarize the key takeaways from these sources."
        ]

    return ChatResponse(text=answer, followups=followups[:3])


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in (".pdf", ".txt", ".md", ".docx"):
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'. Supported: .pdf, .txt, .md, .docx")

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name

        text = extract_text_from_file(temp_path)
        if not text.strip():
            raise HTTPException(status_code=400, detail="File appears to be empty or unreadable")

        dest_path = UPLOAD_DIR / file.filename
        shutil.copy2(temp_path, dest_path)

        chunks = chunk_text(text, file.filename)

        collection = get_chroma()
        existing = collection.get(where={"source": file.filename})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])

        ids = [f"{file.filename}_{i}" for i in range(len(chunks))]
        chunk_texts = [c[0] for c in chunks]
        metadatas = [{"source": file.filename, "chunk": i} for i in range(len(chunks))]

        embeddings = embed_texts(chunk_texts)
        collection.add(
            documents=chunk_texts,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
        )

        return {
            "filename": file.filename,
            "chunks": len(chunks),
            "status": "indexed",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


@app.get("/api/documents")
async def list_documents():
    collection = get_chroma()
    all_docs = collection.get()
    files_seen = {}
    for meta in (all_docs.get("metadatas") or []):
        if meta and "source" in meta:
            src = meta["source"]
            if src not in files_seen:
                fpath = UPLOAD_DIR / src
                size = fpath.stat().st_size if fpath.exists() else 0
                files_seen[src] = {
                    "filename": src,
                    "size": size,
                    "chunks": 0,
                }
            files_seen[src]["chunks"] += 1

    return {"documents": list(files_seen.values())}


@app.delete("/api/documents/{filename:path}")
async def delete_document(filename: str):
    collection = get_chroma()
    existing = collection.get(where={"source": filename})
    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    filepath = UPLOAD_DIR / filename
    if filepath.exists():
        filepath.unlink()

    return {"status": "deleted", "filename": filename}


@app.get("/api/documents/{filename:path}/embeddings")
async def get_document_embeddings(filename: str):
    collection = get_chroma()
    # Fetch embeddings, documents, and metadatas for the specific file
    result = collection.get(
        where={"source": filename},
        include=["embeddings", "documents", "metadatas"]
    )
    
    if not result["ids"]:
        raise HTTPException(status_code=404, detail="Document not found or has no embeddings")
    
    # Format the data for the frontend
    embeddings_data = []
    for i in range(len(result["ids"])):
        embeddings_data.append({
            "id": result["ids"][i],
            "text": result["documents"][i],
            "embedding": result["embeddings"][i],
            "metadata": result["metadatas"][i]
        })
    
    return {
        "filename": filename,
        "total_chunks": len(result["ids"]),
        "dimensions": len(result["embeddings"][0]) if result["embeddings"] else 0,
        "data": embeddings_data
    }


@app.post("/api/clear")
async def clear_all():
    collection = get_chroma()
    all_ids = collection.get()["ids"]
    if all_ids:
        collection.delete(ids=all_ids)
    for f in UPLOAD_DIR.iterdir():
        if f.is_file():
            f.unlink()
    return {"status": "cleared"}app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("rag_backend:app", host="0.0.0.0", port=8000, reload=True)
