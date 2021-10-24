from datetime import datetime
from falcon.errors import HTTPNotFound
from sqlalchemy.sql.sqltypes import Boolean
from model import Session
from model.Content import Page
from model.File import File


class ContentInterface:
    def __init__(self, session: Session):
        self.db = session

    def get_pages(self, slug: str = None, category: str = None, all: Boolean = False):
        db = self.db
        qry = db.query(Page)

        if not all:
            qry = (
                qry.filter(Page.archived == False)
                .filter(Page.publish_on != None)
                .filter(Page.publish_on < datetime.now())
            )

        if category is not None:
            qry = qry.filter(Page.category == category.lower())

        if slug is not None:
            qry = qry.filter(Page.slug == slug.lower())
            return qry.first()

        qry = qry.order_by(Page._created_on.desc())

        return qry.all()

    def create_page(self, **kwargs):
        page = Page()

        for key, value in kwargs.items():
            if key == "id":
                continue

            if hasattr(page, key):
                setattr(page, key, value)

        self.db.add(page)
        self.db.commit()

        return page

    def update_page(self, slug: str, **kwargs):
        page = self.db.query(Page).filter(Page.slug == slug.lower()).first()

        if page is None:
            raise HTTPNotFound

        for key, value in kwargs.items():
            if key in ("id", "slug"):
                continue

            if hasattr(page, key):
                setattr(page, key, value)

        self.db.add(page)
        self.db.commit()

        return page

    def delete_page(self, slug: str):
        db = self.db
        page = db.query(Page).filter(Page.slug == slug.lower()).first()

        if page is None:
            raise HTTPNotFound

        page.archived = True
        db.commit()
