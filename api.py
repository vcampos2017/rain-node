from flask import Flask, jsonify

from rain_common import latest

app = Flask(__name__)


def get_latest():
    return latest()


@app.route("/status")
def status():
    try:
        return jsonify(get_latest())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
