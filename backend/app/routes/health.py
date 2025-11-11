from flask_smorest import Blueprint
from flask.views import MethodView

# PUBLIC_INTERFACE
# Health check blueprint for liveness probe
blp = Blueprint("Health Check", "health", url_prefix="/", description="Health check route")


@blp.route("/")
class HealthCheck(MethodView):
    """Simple health endpoint returning status JSON."""
    def get(self):
        return {"message": "Healthy"}
