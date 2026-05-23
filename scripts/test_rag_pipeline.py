"""Quick end-to-end RAG pipeline validation script.

Runs 3 multilingual queries (EN/FR/AR) and prints:
- retrieved documents
- reranked/merged scores
- final answer
- current model execution mode (API vs local)
"""

from __future__ import annotations

from src.core.model_loader import get_model_loader
from src.rag_system.rag import MedicalRAG


def _mode_text(loader_status: dict) -> str:
    emb_mode = "api" if loader_status.get("use_embedding_api") else "local"
    rerank_mode = "api" if loader_status.get("use_rerank_api") else "local"

    if not loader_status.get("llm_enabled", True):
        llm_mode = "disabled (template fallback)"
    else:
        llm_mode = "api" if loader_status.get("use_llm_api") else "local"

    return f"embedding={emb_mode}, reranker={rerank_mode}, llm={llm_mode}"


def run() -> None:
    loader = get_model_loader()
    rag = MedicalRAG(languages=["ar", "fr", "en"])

    print("=" * 88)
    print("RAG PIPELINE TEST")
    print("Model mode:", _mode_text(loader.get_status()))
    print("=" * 88)

    queries = [
        "What are the main symptoms of pneumonia?",
        "Quels sont les traitements du COVID-19 ?",
        "ما هي اعراض مرض السل؟",
    ]

    for idx, query in enumerate(queries, 1):
        print("\n" + "-" * 88)
        print(f"Query {idx}: {query}")
        result = rag.query(question=query, top_k=5, use_reranking=True)

        print(f"Language: {result.language}")
        print(f"Confidence: {result.confidence:.3f}")

        print("\nRetrieved / reranked sources:")
        if not result.sources:
            print("  - No sources returned")
        else:
            for i, src in enumerate(result.sources[:5], 1):
                title = src.get("title", "Unknown")
                score = float(src.get("score", src.get("relevance_score", 0.0)))
                vec = float(src.get("vector_score", 0.0))
                bm25 = float(src.get("bm25_score", 0.0))
                print(f"  {i}. {title} | final={score:.3f} | faiss={vec:.3f} | bm25={bm25:.3f}")

        print("\nFinal answer:")
        print(result.answer)

    print("\n" + "=" * 88)
    print("Done.")


if __name__ == "__main__":
    run()
