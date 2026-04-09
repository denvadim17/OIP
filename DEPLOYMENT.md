# Deployment Manual

## 1. Требования

- macOS/Linux/Windows
- Python 3.9+
- Git

## 2. Клонирование

```bash
git clone https://github.com/denvadim17/OIP.git
cd OIP
```

## 3. Запуск по заданиям

### ДЗ1 - краулер

```bash
cd dz1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 crawler.py --max-pages 100 --seeds seeds.txt --output output
```

### ДЗ2 - токены и леммы

```bash
cd ../dz2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 process_texts.py --input-dir ../dz1/output/pages --output-dir output
```

### ДЗ3 - инвертированный индекс и булев поиск

```bash
cd ../dz3
python3 inverted_index_search.py --docs-dir ../dz1/output/pages --index-out output/inverted_index.txt
python3 inverted_index_search.py --docs-dir ../dz1/output/pages --index-out output/inverted_index.txt --query "(клеопатра AND цезарь) OR помпей"
```

### ДЗ4 - TF-IDF

```bash
cd ../dz4
python3 compute_tfidf.py --docs-dir ../dz1/output/pages --tokens ../dz2/output/tokens.txt --lemmas ../dz2/output/lemmas.txt --out-terms output/terms_tfidf --out-lemmas output/lemmas_tfidf
```

### ДЗ5 - векторный поиск (CLI)

```bash
cd ../dz5
python3 vector_search.py --terms-tfidf-dir ../dz4/output/terms_tfidf --query "история рим цезарь" --top-k 10
```

### ДЗ5 - WEB интерфейс

```bash
cd ../dz5
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 web_app.py --terms-tfidf-dir ../dz4/output/terms_tfidf --host 127.0.0.1 --port 5000
```

Открыть: `http://127.0.0.1:5000`
