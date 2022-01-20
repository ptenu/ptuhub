from datetime import datetime, timedelta

from sqlalchemy import Column, Date, DateTime
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
import random, base64

from model import Model


class File(Model):

    __tablename__ = "files"

    id = Column(String(10), primary_key=True)
    name = Column(String(255), nullable=False)
    ext = Column(String(10), nullable=False)
    mime_type = Column(String(50))
    size = Column(Integer)
    bucket = Column(String(50))
    key = Column(String(1024))
    description = Column(Text)
    public_url = Column(Text, nullable=True)
    delete_after = Column(DateTime, nullable=True)

    # Meta
    _created_on = Column(DateTime, default=datetime.now())
    _updated_on = Column(DateTime, default=datetime.now(), onupdate=datetime.now())
    _created_by = Column(
        Integer, ForeignKey("contacts.id", onupdate="CASCADE", ondelete="SET NULL")
    )

    uploaded_by = relationship("Contact", backref="files", foreign_keys=[_created_by])

    def __init__(self) -> None:
        bytes = random.randbytes(8)
        code = base64.b64encode(bytes)
        self.id = code.decode("ascii")[:10]
        self.delete_after = datetime.today() + timedelta(hours=24)
