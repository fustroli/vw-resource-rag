import json

from flask import Flask, Response, render_template, request

from ask import get_sources, retrieve, stream_answer_tokens

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    question = (request.json or {}).get("question", "").strip()
    if not question:
        return Response(status=400)

    docs, metas = retrieve(question)

    def generate():
        yield json.dumps({"type": "sources", "items": get_sources(metas)}) + "\n"
        for token in stream_answer_tokens(question, docs, metas):
            yield json.dumps({"type": "token", "content": token}) + "\n"
        yield json.dumps({"type": "done"}) + "\n"

    return Response(generate(), mimetype="application/x-ndjson")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
