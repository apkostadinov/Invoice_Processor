from app.db.base import Base
from app.db.session import engine

from app.db.models.invoice import InvoiceModel
from app.db.models.line_item import LineItemModel


def init_db():
    Base.metadata.create_all(bind=engine)