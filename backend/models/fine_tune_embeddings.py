import os
import time
import subprocess
import urllib.request
import urllib.error
import chromadb
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

try:
    import ollama
except ImportError:
    print("Error: The 'ollama' Python library is not installed. Run 'pip install ollama'")
    exit(1)

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = "documents"
BASE_MODEL = "all-MiniLM-L6-v2"
OLLAMA_MODEL = "mistral"  # You must have pulled this via 'ollama pull mistral'
OUTPUT_DIR = os.path.join(BASE_DIR, "custom_embedding_model")

def generate_synthetic_queries(chunks, num_samples=50):
    print(f"\n[PHASE 1] Generating synthetic training pairs using local Ollama ({OLLAMA_MODEL})...")
    print("-> This is running 100% OFFLINE. The LLM is reading your chunks and writing test questions.")
    
    training_data = []
    
    # We limit to num_samples so you don't wait hours for your first test
    target_chunks = chunks[:num_samples]
    
    for i, chunk in enumerate(target_chunks):
        prompt = (
            "You are an expert data assistant. Read the following text chunk "
            "and generate exactly ONE specific question that this text perfectly answers. "
            "Output ONLY the question, nothing else.\n\n"
            f"Text: {chunk}"
        )
        
        try:
            response = ollama.chat(model=OLLAMA_MODEL, messages=[{'role': 'user', 'content': prompt}])
            
            # Handle different versions of the Ollama Python library
            if hasattr(response, 'message'):
                query = response.message.content.strip()
            else:
                query = response["message"]["content"].strip()
            
            # Basic cleanup of the AI's output
            query = query.replace('"', '').replace('Question:', '').strip()
            
            if query:
                # We create an "InputExample" which is a (Question, Answer Chunk) pair
                training_data.append(InputExample(texts=[query, chunk]))
                print(f"[{i+1}/{len(target_chunks)}] Q: {query}")
        except Exception as e:
            print(f"Failed to generate query for chunk {i}: {e}")
            
    return training_data

def ensure_ollama_running():
    try:
        urllib.request.urlopen('http://127.0.0.1:11434/', timeout=1)
        print("-> Ollama is already running.")
        return
    except urllib.error.URLError:
        pass

    print("-> Ollama is not running. Starting Ollama automatically in the background...")
    try:
        # Start Ollama without blocking the script
        subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait up to 10 seconds for it to boot
        for _ in range(10):
            time.sleep(1)
            try:
                urllib.request.urlopen('http://127.0.0.1:11434/', timeout=1)
                print("-> Ollama started successfully!")
                return
            except urllib.error.URLError:
                continue
                
        print("-> Warning: Tried to start Ollama, but it didn't respond in time. It might still be starting.")
    except Exception as e:
        print(f"-> Error starting Ollama automatically: {e}")
        print("-> Please open a new terminal and type 'ollama serve'")

def main():
    print("==================================================")
    print("  OFFLINE EMBEDDING MODEL FINE-TUNING SCRIPT")
    print("==================================================")
    
    ensure_ollama_running()
    
    # 1. Fetch chunks from your local ChromaDB
    print("\nConnecting to local ChromaDB...")
    if not os.path.exists(CHROMA_DIR):
         print("Error: ChromaDB directory not found. Please upload documents via the frontend first.")
         return

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
    except ValueError:
        print(f"Error: Collection '{COLLECTION_NAME}' not found. Please upload documents first.")
        return
    
    results = collection.get()
    chunks = results.get("documents", [])
    
    if not chunks:
        print("Error: No documents found in ChromaDB. Please upload documents first.")
        return
        
    print(f"-> Successfully grabbed {len(chunks)} document chunks from your local database.")
    
    # 2. Generate Training Pairs
    # (Adjust num_samples higher for better accuracy, lower for faster training)
    train_examples = generate_synthetic_queries(chunks, num_samples=30)
    
    if len(train_examples) < 5:
        print("\nError: Not enough training data generated. Check if Ollama is running.")
        return
        
    # 3. Fine-tune the embedding model
    print(f"\n[PHASE 2] Starting fine-tuning of '{BASE_MODEL}'...")
    print("-> The computer is mathematically adjusting the model to understand your specific data.")
    
    model = SentenceTransformer(BASE_MODEL)
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=8)
    
    # MultipleNegativesRankingLoss pushes matching questions/chunks together, and unrelated ones apart
    train_loss = losses.MultipleNegativesRankingLoss(model=model)
    
    # Train the model
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=3, # 3 passes over the data
        warmup_steps=10,
        show_progress_bar=True
    )
    
    # 4. Save the custom model
    print(f"\n[PHASE 3] Training complete! Saving your absolutely unique custom model...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    model.save(OUTPUT_DIR)
    print(f"-> Saved to: {OUTPUT_DIR}")
    
    print("\n==================================================")
    print("SUCCESS! To use your new model, open 'backend/rag_backend.py'")
    print(f"Change line 47 from:")
    print('EMBED_MODEL_NAME = "all-MiniLM-L6-v2"')
    print("To:")
    print('EMBED_MODEL_NAME = "./custom_embedding_model"')
    print("==================================================")

if __name__ == "__main__":
    main()
