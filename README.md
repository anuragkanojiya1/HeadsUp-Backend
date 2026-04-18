# FastAPI Backend

This is a default setup for a FastAPI backend.

## Installation

1. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Server

To run the server in development mode:
```
uvicorn app.main:app --reload
```

The server will start at `http://127.0.0.1:8000`

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoints

- `GET /`: Returns a hello world message
- `GET /items/{item_id}`: Returns item details with optional query parameter `q`