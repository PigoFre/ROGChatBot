# ROGChatBot

ROGChatBot is a small web app that lets a user enter a citation or information request, selects the most relevant PDF from `PDF_Database`, and returns a citation plus requested information using OpenAI.

## Local development

1. Create and activate a Python 3.11 virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set environment variables:

```bash
set OPENAI_API_KEY=your_key_here
set OPENAI_MODEL=gpt-4o-mini
```

4. Start the app:

```bash
python app.py
```

5. Open `http://localhost:5000`.

## Deploying on Render

This repo includes:

- `render.yaml` for Render service configuration
- `requirements.txt` for Python dependencies
- `runtime.txt` to pin the Python version

On Render, create a new Blueprint or Web Service from this repo and set:

- `OPENAI_API_KEY`
- optionally `OPENAI_MODEL`

Render will install dependencies with `pip install -r requirements.txt` and start the service with `gunicorn app:app`.

## Project structure

- `app.py`: Flask app and API routes
- `frontend/index.html`: frontend UI
- `BackendsGLOBAL/PDFFinder.py`: PDF selection logic
- `BackendsGLOBAL/PDF_Analyzer.py`: PDF text extraction and OpenAI analysis
- `PDF_Database/`: source PDFs searched by the app
