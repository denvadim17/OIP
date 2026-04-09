# ДЗ 3: Инвертированный индекс и булев поиск

## Что реализовано

- построение инвертированного индекса терминов по документам;
- булев поиск с операторами `AND`, `OR`, `NOT`;
- поддержка сложных запросов со скобками;
- запрос передается строкой через параметр `--query`.

## Запуск

```bash
cd dz3
python inverted_index_search.py --docs-dir ../dz1/output/pages --index-out output/inverted_index.txt
```

Пример сложного запроса:

```bash
python inverted_index_search.py \
  --docs-dir ../dz1/output/pages \
  --index-out output/inverted_index.txt \
  --query "(клеопатра AND цезарь) OR (антоний AND цицерон) OR помпей"
```

## Результат для сдачи

- `output/inverted_index.txt` — файл с инвертированным индексом;
- ссылка на код в репозитории (`dz3/inverted_index_search.py`).
