import argparse
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9_-]+")
CYRILLIC_TOKEN_RE = re.compile(r"^[а-яё-]+$")


def normalize_token(token: str) -> str:
    return token.lower().replace("ё", "е").replace("—", "-").strip("-")


def tokenize_query(text: str) -> List[str]:
    tokens: List[str] = []
    for raw in TOKEN_RE.findall(text):
        token = normalize_token(raw)
        if len(token) < 2:
            continue
        if not CYRILLIC_TOKEN_RE.match(token):
            continue
        tokens.append(token)
    return tokens


def load_document_vectors(terms_tfidf_dir: Path) -> Tuple[Dict[str, Dict[str, float]], Dict[str, float]]:
    doc_vectors: Dict[str, Dict[str, float]] = {}
    idf_map: Dict[str, float] = {}

    for file_path in sorted(terms_tfidf_dir.glob("*.txt")):
        doc_id = file_path.stem
        vector: Dict[str, float] = {}
        for line in file_path.read_text(encoding="utf-8").splitlines():
            parts = line.strip().split()
            if len(parts) != 3:
                continue
            term, idf_str, tfidf_str = parts
            idf = float(idf_str)
            tfidf = float(tfidf_str)
            vector[term] = tfidf
            if term not in idf_map:
                idf_map[term] = idf
        doc_vectors[doc_id] = vector

    return doc_vectors, idf_map


def compute_norm(vector: Dict[str, float]) -> float:
    return math.sqrt(sum(v * v for v in vector.values()))


def build_inverted_doc_weights(doc_vectors: Dict[str, Dict[str, float]]) -> Dict[str, List[Tuple[str, float]]]:
    inverted: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
    for doc_id, vector in doc_vectors.items():
        for term, weight in vector.items():
            inverted[term].append((doc_id, weight))
    return inverted


def build_query_vector(query: str, idf_map: Dict[str, float]) -> Dict[str, float]:
    tokens = tokenize_query(query)
    if not tokens:
        return {}
    counts = Counter(tokens)
    total = sum(counts.values())
    vector: Dict[str, float] = {}
    for term, cnt in counts.items():
        if term not in idf_map:
            continue
        tf = cnt / total
        vector[term] = tf * idf_map[term]
    return vector


def search(
    query: str,
    doc_vectors: Dict[str, Dict[str, float]],
    doc_norms: Dict[str, float],
    inverted: Dict[str, List[Tuple[str, float]]],
    idf_map: Dict[str, float],
    top_k: int = 10,
) -> List[Tuple[str, float]]:
    q_vec = build_query_vector(query, idf_map)
    q_norm = compute_norm(q_vec)
    if not q_vec or q_norm == 0.0:
        return []

    dot_scores: Dict[str, float] = defaultdict(float)
    for term, q_w in q_vec.items():
        for doc_id, d_w in inverted.get(term, []):
            dot_scores[doc_id] += q_w * d_w

    results: List[Tuple[str, float]] = []
    for doc_id, dot in dot_scores.items():
        d_norm = doc_norms.get(doc_id, 0.0)
        if d_norm == 0.0:
            continue
        sim = dot / (q_norm * d_norm)
        if sim > 0:
            results.append((doc_id, sim))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


def main() -> None:
    parser = argparse.ArgumentParser(description="Vector search with TF-IDF and cosine similarity")
    parser.add_argument(
        "--terms-tfidf-dir",
        default="../dz4/output/terms_tfidf",
        help="Directory with per-document term tf-idf files",
    )
    parser.add_argument("--query", required=True, help="Search query string")
    parser.add_argument("--top-k", type=int, default=10, help="How many results to return")
    args = parser.parse_args()

    terms_dir = Path(args.terms_tfidf_dir)
    doc_vectors, idf_map = load_document_vectors(terms_dir)
    doc_norms = {doc_id: compute_norm(vec) for doc_id, vec in doc_vectors.items()}
    inverted = build_inverted_doc_weights(doc_vectors)

    results = search(args.query, doc_vectors, doc_norms, inverted, idf_map, top_k=args.top_k)

    print(f"Documents in index: {len(doc_vectors)}")
    print(f"Query: {args.query}")
    print(f"Top {args.top_k} results:")
    for rank, (doc_id, score) in enumerate(results, start=1):
        print(f"{rank}. {doc_id} {score:.6f}")


if __name__ == "__main__":
    main()
