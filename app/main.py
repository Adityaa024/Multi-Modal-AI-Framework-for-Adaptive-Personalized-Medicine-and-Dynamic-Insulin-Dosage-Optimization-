import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import patients, predictions
from app.core.config import config
from app.db.models import Base
from app.db.session import engine


def create_app() -> FastAPI:
    """
    Application factory used for both production and test instances.

    Using a factory (rather than a global app) keeps initialization explicit
    and makes it straightforward to spin up ephemeral apps in unit tests.
    """

    app = FastAPI(
        title=config.project_name,
        version="0.1.0",
        description=(
            "Research-grade backend for exploring multi-modal AI approaches "
            "to adaptive insulin dosage optimization in Type 2 diabetes "
            "management. Not for clinical use."
        ),
    )

    allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
    allowed_origins = [
        origin.strip()
        for origin in allowed_origins_env.split(",")
        if origin.strip()
    ]

    # Always ensure local dev ports are permitted
    for dev_origin in ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]:
        if dev_origin not in allowed_origins:
            allowed_origins.append(dev_origin)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=r"https:\/\/.*\.onrender\.com",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize database metadata. For a pure research scaffold we keep this
    # simple and rely on SQLAlchemy's metadata creation instead of migrations.
    Base.metadata.create_all(bind=engine)

    # Mount versioned API routers
    app.include_router(
        patients.router,
        prefix=config.api_v1_prefix,
    )
    app.include_router(
        predictions.router,
        prefix=config.api_v1_prefix,
    )

    return app


app = create_app()

