from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, request, send_file
#This is the main entry point for the Flask application. It defines the API endpoint that receives user queries, processes them using the PDFFinder, and returns the results as JSON. The app also serves a static index.html file for the frontend interface.
from BackendsGLOBAL.PDFFinder import handle_info_request

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__, static_folder=None)

#if the user accesses the root URL, we serve the index.html file from the frontend directory. This allows us to have a simple web interface for users to interact with the PDF analysis functionality. The static_folder is set to None because we are manually serving the index.html file, and we don't need Flask's built-in static file handling for this simple setup.
@app.get("/")
def serve_index():
    return send_file(FRONTEND_DIR / "index.html")

#From da button on the index html, it calls this post.
@app.post("/api/query")
def query_pdf():
    #This is da user request.
    payload = request.get_json(silent=True) or {}
    #Turns the request into a string, and if there is no request, it defaults to an empty string. This ensures that the subsequent processing has a consistent input format, even if the user does not provide any query.
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
