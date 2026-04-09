import argparse
import html
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9_-]+")
CYRILLIC_TOKEN_RE = re.compile(r"^[а-яё-]+$")


def html_to_text(raw_html: str) -> str:
    no_scripts = re.sub(r"<script[\s\S]*?</script>", " ", raw_html, flags=re.IGNORECASE)
    no_styles = re.sub(r"<style[\s\S]*?</style>", " ", no_scripts, flags=re.IGNORECASE)
    no_tags = re.sub(r"<[^>]+>", " ", no_styles)
    return html.unescape(no_tags)


def normalize_token(token: str) -> str:
    return token.lower().replace("—", "-").strip("-")


def is_clean_token(token: str) -> bool:
    if not token:
        return False
    if len(token) < 2:
        return False
    if not CYRILLIC_TOKEN_RE.match(token):
        return False
    if token.isdigit():
        return False
    return True


def tokenize_text(text: str) -> List[str]:
    result: List[str] = []
    for raw in TOKEN_RE.findall(text):
        token = normalize_token(raw)
        if is_clean_token(token):
            result.append(token)
    return result


def load_tokens(tokens_path: Path) -> Set[str]:
    return {line.strip() for line in tokens_path.read_text(encoding="utf-8").splitlines() if line.strip()}


def load_lemma_map(lemmas_path: Path) -> Dict[str, Set[str]]:
    lemma_map: Dict[str, Set[str]] = {}
    for line in lemmas_path.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        lemma = parts[0]
        forms = set(parts[1:])
        if not forms:
            forms = {lemma}
        lemma_map[lemma] = forms
    return lemma_map


def compute_doc_token_counts(
    docs_dir: Path, allowed_tokens: Set[str]
) -> Tuple[Dict[str, Counter], Dict[str, int], Dict[str, Set[str]]]:
    doc_to_counts: Dict[str, Counter] = {}
    doc_to_total_terms: Dict[str, int] = {}
    token_to_docs: Dict[str, Set[str]] = defaultdict(set)

    for doc_path in sorted(docs_dir.glob("*.txt")):
        doc_id = doc_path.stem
        raw_html = doc_path.read_text(encoding="utf-8", errors="ignore")
        cleaned_tokens = tokenize_text(html_to_text(raw_html))
        counts = Counter(t for t in cleaned_tokens if t in allowed_tokens)
        doc_to_counts[doc_id] = counts
        doc_to_total_terms[doc_id] = sum(counts.values())
        for token in counts:
            token_to_docs[token].add(doc_id)

    return doc_to_counts, doc_to_total_terms, token_to_docs


def build_lemma_document_frequency(
    doc_to_counts: Dict[str, Counter], lemma_map: Dict[str, Set[str]]
) -> Dict[str, int]:
    lemma_df: Dict[str, int] = {}
    for lemma, forms in lemma_map.items():
        df = 0
        for counts in doc_to_counts.values():
            if any(form in counts for form in forms):
                df += 1
        lemma_df[lemma] = df
    return lemma_df


def write_term_tfidf(
    output_dir: Path,
    doc_to_counts: Dict[str, Counter],
    doc_to_total_terms: Dict[str, int],
    token_to_docs: Dict[str, Set[str]],
    total_docs: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for doc_id, counts in doc_to_counts.items():
        total_terms = doc_to_total_terms[doc_id]
        lines: List[str] = []
        if total_terms > 0:
            for token in sorted(counts.keys()):
                tf = counts[token] / total_terms
                df = len(token_to_docs[token])
                idf = math.log(total_docs / df) if df > 0 else 0.0
                tfidf = tf * idf
                lines.append(f"{token} {idf:.10f} {tfidf:.10f}")
        (output_dir / f"{doc_id}.txt").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_lemma_tfidf(
    output_dir: Path,
    doc_to_counts: Dict[str, Counter],
    doc_to_total_terms: Dict[str, int],
    lemma_map: Dict[str, Set[str]],
    lemma_df: Dict[str, int],
    total_docs: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for doc_id, counts in doc_to_counts.items():
        total_terms = doc_to_total_terms[doc_id]
        lines: List[str] = []
        if total_terms > 0:
            for lemma in sorted(lemma_map.keys()):
                lemma_count = sum(counts.get(form, 0) for form in lemma_map[lemma])
                if lemma_count == 0:
                    continue
                tf = lemma_count / total_terms
                df = lemma_df.get(lemma, 0)
                idf = math.log(total_docs / df) if df > 0 else 0.0
                tfidf = tf * idf
                lines.append(f"{lemma} {idf:.10f} {tfidf:.10f}")
        (output_dir / f"{doc_id}.txt").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute term and lemma TF-IDF for each document")
    parser.add_argument("--docs-dir", default="../dz1/output/pages", help="Directory with downloaded documents")
    parser.add_argument("--tokens", default="../dz2/output/tokens.txt", help="Path to unique tokens list")
    parser.add_argument("--lemmas", default="../dz2/output/lemmas.txt", help="Path to lemma -> forms list")
    parser.add_argument("--out-terms", default="output/terms_tfidf", help="Output dir for term tf-idf files")
    parser.add_argument("--out-lemmas", default="output/lemmas_tfidf", help="Output dir for lemma tf-idf files")
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    tokens_path = Path(args.tokens)
    lemmas_path = Path(args.lemmas)
    out_terms = Path(args.out_terms)
    out_lemmas = Path(args.out_lemmas)

    allowed_tokens = load_tokens(tokens_path)
    lemma_map = load_lemma_map(lemmas_path)

    doc_to_counts, doc_to_total_terms, token_to_docs = compute_doc_token_counts(docs_dir, allowed_tokens)
    total_docs = len(doc_to_counts)
    lemma_df = build_lemma_document_frequency(doc_to_counts, lemma_map)

    write_term_tfidf(out_terms, doc_to_counts, doc_to_total_terms, token_to_docs, total_docs)
    write_lemma_tfidf(out_lemmas, doc_to_counts, doc_to_total_terms, lemma_map, lemma_df, total_docs)

    print(f"Documents processed: {total_docs}")
    print(f"Term files: {out_terms.resolve()}")
    print(f"Lemma files: {out_lemmas.resolve()}")


if __name__ == "__main__":
    main()
