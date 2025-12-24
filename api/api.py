from flask import Flask, request, jsonify
from flask_cors import CORS

from main import handle_query

app = Flask(__name__)
CORS(app)


@app.route("/api/query", methods=["POST"])
def query_api():
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400

    cleaned, response = handle_query(data["message"])

    return jsonify({
        "cleaned_input": cleaned,
        "response": response
    })


if __name__ == "__main__":
    app.run(debug=True)
