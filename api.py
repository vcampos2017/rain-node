from flask import Flask, jsonify

from rain_common import rate_mm_hr, read_rows

app = Flask(__name__)


def get_latest():
    rows = read_rows()
    if not rows:
        return {}

    row = rows[-1]

    return {
        "timestamp_utc": row["timestamp_utc"],
        "tip_count": row["tip_count"],
        "rain_mm": row["rain_mm"],
        "rain_in": row["rain_in"],
        # Worked out from recent tips at request time, so it drops back
        # to 0 once the rain stops instead of repeating the last value.
        "rate_mm_hr": round(rate_mm_hr(r["time"] for r in rows), 2),
    }


@app.route("/status")
def status():
    try:
        return jsonify(get_latest())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
