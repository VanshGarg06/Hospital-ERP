from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Session

db = SQLAlchemy()


def init_db(app) -> None:
    db.init_app(app)
    with app.app_context():
        db.create_all()


@contextmanager
def session_scope() -> Iterator[Session]:
    session: Session = db.session
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

