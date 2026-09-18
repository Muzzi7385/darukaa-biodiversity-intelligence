from pathlib import Path

import chromadb

from backend.rag.embeddings import generate_embeddings


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

CHROMA_DIR = PROJECT_ROOT / "data" / "chroma"


# ---------------------------------------------------------
# Chroma
# ---------------------------------------------------------

chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = chroma_client.get_or_create_collection(
    name="environmental_knowledge"
)


# ---------------------------------------------------------
# Single query retrieval
# ---------------------------------------------------------

def retrieve_single_query(
    query: str,
    top_k: int = 5,
) -> list[dict]:

    query = query.strip()

    if not query:
        return []

    query_embedding = generate_embeddings(
        [query]
    )[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    documents = results.get(
        "documents",
        [[]]
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    distances = results.get(
        "distances",
        [[]]
    )[0]

    retrieved: list[dict] = []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances,
    ):

        retrieved.append(
            {
                "text": document,
                "source": metadata.get("source"),
                "page": metadata.get("page"),
                "chunk_index": metadata.get("chunk_index"),
                "distance": distance,
                "query": query,
            }
        )

    return retrieved


# ---------------------------------------------------------
# Multi-dimensional retrieval
# ---------------------------------------------------------

def retrieve_multi_metric_knowledge(
    queries: list[str],
    top_k_per_query: int = 3,
) -> list[dict]:
    """
    Retrieve evidence separately for multiple
    environmental dimensions.

    Results are deduplicated by source + page + chunk.
    """

    all_results: list[dict] = []

    for query in queries:

        results = retrieve_single_query(
            query=query,
            top_k=top_k_per_query,
        )

        all_results.extend(results)

    # -----------------------------------------------------
    # Deduplicate
    # -----------------------------------------------------

    unique_results: dict[str, dict] = {}

    for result in all_results:

        unique_id = (
            f"{result['source']}_"
            f"{result['page']}_"
            f"{result['chunk_index']}"
        )

        existing = unique_results.get(
            unique_id
        )

        if (
            existing is None
            or result["distance"]
            < existing["distance"]
        ):
            unique_results[unique_id] = result

    # -----------------------------------------------------
    # Sort by semantic relevance
    # Lower cosine distance = more similar
    # -----------------------------------------------------

    ranked_results = sorted(
        unique_results.values(),
        key=lambda item: item["distance"]
    )

    return ranked_results


# ---------------------------------------------------------
# CLI test
# ---------------------------------------------------------

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("MULTI-METRIC RAG TEST")
    print("=" * 70)

    queries = [
        "soil organic carbon and soil health in agricultural land",
        "low rainfall water availability and agricultural ecosystems",
        "wheat monoculture biodiversity habitat diversity and species richness",
        "agroforestry intercropping and biodiversity",
        "semi-arid agriculture biodiversity conservation",
    ]

    results = retrieve_multi_metric_knowledge(
        queries,
        top_k_per_query=3,
    )

    print()

    for index, result in enumerate(
        results,
        start=1,
    ):

        print(f"RESULT {index}")
        print(
            f"Query: {result['query']}"
        )
        print(
            f"Source: {result['source']}"
        )
        print(
            f"Page: {result['page']}"
        )
        print(
            f"Distance: {result['distance']:.4f}"
        )
        print()
        print(result["text"])
        print("-" * 70)