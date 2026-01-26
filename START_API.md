# How to Start the API Server

## Quick Start

Open a terminal in the project directory and run:

```bash
cd c:\Users\riyas\IdeaProjects\ATS-Approved
uvicorn app.main:app --reload
```

## What This Does

- Starts the FastAPI server on `http://localhost:8000`
- `--reload` flag enables auto-reload (server restarts when you change code)
- The API will be available at: `http://localhost:8000`

## Verify It's Running

Once started, you should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Test the API

Open your browser and go to:
- `http://localhost:8000` - API root
- `http://localhost:8000/docs` - Interactive API documentation (Swagger UI)
- `http://localhost:8000/health` - Health check endpoint

## Available Endpoints

Once running, you can use:
- `POST /parse/docx` - Parse a resume
- `POST /jd/extract` - Extract JD signals
- `POST /evidence/map` - Map evidence
- `POST /rewrite/suggest` - Generate rewrite suggestions

## Stop the Server

Press `Ctrl+C` in the terminal to stop the server.

## Troubleshooting

### "uvicorn not found"
Install it:
```bash
python -m pip install uvicorn[standard]
```

### "Port 8000 already in use"
Use a different port:
```bash
uvicorn app.main:app --reload --port 8001
```

### "Module not found errors"
Install all dependencies:
```bash
python -m pip install -r requirements.txt
```
