from services.address import AddressImportService
from model.Organisation import Branch
from model import db


def download():
    ais = AddressImportService()
    ais.download_data()


def do_import():
    ais = AddressImportService()
    ais.import_addresses()


def get_branch_members_from_id(branch_id):
    branch = db.query(Branch).get(branch_id)
    if branch is None:
        return

    return branch.contacts
