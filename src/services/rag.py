#!/usr/bin/env python3
"""Refactored MongoDB RAG toolkit with Python-only fallback retriever.

This version is updated to support:
- MongoDB Atlas Local (Docker) with 'vectorSearch' type indexes.
- Direct connection URI handling for local Docker setups.
- Renamed indexes (vector_index, text_index).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pcre2
import time
from tqdm import tqdm 
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Any

from utils.logging import app_logger
from services.settings import settings_service

import numpy as np
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError, OperationFailure, ServerSelectionTimeoutError

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer

# --- Defaults ---
SUPPORTED_EXTENSIONS = {".txt", ".md", ".json", ".yaml", ".yml", ".csv", ".pdf"}
DEFAULT_ALLOWED_METADATA = ["source", "category", "tags", "file_type", "collection"]
DEFAULT_TEXT_PATHS = ["content", "metadata.source"]

# --- Utility helpers ---

def batched(items: Sequence, batch_size: int) -> Iterable[Sequence]:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    for start in range(0, len(items), batch_size):
        yield items[start: start + batch_size]


def filter_metadata(metadata: Dict, allowed_fields: Sequence[str]) -> Dict:
    allowed = set(allowed_fields)
    return {k: v for k, v in metadata.items() if k in allowed and v not in (None, "")}


# --- RRF fusion ---

def reciprocal_rank_fusion(runs: Sequence[List[Dict]], k: int, limit: int) -> List[Dict]:
    scores: Dict[str, float] = defaultdict(float)
    docs: Dict[str, Dict] = {}
    for run in runs:
        for rank, doc in enumerate(run):
            doc_id = str(doc.get("_id")) if doc.get("_id") is not None else str(hash(json.dumps(doc, sort_keys=True)))
            docs[doc_id] = doc
            scores[doc_id] += 1.0 / (k + rank + 1)
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [docs[doc_id] for doc_id, _ in ranked[:limit]]


def format_docs(docs: Sequence[Document]) -> str:
    return "\n\n".join(
        f"[{i+1}] Source: {d.metadata.get('source','unknown')}\n{d.page_content}"
        for i, d in enumerate(docs)
    )


# --- RAG class (single programmatic entrypoint) ---

class RAG:
    def __init__(
        self,
        # UPDATED: Added directConnection=true for local Docker compatibility
        mongo_uri: str = "mongodb://localhost:27017/?directConnection=true",
        database: str = "soc_rag_db",
        collection_name: str = "knowledge_base",
        embedding_dim: int = 384,
        embedding_provider: str = "all-MiniLM-L6-v2",
        vector_index: str = "vector_index",
        text_index: str = "text_index",
        text_paths: Sequence[str] = DEFAULT_TEXT_PATHS,
        text_language: str = "english",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        embedding_batch_size: int = 512,
        batch_size: int = 128,
    ) -> None:
        self.mongo_uri = mongo_uri
        self.database = database
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self.embedding_provider = embedding_provider
        self.vector_index = vector_index
        self.text_index = text_index
        self.text_paths = list(text_paths)
        self.text_language = text_language
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_batch_size = embedding_batch_size
        self.batch_size = batch_size

        self.client: Optional[MongoClient] = None
        self.collection: Optional[Collection] = None
        self._embedding_model: Optional[SentenceTransformer] = None

    # --- Connection / index helpers ---
    def connect(self) -> MongoClient:
        if self.client is None:
            try:
                # serverSelectionTimeoutMS prevents hanging if Docker is down
                client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
                client.admin.command("ping")
                self.client = client
            except ServerSelectionTimeoutError as exc:
                app_logger.log_message("log", f"Unable to reach MongoDB at {self.mongo_uri}: {exc}", "ERROR")
                raise
        return self.client

    def _ensure_collection(self) -> Collection:
        if self.collection is None:
            client = self.connect()
            self.collection = client[self.database][self.collection_name]
        return self.collection

    def init(self) -> None:
        coll = self._ensure_collection()
        self.ensure_text_index(coll, self.text_index, self.text_paths, self.text_language)
        self.ensure_vector_index(coll, self.vector_index, self.embedding_dim)
        app_logger.log_message("log", "RAG initialization complete", "INFO")

    # --- Embeddings ---
    def get_embedding_model(self) -> SentenceTransformer:
        if self._embedding_model is None:
            app_logger.log_message("log", f"Loading SentenceTransformer: {self.embedding_provider}", "INFO")
            self._embedding_model = SentenceTransformer(self.embedding_provider)
        return self._embedding_model

    def generate_embeddings(self, texts: Sequence[str], show_progress: bool = False) -> List[List[float]]:
        embedder = self.get_embedding_model()
        embeddings = embedder.encode(texts, show_progress_bar=show_progress)
        return np.asarray(embeddings).tolist()

    # Cosine similarity for fallback
    def cosine(self, a, b):
        a = np.asarray(a, dtype=float)
        b = np.asarray(b, dtype=float)
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        return float(a.dot(b) / denom) if denom > 0 else 0.0

    # --- Document loading / chunking ---
    def load_documents(self, input_path: Path) -> List[Document]:
        from langchain_community.document_loaders import JSONLoader, PyPDFLoader, TextLoader

        def load_file(path: Path) -> List[Document]:
            suffix = path.suffix.lower()
            if suffix not in SUPPORTED_EXTENSIONS:
                return []
            
            try:
                if suffix in {".txt", ".md", ".yaml", ".yml"}:
                    loader = TextLoader(str(path), encoding="utf-8")
                    docs = loader.load()
                elif suffix == ".json":
                    loader = JSONLoader(str(path), jq_schema=".", text_content=False)
                    docs = loader.load()
                elif suffix == ".csv":
                    content = path.read_text(encoding="utf-8")
                    docs = [Document(page_content=content, metadata={})]
                elif suffix == ".pdf":
                    loader = PyPDFLoader(str(path))
                    docs = loader.load()
                else:
                    docs = []
            except Exception as e:
                app_logger.log_message("log", f"Failed to load {path}: {e}", "WARNING")
                return []

            for doc in docs:
                doc.metadata.setdefault("source", path.name)
                doc.metadata.setdefault("file_path", str(path))
                doc.metadata.setdefault("file_type", suffix.lstrip("."))
            return docs

        path = input_path
        if path.is_file():
            return load_file(path)
        docs: List[Document] = []
        for file_path in path.rglob("*"):
            if file_path.is_file():
                docs.extend(load_file(file_path))
        return docs

    def chunk_documents(self, docs: List[Document]) -> List[Document]:
        splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        return splitter.split_documents(docs)

    def chunk_to_record(self, chunk: Document, embedding: List[float], provider: str, allowed_metadata: Sequence[str]) -> Dict:
        metadata = filter_metadata(dict(chunk.metadata or {}), allowed_metadata)
        metadata.setdefault("source", chunk.metadata.get("source", "unknown"))
        metadata.setdefault("file_type", chunk.metadata.get("file_type", "text"))
        
        content = chunk.page_content.strip()
        content_hash = hashlib.sha1(content.encode("utf-8")).hexdigest()

        return {
            "_id": content_hash,
            "chunk_id": content_hash,
            "content": content,
            "metadata": metadata,
            "embedding": embedding,
            "embedding_provider": provider,
            "created_at": datetime.utcnow(),
            "hash": content_hash,
        }

    # --- Ingest ---
    def ingest(self, input_path: Path, category: Optional[str] = None, dry_run: bool = False, allowed_metadata: Sequence[str] = DEFAULT_ALLOWED_METADATA) -> int:
        coll = self._ensure_collection()
        docs = self.load_documents(input_path)
        if not docs:
            app_logger.log_message("log", f"No documents found under {input_path}", "WARNING")
            return 0
        chunks = self.chunk_documents(docs)
        if not chunks:
            app_logger.log_message("log", "No chunks produced", "WARNING")
            return 0
        app_logger.log_message("log", f"Loaded {len(docs)} docs -> {len(chunks)} chunks", "INFO")

        # Delta check
        content_hashes = [hashlib.sha1(c.page_content.encode("utf-8")).hexdigest() for c in chunks]
        existing_ids: set[str] = set()
        
        # Check existence in batches
        check_batch_size = 5000
        for i in range(0, len(content_hashes), check_batch_size):
            batch = content_hashes[i: i + check_batch_size]
            if not batch: continue
            for doc in coll.find({"_id": {"$in": batch}}, {"_id": 1}):
                existing_ids.add(doc["_id"])
        
        chunks_to_embed = [chunk for chunk, h in zip(chunks, content_hashes) if h not in existing_ids]
        if not chunks_to_embed:
            app_logger.log_message("log", "All chunks already exist; skipping ingest", "INFO")
            return 0

        mongo_batch: List[Dict] = []
        inserted = 0

        for chunk_batch in tqdm(batched(chunks_to_embed, self.embedding_batch_size)):
            texts = [c.page_content for c in chunk_batch]
            embeddings = self.generate_embeddings(texts, show_progress=False)
            
            for chunk, embedding in zip(chunk_batch, embeddings):
                if category:
                    chunk.metadata["category"] = category
                mongo_batch.append(self.chunk_to_record(chunk, embedding, self.embedding_provider, allowed_metadata))
                
                if len(mongo_batch) >= self.batch_size:
                    if not dry_run:
                        try:
                            res = coll.insert_many(mongo_batch, ordered=False)
                            inserted += len(res.inserted_ids)
                        except BulkWriteError as exc:
                            inserted += exc.details.get("nInserted", 0)
                    else:
                        inserted += len(mongo_batch)
                    mongo_batch.clear()

        if mongo_batch and not dry_run:
            try:
                res = coll.insert_many(mongo_batch, ordered=False)
                inserted += len(res.inserted_ids)
            except BulkWriteError as exc:
                inserted += exc.details.get("nInserted", 0)
        elif mongo_batch and dry_run:
            inserted += len(mongo_batch)

        app_logger.log_message("log", f"Ingest complete. {inserted} chunks {'simulated' if dry_run else 'inserted'}", "INFO")
        return inserted

    # --- Python-only fallback ---
    def _py_fallback_retrieve(self, query: str, limit: int = 5, semantic_k: int = 50, keyword_k: int = 50, rrf_k: int = 60, filter_category: Optional[str] = None) -> List[Document]:
        """Fallback retriever that runs locally using retrieved documents."""
        app_logger.log_message("log", "Using Python fallback retriever", "INFO")
        coll = self._ensure_collection()

        query_filter = {}
        if filter_category:
            query_filter["metadata.category"] = filter_category

        # Fetch candidates
        all_docs = list(coll.find(query_filter, {"content": 1, "metadata": 1, "embedding": 1, "_id": 1}).limit(10000))
        if not all_docs:
            return []

        # 1. Semantic Score (Cosine)
        q_emb = self.generate_embeddings([query], show_progress=False)[0]
        for doc in all_docs:
            doc["_sim_score"] = self.cosine(q_emb, doc.get("embedding", [])) if doc.get("embedding") else 0.0

        semantic_top = sorted(all_docs, key=lambda x: x.get("_sim_score", 0.0), reverse=True)[:semantic_k]

        # 2. Keyword Score (Exact Match)
        tokens = set(pcre2.findall(r"\w+", query.lower()))
        for doc in all_docs:
            text = (doc.get("content") or "").lower()
            doc["_kw_score"] = sum(1 for t in tokens if t in text)

        keyword_top = sorted(all_docs, key=lambda x: x.get("_kw_score", 0), reverse=True)[:keyword_k]

        # 3. Fuse
        sem_run = [{"_id": d.get("_id"), "content": d.get("content", ""), "metadata": d.get("metadata", {}), "score": d.get("_sim_score")} for d in semantic_top]
        kw_run = [{"_id": d.get("_id"), "content": d.get("content", ""), "metadata": d.get("metadata", {}), "score": d.get("_kw_score")} for d in keyword_top]

        fused = reciprocal_rank_fusion([sem_run, kw_run], rrf_k, limit)
        return [Document(page_content=d.get("content", ""), metadata=d.get("metadata", {})) for d in fused]

    # --- Retriever (Atlas + Fallback) ---
    class _MongoHybridRetriever:
        def __init__(self, collection: Collection, embedding_fn, embedding_dim: int, vector_index: str, text_index: str, top_k: int, semantic_candidates: int, keyword_candidates: int, rrf_k: int, allowed_text_paths: Sequence[str], filter_category: Optional[str] = None) -> None:
            self.collection = collection
            self.embedding_fn = embedding_fn
            self.vector_index = vector_index
            self.text_index = text_index
            self.top_k = top_k
            self.semantic_candidates = semantic_candidates
            self.keyword_candidates = keyword_candidates
            self.rrf_k = rrf_k
            self.allowed_text_paths = allowed_text_paths
            self.filter_category = filter_category
            self.parent: Optional["RAG"] = None

        def invoke(self, query: str) -> List[Document]:
            qv = self.embedding_fn([query])[0]
            
            vector_results: List[Dict] = []
            text_results: List[Dict] = []

            # 1. Vector Search ($vectorSearch)
            if self.semantic_candidates > 0:
                vector_search_spec = {
                    "index": self.vector_index,
                    "path": "embedding",
                    "queryVector": qv,
                    "numCandidates": self.semantic_candidates,
                    "limit": self.top_k,
                }
                if self.filter_category:
                    vector_search_spec["filter"] = {"metadata.category": {"$eq": self.filter_category}}

                pipeline = [
                    {"$vectorSearch": vector_search_spec},
                    {"$project": {"content": 1, "metadata": 1, "score": {"$meta": "vectorSearchScore"}}},
                    {"$unset": "embedding"}
                ]
                try:
                    vector_results = list(self.collection.aggregate(pipeline))
                except Exception as exc:
                    app_logger.log_message("log", f"Vector search failed: {exc}", "WARNING")

            # 2. Text Search ($search)
            if self.keyword_candidates > 0:
                pipeline = [
                    {"$search": {"index": self.text_index, "text": {"query": query, "path": list(self.allowed_text_paths)}}},
                    {"$limit": self.keyword_candidates},
                    {"$project": {"content": 1, "metadata": 1, "score": {"$meta": "searchScore"}}}
                ]
                try:
                    text_results = list(self.collection.aggregate(pipeline))
                except Exception:
                    # Fallback to standard text index if Atlas Search fails
                    try:
                        text_filter = {"$text": {"$search": query}}
                        if self.filter_category:
                            text_filter["metadata.category"] = {"$eq": self.filter_category}
                        text_results = list(self.collection.find(text_filter, {"content": 1, "metadata": 1, "score": {"$meta": "textScore"}}).limit(self.keyword_candidates))
                    except Exception:
                        pass

            # 3. Fallback or Fuse
            if not vector_results and not text_results:
                if self.parent:
                    return self.parent._py_fallback_retrieve(query, self.top_k, self.semantic_candidates, self.keyword_candidates, self.rrf_k, self.filter_category)
                return []

            fused = reciprocal_rank_fusion([vector_results, text_results], self.rrf_k, self.top_k)
            return [Document(page_content=doc.get("content", ""), metadata={**doc.get("metadata", {}), "score": doc.get("score")}) for doc in fused]

    # --- Chain builder ---
    def _build_chain(self, retriever: _MongoHybridRetriever, model_override=None, url_override=None, api_key_override=None) -> RunnableLambda:

        llm_settings = settings_service.get_active_llm()
        model_cfg = llm_settings["model"]
        endpoint_cfg = llm_settings["endpoint"]
        
        llm = ChatOpenAI(
            model=model_override or model_cfg["model_name"],
            base_url=url_override or endpoint_cfg["url"],
            api_key=api_key_override or endpoint_cfg.get("api_key", ""),
            temperature=0
        )

        prompt = PromptTemplate(
            template="{system_prompt}\n\nContext:\n{context}\n\nQuestion:\n{question}\n\nUsing only the context above, provide the answer.",
            input_variables=["system_prompt", "question", "context"],
        )

        return (
            {
                "system_prompt": lambda x: x["system_prompt"],
                "question": lambda x: x["question"],
                "context": RunnableLambda(lambda x: format_docs(retriever.invoke(x["question"]))),
            }
            | prompt
            | llm
            | StrOutputParser()
        )

    # --- Query Method ---
    def query_rag(self, user_prompt: str, system_prompt: Optional[str] = None, top_k: int = 5, **kwargs) -> Dict[str, Any]:
        start = time.time()
        try:
            coll = self._ensure_collection()
            retriever = self._MongoHybridRetriever(
                collection=coll,
                embedding_fn=lambda texts: self.generate_embeddings(texts, show_progress=False),
                embedding_dim=self.embedding_dim,
                vector_index=self.vector_index,
                text_index=self.text_index,
                top_k=top_k,
                semantic_candidates=kwargs.get("semantic_candidates", 50),
                keyword_candidates=kwargs.get("keyword_candidates", 30),
                rrf_k=kwargs.get("rrf_k", 60),
                allowed_text_paths=kwargs.get("allowed_text_paths", DEFAULT_TEXT_PATHS),
                filter_category=kwargs.get("filter_category"),
            )
            retriever.parent = self

            chain = self._build_chain(retriever, kwargs.get("model_override"), kwargs.get("url_override"), kwargs.get("api_key_override"))
            answer = chain.invoke({"system_prompt": system_prompt or "", "question": user_prompt})

            return {"success": True, "content": answer, "latency": round(time.time() - start, 3)}

        except Exception as e:
            return {"success": False, "error": str(e), "latency": round(time.time() - start, 3)}

    # --- Index Creation Helpers ---

    def ensure_vector_index(collection: Collection, index_name: str, embedding_dim: int) -> None:
        # UPDATED: Matches the working configuration from mongosh
        definition = {
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": embedding_dim,
                    "similarity": "cosine"
                },
                {
                    "type": "filter",
                    "path": "metadata.category"
                }
            ]
        }
        
        try:
            # Check if index exists via listSearchIndexes (Atlas only)
            # We assume if it exists, it's correct.
            existing = list(collection.list_search_indexes(index_name))
            if existing:
                app_logger.log_message("log", f"Vector index '{index_name}' already exists.", "INFO")
                return
        except Exception:
            pass

        app_logger.log_message("log", f"Creating vector search index '{index_name}'...", "INFO")
        try:
            collection.create_search_index(
                model={"definition": definition, "name": index_name, "type": "vectorSearch"}
            )
            app_logger.log_message("log", "Index creation initiated. Check status in Atlas/Mongot.", "INFO")
        except OperationFailure as e:
            if "already exists" in str(e):
                app_logger.log_message("log", f"Index '{index_name}' exists.", "INFO")
            else:
                app_logger.log_message("log", f"Failed to create vector index: {e}", "ERROR")

    def ensure_text_index(collection: Collection, index_name: str) -> None:
        definition = {
            "mappings": {
                "dynamic": True
            }
        }
        try:
            existing = list(collection.list_search_indexes(index_name))
            if existing:
                app_logger.log_message("log", f"search index '{index_name}' already exists.", "INFO")
                return
        except Exception:
            pass

        app_logger.log_message("log", f"Creating search index '{index_name}'...", "INFO")
        try:
            collection.create_search_index(
                model={"definition": definition, "name": index_name, "type": "search"}
            )
            app_logger.log_message("log", f"search creation initiated. Check status in Atlas/Mongot.", "INFO")
        except OperationFailure as e:
            if "already exists" in str(e):
                app_logger.log_message("log", f"Index '{index_name}' exists.", "INFO")
            else:
                app_logger.log_message("log", f"Failed to create search index: {e}", "ERROR")

rag_service = RAG()

# --- CLI ---
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["init", "ingest", "query"])
    parser.add_argument("--query-text", default="Test query")
    parser.add_argument("--input-path", type=Path)
    args = parser.parse_args()

    rag = RAG() # Uses new defaults

    if args.mode == "init":
        rag.init()
    elif args.mode == "ingest" and args.input_path:
        rag.ingest(args.input_path)
    elif args.mode == "query":
        print(rag.query_rag(args.query_text))

if __name__ == "__main__":
    main()