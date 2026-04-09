import argparse
import html
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple


WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё]+")
QUERY_TOKEN_RE = re.compile(r"\(|\)|AND|OR|NOT|[A-Za-zА-Яа-яЁё]+", flags=re.IGNORECASE)


def normalize_word(word: str) -> str:
    return word.lower().replace("ё", "е")


def html_to_text(raw_html: str) -> str:
    no_scripts = re.sub(r"<script[\s\S]*?</script>", " ", raw_html, flags=re.IGNORECASE)
    no_styles = re.sub(r"<style[\s\S]*?</style>", " ", no_scripts, flags=re.IGNORECASE)
    no_tags = re.sub(r"<[^>]+>", " ", no_styles)
    decoded = html.unescape(no_tags)
    return decoded


def extract_terms(text: str) -> Set[str]:
    terms = {normalize_word(w) for w in WORD_RE.findall(text)}
    return {t for t in terms if len(t) > 1}


def build_inverted_index(docs_dir: Path) -> Tuple[Dict[str, Set[str]], Set[str]]:
    index: Dict[str, Set[str]] = {}
    all_docs: Set[str] = set()

    for file_path in sorted(docs_dir.glob("*.txt")):
        doc_id = file_path.stem
        all_docs.add(doc_id)
        raw_html = file_path.read_text(encoding="utf-8", errors="ignore")
        terms = extract_terms(html_to_text(raw_html))
        for term in terms:
            index.setdefault(term, set()).add(doc_id)

    return index, all_docs


def save_index(index: Dict[str, Set[str]], output_path: Path) -> None:
    lines: List[str] = []
    for term in sorted(index.keys()):
        postings = " ".join(sorted(index[term]))
        lines.append(f"{term} {postings}")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def tokenize_query(query: str) -> List[str]:
    tokens = QUERY_TOKEN_RE.findall(query)
    return [t.upper() if t.upper() in {"AND", "OR", "NOT"} else normalize_word(t) for t in tokens]


class QueryParser:
    def __init__(self, tokens: List[str], index: Dict[str, Set[str]], all_docs: Set[str]):
        self.tokens = tokens
        self.i = 0
        self.index = index
        self.all_docs = all_docs

    def current(self) -> str:
        return self.tokens[self.i] if self.i < len(self.tokens) else ""

    def eat(self, expected: str = "") -> str:
        tok = self.current()
        if not tok:
            raise ValueError("Неожиданный конец запроса")
        if expected and tok != expected:
            raise ValueError(f"Ожидался токен '{expected}', получен '{tok}'")
        self.i += 1
        return tok

    def parse(self) -> Set[str]:
        result = self.parse_or()
        if self.current():
            raise ValueError(f"Лишний токен в запросе: '{self.current()}'")
        return result

    def parse_or(self) -> Set[str]:
        left = self.parse_and()
        while self.current() == "OR":
            self.eat("OR")
            right = self.parse_and()
            left = left | right
        return left

    def parse_and(self) -> Set[str]:
        left = self.parse_not()
        while self.current() == "AND":
            self.eat("AND")
            right = self.parse_not()
            left = left & right
        return left

    def parse_not(self) -> Set[str]:
        if self.current() == "NOT":
            self.eat("NOT")
            return self.all_docs - self.parse_not()
        return self.parse_atom()

    def parse_atom(self) -> Set[str]:
        tok = self.current()
        if tok == "(":
            self.eat("(")
            value = self.parse_or()
            self.eat(")")
            return value
        if tok in {"AND", "OR", "NOT", ")"}:
            raise ValueError(f"Ожидался термин, получен '{tok}'")
        term = self.eat()
        return set(self.index.get(term, set()))


def run_search(query: str, index: Dict[str, Set[str]], all_docs: Set[str]) -> List[str]:
    tokens = tokenize_query(query)
    if not tokens:
        return []
    parser = QueryParser(tokens, index, all_docs)
    result = parser.parse()
    return sorted(result)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build inverted index and run boolean search (AND/OR/NOT)"
    )
    parser.add_argument("--docs-dir", default="../dz1/output/pages", help="Path to documents")
    parser.add_argument(
        "--index-out",
        default="output/inverted_index.txt",
        help="Path to save inverted index",
    )
    parser.add_argument(
        "--query",
        default="",
        help="Boolean query, e.g. (клеопатра AND цезарь) OR помпей",
    )
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    index_out = Path(args.index_out)
    index_out.parent.mkdir(parents=True, exist_ok=True)

    index, all_docs = build_inverted_index(docs_dir)
    save_index(index, index_out)

    print(f"Documents indexed: {len(all_docs)}")
    print(f"Terms in index: {len(index)}")
    print(f"Inverted index file: {index_out.resolve()}")

    if args.query:
        result_docs = run_search(args.query, index, all_docs)
        print(f"Query: {args.query}")
        print(f"Matched documents: {len(result_docs)}")
        print(" ".join(result_docs))


if __name__ == "__main__":
    main()
