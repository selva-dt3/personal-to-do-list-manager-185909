from flask import Flask
from flask_cors import CORS
from flask_smorest import Api
from .routes.health import blp as health_blp

# Initialize Flask app
app = Flask(__name__)
app.url_map.strict_slashes = False

# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*"}})

# API metadata and OpenAPI/Swagger UI config
app.config["API_TITLE"] = "Personal To-Do API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
# Serve Swagger UI at /docs and spec at /openapi.json
app.config["OPENAPI_URL_PREFIX"] = ""
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/docs"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

# Initialize Api
api = Api(app)

# Register blueprints
api.register_blueprint(health_blp)

# Import and register tasks blueprint
from .routes.tasks import blp as tasks_blp  # noqa: E402
api.register_blueprint(tasks_blp)
