from flask import Flask, request, jsonify
from flask_cors import CORS

from main_py import handle_query

may_legal_assistant = Flask(__name__)
CORS(may_legal_assistant)


@may_legal_assistant.route("/api/query", methods=["POST"])
def query_api():
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400

    cleaned, response = handle_query(data["message"])

    return jsonify({
        "cleaned_input": cleaned,
        "response": response
    })


@may_legal_assistant.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    may_legal_assistant.run(debug=True)
