from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, request, send_file

from BackendsGLOBAL.PDFFinder import handle_info_request

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__, static_folder=None)


@app.get("/")
def serve_index():
    return send_file(FRONTEND_DIR / "index.html")


@app.post("/api/query")
def query_pdf():
    payload = request.get_json(silent=True) or {}
    info_request = str(payload.get("request", "")).strip()

    try:
        result = handle_info_request(info_request)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 404
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception:
        return jsonify({"error": "Unexpected server error."}), 500

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
