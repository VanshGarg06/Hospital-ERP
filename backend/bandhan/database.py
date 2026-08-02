"""
This module sets up the database connection and 
provides a context manager for database sessions.
"""

from __future__ import annotations
from contextlib import contextmanager
from typing import Iterator
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Session

db = SQLAlchemy()

def init_db(app) -> None:
    """
    Initialize the database with the Flask app.
    This function binds the SQLAlchemy instance to the Flask app
    and creates all tables defined in the models.
    Args:
        app: The Flask application instance.
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()

@contextmanager
def session_scope() -> Iterator[Session]:
    """
        Provide a transactional scope around a series of operations.
        This context manager ensures that the session is committed if no exceptions occur,
        and rolled back if an exception is raised. It also ensures that the session is closed
        after use.
        Yields:
            A SQLAlchemy Session object for database operations.
    """
    session: Session = db.session
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
