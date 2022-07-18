from sqlalchemy.sql.sqltypes import Boolean
from model import Model
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    BigInteger,
)
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as EnumColumn
from enum import Enum
from datetime import datetime


class Page(Model):

    __tablename__ = "pages"

    id = Column(Integer, primary_key=True)
    slug = Column(String(255), unique=True)
    title = Column(String(255), nullable=False)
    image_id = Column(String(10), ForeignKey("files.id"))
    description = Column(Text)
    body = Column(Text)
    category = Column(String(25), index=True)
    archived = Column(Boolean, nullable=False, default=False)
    publish_on = Column(DateTime, nullable=True)

    # Meta
    _created_on = Column(DateTime, default=datetime.now())
    _updated_on = Column(DateTime, onupdate=datetime.now())
    _created_by = Column(
        Integer, ForeignKey("contacts.id", onupdate="CASCADE", ondelete="SET NULL")
    )

    # Relations
    image = relationship("File", backref="page_image")
    created_by = relationship("Contact", backref="pages", foreign_keys=[_created_by])

    @property
    def status(self):
        if self.archived:
            return "archived"

        if self.publish_on is None:
            return "draft"

        if self.publish_on > datetime.now():
            return "scheduled"

        if self.publish_on < datetime.now():
            return "published"
