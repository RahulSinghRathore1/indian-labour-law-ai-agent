from dotenv import load_dotenv
import os
import pathlib

# ---------------------------------------------------------
# Load .env from project root (2 levels above /src/database/)
# ---------------------------------------------------------
# db.py is at: project/src/database/db.py
# .env is at:  project/.env
# Therefore: parents[2] gives project root folder
ENV_PATH = pathlib.Path(__file__).resolve().parents[2] / ".env"

print("Loading .env from:", ENV_PATH)

load_dotenv(dotenv_path=ENV_PATH)

# ---------------------------------------------------------
# Flask + SQLAlchemy setup
# ---------------------------------------------------------
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)


def create_app():
    app = Flask(__name__)
    CORS(app)

    # Load secret key
    app.secret_key = os.environ.get("SESSION_SECRET") or "labour-law-agent-secret-key"

    # Load DB connection from .env
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    return app
