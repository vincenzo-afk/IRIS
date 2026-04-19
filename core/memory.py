"""
IRIS — Persistent Memory Module (Mem0)
========================================
Wraps Mem0 to store/retrieve/search memories per user session.
Supports both cloud Mem0 API and local Qdrant backend.
"""

import logging
from typing import List, Optional

from config import (
    MEM0_API_KEY,
    USER_ID,
    MEMORY_TOP_K,
    MEMORY_LOCAL,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# MEM0 CLIENT INIT
# ──────────────────────────────────────────────────────────────

def _build_client():
    """Initialize and return the Mem0 client (cloud or local)."""
    try:
        from mem0 import Memory, MemoryClient

        if MEM0_API_KEY and not MEMORY_LOCAL:
            # Cloud-hosted Mem0
            client = MemoryClient(api_key=MEM0_API_KEY)
            logger.info("Mem0 client: CLOUD mode")
            return client
        else:
            # Local mode using built-in vector store
            config = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "collection_name": "iris_memory",
                        "host": "localhost",
                        "port": 6333,
                        "embedding_model_dims": 1536,
                    },
                },
                "llm": {
                    "provider": "google",
                    "config": {
                        "model": "gemini-2.0-flash",
                        "api_key": _get_gemini_key(),
                    },
                },
                "embedder": {
                    "provider": "google",
                    "config": {
                        "model": "models/text-embedding-004",
                        "api_key": _get_gemini_key(),
                    },
                },
            }
            client = Memory.from_config(config)
            logger.info("Mem0 client: LOCAL mode (Qdrant)")
            return client

    except ImportError:
        logger.warning("mem0ai not installed — memory will be in-process only")
        return None
    except Exception as exc:
        logger.error("Mem0 init failed: %s", exc)
        return None


def _get_gemini_key():
    from config import GEMINI_API_KEY
    return GEMINI_API_KEY


_client = None

def get_client():
    global _client
    if _client is None:
        _client = _build_client()
    return _client


# ──────────────────────────────────────────────────────────────
# MEMORY OPERATIONS
# ──────────────────────────────────────────────────────────────

def add_memory(text: str, metadata: Optional[dict] = None) -> bool:
    """
    Store a new memory for the current user.

    Args:
        text: The memory content (fact, observation, preference, task).
        metadata: Optional dict with extra tags (e.g. {"type": "preference"}).

    Returns:
        True if stored successfully.
    """
    client = get_client()
    if client is None:
        logger.warning("Memory client unavailable — skipping add_memory")
        return False

    try:
        messages = [{"role": "user", "content": text}]
        kwargs = {"user_id": USER_ID}
        if metadata:
            kwargs["metadata"] = metadata
        client.add(messages, **kwargs)
        logger.info("Memory stored: %s…", text[:60])
        return True
    except Exception as exc:
        logger.error("add_memory failed: %s", exc)
        return False


def search_memory(query: str, top_k: int = MEMORY_TOP_K) -> List[str]:
    """
    Search memories relevant to a query.

    Returns:
        List of memory strings, most relevant first.
    """
    client = get_client()
    if client is None:
        return []

    try:
        results = client.search(query, user_id=USER_ID, limit=top_k)
        if isinstance(results, dict):
            # Cloud API returns {"results": [...]}
            hits = results.get("results", [])
        else:
            hits = results

        memories = [
            r.get("memory", r.get("text", "")) for r in hits if r
        ]
        logger.debug("Memory search '%s' → %d results", query[:40], len(memories))
        return [m for m in memories if m]
    except Exception as exc:
        logger.error("search_memory failed: %s", exc)
        return []


def get_all_memories() -> List[str]:
    """Retrieve all stored memories for the user."""
    client = get_client()
    if client is None:
        return []

    try:
        results = client.get_all(user_id=USER_ID)
        if isinstance(results, dict):
            hits = results.get("results", [])
        else:
            hits = results
        return [r.get("memory", r.get("text", "")) for r in hits if r]
    except Exception as exc:
        logger.error("get_all_memories failed: %s", exc)
        return []


def build_memory_context(query: str) -> str:
    """
    Build a formatted context string of relevant memories
    to inject into a Gemini prompt.
    """
    memories = search_memory(query)
    if not memories:
        return ""

    lines = "\n".join(f"- {m}" for m in memories)
    return f"[Relevant memories about the user]\n{lines}"


def save_session_summary(summary: str):
    """Call at end of session to persist what happened."""
    add_memory(
        f"Session summary: {summary}",
        metadata={"type": "session_summary"},
    )
    logger.info("Session summary saved to memory")
