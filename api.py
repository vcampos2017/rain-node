from flask import Flask, jsonify
import csv

app = Flask(__name__)

LOG_FILE = "logs/rain_log.csv"


def get_latest():
    try:
        with open(LOG_FILE, "r") as f:
            rows = list(csv.DictReader(f))
            if not rows:
                return {}

            row = rows[-1]

            return {
                "timestamp_utc": row["timestamp_utc"],
                "tip_count": int(row["tip_count"]),
                "rain_mm": float(row["rain_mm"]),
                "rain_in": float(row["rain_in"]),
                "rate_mm_hr": float(row["rate_mm_hr"]),
            }

    except Exception as e:
        return {"error": str(e)}


@app.route("/status")
def status():
    return jsonify(get_latest())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
