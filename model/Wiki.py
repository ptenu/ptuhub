from email.policy import default
from sqlalchemy import TEXT, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, backref
from model import Model
from services.permissions import trusted_user


class WikiPage(Model):
    __tablename__ = "wiki_pages"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), unique=True, index=True)
    created_by = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    created_on = Column(DateTime, default="NOW()")
    parent_id = Column(Integer, ForeignKey("wiki_pages.id"), nullable=True)

    children = relationship("WikiPage", backref=backref("parent", remote_side=[id]))


class Tag(Model):
    __tablename__ = "wiki_tag"

    parent_id = Column(Integer, ForeignKey("wiki_pages.id"), primary_key=True)
    tag = Column(String, primary_key=True)

    page = relationship(WikiPage, backref="tags")


class WikiText(Model):
    __tablename__ = "wiki_text"

    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey("wiki_pages.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    created_on = Column(DateTime, default="NOW()")
    body = Column(TEXT, nullable="False")

    page = relationship(
        WikiPage, backref=backref("versions", order_by=created_on.desc())
    )

    def view_guard(self, contact):
        trusted_user(contact)


class Interlink(Model):
    __tablename__ = "wiki_interlinks"

    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey("wiki_pages.id"), nullable=False)
    links_to = Column(Integer, ForeignKey("wiki_pages.id"), nullable=True)
    links_to_title = Column(String, nullable=True)

    page = relationship(WikiPage, backref="interlinks", foreign_keys=[page_id])
    links_to = relationship(WikiPage, backref="linked_from", foreign_keys=[links_to])

    @property
    def redlink(self):
        return self.links_to_title is not None and self.links_to is None
