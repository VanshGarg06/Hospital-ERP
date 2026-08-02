from pathlib import Path

from flask import Flask, send_from_directory
from flask_cors import CORS

from .database import init_db
from .routes import api_bp

# Get the project root directory (two levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def create_app(testing: bool = False) -> Flask:
    app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="/static")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hospital_erp.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    CORS(app)

    init_db(app)

    app.register_blueprint(api_bp, url_prefix="/api")

    @app.route("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    # Serve index.html at root
    @app.route("/")
    def index():
        return send_from_directory(str(FRONTEND_DIR), "index.html")

    # Serve static files (CSS, JS, etc.)
    @app.route("/<path:filename>")
    def serve_static(filename: str):
        # Don't serve API routes as static files
        if filename.startswith("api/"):
            return {"error": "Not found"}, 404
        try:
            return send_from_directory(str(FRONTEND_DIR), filename)
        except FileNotFoundError:
            # For SPA, return index.html for non-API routes
            return send_from_directory(str(FRONTEND_DIR), "index.html")

    return app

app = create_app()