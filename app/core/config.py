from pathlib import Path
from pydantic import BaseModel


class AppConfig(BaseModel):
    """
    Central application configuration.

    This lightweight config object keeps paths and simple constants in one
    place so they can be imported without creating circular dependencies.
    """

    project_name: str = (
        "A Multi-Modal AI Framework for Adaptive Insulin Dosage Optimization in "
        "Type 2 Diabetes Management"
    )
    api_v1_prefix: str = "/api/v1"

    # Paths
    root_dir: Path = Path(__file__).resolve().parents[2]
    data_dir: Path = root_dir / "data"
    sqlite_path: Path = data_dir / "app.db"


config = AppConfig()

# Ensure that the data directory exists at import time so that the SQLite
# database can be created lazily by SQLAlchemy on first use.
config.data_dir.mkdir(parents=True, exist_ok=True)

