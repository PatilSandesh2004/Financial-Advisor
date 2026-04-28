from __future__ import annotations

import os

from sqlalchemy import create_engine

from backend.models.db_models import Base


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is not set; skipping DB init.")
        return
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    print("DB schema created")


if __name__ == "__main__":
    main()
