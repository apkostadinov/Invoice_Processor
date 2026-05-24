from app.db.database import engine, Base
from app.models.invoice import Invoice


def init_db():
    Base.metadata.create_all(bind=engine)