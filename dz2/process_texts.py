import argparse
import re
from collections import defaultdict
from pathlib import Path

from bs4 import BeautifulSoup
from pymorphy2 import MorphAnalyzer


CYRILLIC_WORD_RE = re.compile(r"^[а-яё-]+$")


def extract_text_from_html(path: Path) -> str:
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(" ")


def normalize_token(token: str) -> str:
    token = token.lower().replace("—", "-").strip("-")
    return token


def is_clean_token(token: str) -> bool:
    if not token:
        return False
    if not CYRILLIC_WORD_RE.match(token):
        return False
    if len(token) < 2:
        return False
    return True


def build_tokens_and_lemmas(input_dir: Path) -> tuple[set[str], dict[str, set[str]]]:
    morph = MorphAnalyzer()
    unique_tokens: set[str] = set()
    lemma_to_tokens: dict[str, set[str]] = defaultdict(set)

    for file_path in sorted(input_dir.glob("*.txt")):
        text = extract_text_from_html(file_path)
        raw_tokens = re.findall(r"[A-Za-zА-Яа-яЁё0-9_-]+", text)

        for raw in raw_tokens:
            token = normalize_token(raw)
            if not is_clean_token(token):
                continue

            parsed = morph.parse(token)[0]
            pos = parsed.tag.POS
            if pos in {"PREP", "CONJ"}:
                continue
            if token.isdigit():
                continue

            unique_tokens.add(token)
            lemma_to_tokens[parsed.normal_form].add(token)

    return unique_tokens, lemma_to_tokens


def write_outputs(tokens: set[str], lemmas: dict[str, set[str]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    tokens_path = output_dir / "tokens.txt"
    lemmas_path = output_dir / "lemmas.txt"

    sorted_tokens = sorted(tokens)
    tokens_path.write_text("".join(f"{token}\n" for token in sorted_tokens), encoding="utf-8")

    lemma_lines = []
    for lemma in sorted(lemmas):
        forms = " ".join(sorted(lemmas[lemma]))
        lemma_lines.append(f"{lemma} {forms}")
    lemmas_path.write_text("\n".join(lemma_lines) + "\n", encoding="utf-8")

    print(f"Tokens count: {len(sorted_tokens)}")
    print(f"Lemmas count: {len(lemmas)}")
    print(f"Tokens file: {tokens_path.resolve()}")
    print(f"Lemmas file: {lemmas_path.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tokenize HTML pages, remove noise, and group tokens by lemma"
    )
    parser.add_argument(
        "--input-dir",
        default="../dz1/output/pages",
        help="Directory with downloaded HTML .txt files",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory where tokens.txt and lemmas.txt will be written",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    tokens, lemmas = build_tokens_and_lemmas(input_dir)
    write_outputs(tokens, lemmas, output_dir)


if __name__ == "__main__":
    main()
