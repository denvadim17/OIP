# OIP: Поисковые технологии (ДЗ 1-5)

Репозиторий содержит полный цикл учебных заданий по обработке текстов и поиску:

- сбор документов;
- токенизация и лемматизация;
- построение инвертированного индекса и булев поиск;
- вычисление TF-IDF;
- векторный поиск с WEB интерфейсом.

## Структура репозитория

- `dz1` - краулер, выкачка HTML страниц, `index.txt`.
- `dz2` - токены и леммы (`tokens.txt`, `lemmas.txt`).
- `dz3` - инвертированный индекс и булев поиск (`AND/OR/NOT`).
- `dz4` - TF-IDF для терминов и лемматизированных форм по каждому документу.
- `dz5` - векторный поиск (cosine similarity) и WEB интерфейс (top-10 результатов).

## Быстрый запуск демо (ДЗ5)

```bash
cd dz5
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 web_app.py --terms-tfidf-dir ../dz4/output/terms_tfidf --host 127.0.0.1 --port 5000
```

Открыть в браузере: `http://127.0.0.1:5000`

## Проверка без запуска

Преподаватель может посмотреть готовые результаты напрямую:

- `dz1/output/index.txt`
- `dz2/output/tokens.txt`
- `dz2/output/lemmas.txt`
- `dz3/output/inverted_index.txt`
- `dz4/output/terms_tfidf/*.txt`
- `dz4/output/lemmas_tfidf/*.txt`
