# Backend (Flask) - Personal To-Do API

A simple Flask backend serving a to-do list API with OpenAPI/Swagger documentation.

## Endpoints

Base URL: http://localhost:3001

- GET /api/tasks
- POST /api/tasks
- PATCH /api/tasks/{task_id}
- DELETE /api/tasks/{task_id}

OpenAPI docs:
- Swagger UI: http://localhost:3001/docs
- OpenAPI JSON: http://localhost:3001/openapi.json

## Running Locally

1) Create and activate a virtual environment (optional but recommended)

2) Install dependencies
- pip install -r requirements.txt (if available) or the packages used by the app (Flask, CORS library if applicable)

3) Run the app
- By default the service should listen on port 3001
- Example:
  export PORT=3001
  python app.py
  or
  flask run --host=0.0.0.0 --port=3001

Check http://localhost:3001/docs to verify the service is running.

## CORS

If you restrict CORS, ensure the frontend origin is allowed:
- Frontend dev origin: http://localhost:3000

Example (using flask-cors):
from flask_cors import CORS
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

## Notes

- The OpenAPI document is available at /openapi.json (see interfaces/openapi.json for reference).
- Adjust environment variables as needed; do not hardcode secrets in code.
