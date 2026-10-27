"""Локальный сервер: python app.py, затем http://127.0.0.1:8000."""

import os

from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge, UnsupportedMediaType

from api_adapter import move_response, score_response

app = Flask(__name__, static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.post("/api/move")
def move():
    result, status = move_response(request.get_json())
    return jsonify(result), status


@app.post("/api/score")
def score():
    return jsonify(score_response(request.get_json()))


@app.errorhandler(ValueError)
@app.errorhandler(BadRequest)
@app.errorhandler(UnsupportedMediaType)
def invalid_request(error):
    message = str(error) if isinstance(error, ValueError) else "Передайте корректный JSON с Content-Type: application/json"
    return jsonify(error=message), 400


@app.errorhandler(RequestEntityTooLarge)
def too_large(_error):
    return jsonify(error="Размер запроса превышает 1 МБ"), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8000")), debug=False)
