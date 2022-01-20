from services.address import AddressImportService


def download():
    ais = AddressImportService()
    ais.download_data()


def do_import():
    ais = AddressImportService()
    ais.import_addresses()
