from falcon.errors import HTTPNotFound
from falcon.status_codes import HTTP_204
import api.middleware.authentication as auth
from api.interface.cms import ContentInterface
import falcon


class PublicPageResource:
    def on_get_all(self, req, resp):
        pages = ContentInterface(self.session).get_pages()
        page_list = []
        for p in pages:
            page_list.append(
                {
                    "slug": p.slug,
                    "title": p.title,
                    "category": p.category,
                    "description": p.description,
                }
            )

        resp.media = page_list

    def on_get_category(self, req, resp, category: str):
        pages = ContentInterface(self.session).get_pages(category=category)
        page_list = []
        for p in pages:
            page_list.append(
                {
                    "slug": p.slug,
                    "title": p.title,
                    "category": p.category,
                    "description": p.description,
                }
            )

        resp.media = page_list

    def on_get_page(self, req, resp, slug: str):
        page = ContentInterface(self.session).get_pages(slug=slug)
        if page is None:
            raise HTTPNotFound
        resp.media = {
            "page": {
                "title": page.title,
                "category": page.category,
                "body": page.body,
                "description": page.description,
                "created": page._created_on.isoformat(),
                "updated": page._updated_on.isoformat()
                if page._updated_on is not None
                else None,
            }
        }


@falcon.before(auth.EnforceRoles, ["cms.manage"])
class AdminPageResource:
    def on_get_pages(self, req, resp):
        category = None

        if "category" in req.params:
            category = req.params["category"]

        pages = ContentInterface(self.session).get_pages(category=category, all=True)
        page_list = []
        for p in pages:
            page_list.append(
                {
                    "slug": p.slug,
                    "title": p.title,
                    "category": p.category,
                    "description": p.description,
                    "publish_date": p.publish_on.isoformat()
                    if p.publish_on is not None
                    else None,
                    "status": p.status,
                }
            )

        resp.media = page_list

    def on_get_page(self, req, resp, slug: str):
        page = ContentInterface(self.session).get_pages(slug=slug, all=True)
        if page is None:
            raise HTTPNotFound
        resp.media = {
            "page": {
                "title": page.title,
                "category": page.category,
                "body": page.body,
                "description": page.description,
                "created": page._created_on.isoformat(),
                "updated": page._updated_on.isoformat()
                if page._updated_on is not None
                else None,
                "publish_date": page.publish_on.isoformat()
                if page.publish_on is not None
                else None,
                "status": page.status,
                "created_by": {"name": page.created_by.name, "id": page.created_by.id},
            }
        }

    def on_post_pages(self, req, resp):
        current_user = req.context.user
        attributes = req.get_media()
        page = ContentInterface(self.session).create_page(
            created_by=current_user, **attributes
        )
        resp.media = {
            "page": {
                "title": page.title,
                "category": page.category,
                "body": page.body,
                "description": page.description,
                "created": page._created_on.isoformat(),
                "updated": page._updated_on.isoformat()
                if page._updated_on is not None
                else None,
                "publish_date": page.publish_on.isoformat()
                if page.publish_on is not None
                else None,
                "status": page.status,
                "created_by": {"name": page.created_by.name, "id": page.created_by.id},
            }
        }

    def on_patch_page(self, req, resp, slug: str):
        attributes = req.get_media()
        page = ContentInterface(self.session).update_page(slug=slug, **attributes)
        resp.media = {
            "page": {
                "title": page.title,
                "category": page.category,
                "body": page.body,
                "description": page.description,
                "created": page._created_on.isoformat(),
                "updated": page._updated_on.isoformat()
                if page._updated_on is not None
                else None,
                "publish_date": page.publish_on.isoformat()
                if page.publish_on is not None
                else None,
                "status": page.status,
                "created_by": {"name": page.created_by.name, "id": page.created_by.id},
            }
        }

    def on_delete_page(self, req, resp, slug: str):
        ContentInterface(self.session).delete_page(slug)

        resp.status = HTTP_204
