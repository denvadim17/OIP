import argparse
from pathlib import Path

from flask import Flask, render_template_string, request

from vector_search import VectorSearchEngine


PAGE_TEMPLATE = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Vector Search</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 900px; margin: 30px auto; }
    input[type=text] { width: 100%; padding: 10px; font-size: 16px; }
    button { margin-top: 10px; padding: 10px 14px; font-size: 15px; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { border-bottom: 1px solid #ddd; text-align: left; padding: 8px; }
    .hint { color: #666; margin-top: 8px; }
  </style>
</head>
<body>
  <h2>Поисковая система (векторный поиск)</h2>
  <form method="get">
    <input type="text" name="q" placeholder="Введите запрос..." value="{{ query }}">
    <button type="submit">Искать</button>
  </form>
  <div class="hint">Показываются топ-10 результатов по cosine similarity.</div>

  {% if query %}
    <h3>Результаты для: "{{ query }}"</h3>
    {% if results %}
      <table>
        <thead>
          <tr><th>#</th><th>Документ</th><th>Скор</th></tr>
        </thead>
        <tbody>
          {% for item in results %}
          <tr>
            <td>{{ item.rank }}</td>
            <td>{{ item.doc_id }}</td>
            <td>{{ "%.6f"|format(item.score) }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      <p>Ничего не найдено.</p>
    {% endif %}
  {% endif %}
</body>
</html>
"""


def create_app(terms_tfidf_dir: Path) -> Flask:
    app = Flask(__name__)
    engine = VectorSearchEngine(terms_tfidf_dir)

    @app.get("/")
    def index():
        query = request.args.get("q", "").strip()
        rows = []
        if query:
            matches = engine.search(query, top_k=10)
            rows = [
                {"rank": rank, "doc_id": doc_id, "score": score}
                for rank, (doc_id, score) in enumerate(matches, start=1)
            ]
        return render_template_string(PAGE_TEMPLATE, query=query, results=rows)

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run web UI for vector search")
    parser.add_argument(
        "--terms-tfidf-dir",
        default="../dz4/output/terms_tfidf",
        help="Directory with per-document term tf-idf files",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for web server")
    parser.add_argument("--port", type=int, default=5000, help="Port for web server")
    args = parser.parse_args()

    app = create_app(Path(args.terms_tfidf_dir))
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
