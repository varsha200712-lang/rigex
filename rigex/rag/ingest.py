"""
RAG Knowledge Base Ingestion for ResolveAI.
Reads policy files, chunks text semantically, generates embeddings via Gemini,
and persists in ChromaDB (with local JSON vector cache for fallback reliability).
"""

import os
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple
from config.settings import POLICIES_DIR, CHROMA_PERSIST_DIR, EMBEDDING_MODEL, is_api_key_configured


def chunk_policy_text(file_path: Path, chunk_size: int = 500, overlap: int = 100) -> List[Dict[str, Any]]:
    """Read a policy document and split into structured chunks with metadata."""
    if not file_path.exists():
        return []
    
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Split into sections based on numbered or titled paragraphs
    paragraphs = text.split("\n\n")
    chunks = []
    chunk_idx = 1
    
    current_chunk = ""
    current_section = file_path.stem.replace("_", " ").title()

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # Check if line looks like a header/section
        if para.startswith(("#", "1.", "2.", "3.", "4.", "5.", "Q:", "Step")):
            lines = para.split("\n")
            current_section = lines[0].strip()

        if len(current_chunk) + len(para) > chunk_size and len(current_chunk) > 100:
            chunks.append({
                "chunk_id": f"{file_path.stem}_{chunk_idx}",
                "source": file_path.name,
                "section": current_section,
                "text": current_chunk.strip()
            })
            chunk_idx += 1
            # Keep overlap
            current_chunk = para + "\n\n"
        else:
            current_chunk += para + "\n\n"

    if current_chunk.strip():
        chunks.append({
            "chunk_id": f"{file_path.stem}_{chunk_idx}",
            "source": file_path.name,
            "section": current_section,
            "text": current_chunk.strip()
        })

    return chunks


def get_all_policy_chunks() -> List[Dict[str, Any]]:
    """Gather chunks from all 5 policy documents."""
    all_chunks = []
    policy_files = [
        "return_policy.txt",
        "refund_policy.txt",
        "shipping_policy.txt",
        "warranty_policy.txt",
        "faq.txt"
    ]
    for filename in policy_files:
        p_path = POLICIES_DIR / filename
        chunks = chunk_policy_text(p_path)
        all_chunks.extend(chunks)
    return all_chunks


def generate_gemini_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings using official Google GenAI SDK."""
    if not is_api_key_configured():
        return []
    
    try:
        from google import genai
        client = genai.Client()
        embeddings = []
        # Batch in groups of 10
        batch_size = 10
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            for t in batch:
                res = client.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=t
                )
                if hasattr(res, "embedding") and res.embedding:
                    embeddings.append(res.embedding.values)
                elif hasattr(res, "embeddings") and res.embeddings:
                    embeddings.append(res.embeddings[0].values)
                else:
                    embeddings.append([])
        return embeddings
    except Exception as e:
        print(f"Embedding generation error: {e}")
        return []


def index_knowledge_base() -> Tuple[bool, str]:
    """
    Ingest all policy documents and store in ChromaDB and cached index.
    Returns (success: bool, summary: str).
    """
    chunks = get_all_policy_chunks()
    if not chunks:
        return False, "No policy documents found in rag/policies/"

    texts = [c["text"] for c in chunks]
    ids = [c["chunk_id"] for c in chunks]
    metadatas = [{"source": c["source"], "section": c["section"]} for c in chunks]

    # Save lightweight backup JSON vector cache
    backup_path = CHROMA_PERSIST_DIR / "policy_chunks.json"
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)

    # Try ChromaDB ingestion
    chroma_ok = False
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
        collection = client.get_or_create_collection(name="resolveai_policies")

        # Clear existing
        existing_ids = collection.get().get("ids", [])
        if existing_ids:
            collection.delete(ids=existing_ids)

        # Generate embeddings if API key available
        embeddings = generate_gemini_embeddings(texts)
        if embeddings and len(embeddings) == len(texts):
            collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
                embeddings=embeddings
            )
        else:
            # Add without explicit embeddings; chromadb default handles or stored for retrieval
            collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
        chroma_ok = True
    except Exception as e:
        print(f"ChromaDB ingestion note: {e}")

    summary = f"Indexed {len(chunks)} policy chunks from 5 policy files. " + (
        "Stored in ChromaDB vector store." if chroma_ok else "Stored in local policy index."
    )
    return True, summary


if __name__ == "__main__":
    success, msg = index_knowledge_base()
    print("Ingestion result:", success, msg)
