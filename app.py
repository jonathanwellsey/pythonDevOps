import signal
import sys
import uuid

from flask import Flask, jsonify, request, send_from_directory

import persistence as db

STATIC_DIR = "static"

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")


@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/items", methods=["GET"])
def list_items():
    return jsonify(db.get_items())


@app.route("/items", methods=["POST"])
def add_item():
    body = request.get_json()
    item = {"id": str(uuid.uuid4()), "name": body["name"], "completed": False}
    db.store_item(item)
    return jsonify(item)


@app.route("/items/<item_id>", methods=["PUT"])
def update_item(item_id: str):
    body = request.get_json()
    db.update_item(item_id, {"name": body["name"], "completed": body["completed"]})
    item = db.get_item(item_id)
    return jsonify(item)


@app.route("/items/<item_id>", methods=["DELETE"])
def delete_item(item_id: str):
    db.remove_item(item_id)
    return "", 200


def _shutdown(*_):
    try:
        db.teardown()
    except Exception:
        pass
    sys.exit(0)


signal.signal(signal.SIGINT, _shutdown)
signal.signal(signal.SIGTERM, _shutdown)

if __name__ == "__main__":
    db.init()
    app.run(host="0.0.0.0", port=3000)
