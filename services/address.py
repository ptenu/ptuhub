import os
import shutil
import zipfile
import click

import pandas as pd
from model import db
from model.Address import Address, Classification, Street, Postcode, Boundary

from services.files import FileService


class AddressImportService:

    DATA_S3_BUCKET = "ptu-static"
    DATA_S3_KEY = "AddressData.zip"
    DATA_SAVE_PATH = "~/AddressData"

    STREET = "ID11_Street_Records"
    STREET_DESC = "ID15_StreetDesc_Records"
    BLPU = "ID21_BLPU_Records"
    LPI = "ID24_LPI_Records"
    ORG = "ID31_Org_Records"
    CLASS = "ID32_Class_Records"
    CLASS_DEF = "addressbase-product-classification-scheme"
    POSTCODES = "ONSPD_NOV_2020_UK_PE"
    BOUNDARIES = "boundaries"

    FIELD_MAP = (
        ("UPRN", "uprn", "int"),
        ("BLPU_STATE", "state", "int"),
        ("PARENT_UPRN", "parent_uprn", "int"),
        ("LATITUDE", "latitude", "float"),
        ("LONGITUDE", "longitude", "float"),
        ("POSTCODE_LOCATOR", "postcode", "str"),
        ("MULTI_OCC_COUNT", "multi_occupancy", "int"),
        ("SAO_START_NUMBER", "sao_start_number", "int"),
        ("SAO_START_SUFFIX", "sao_start_suffix", "str"),
        ("SAO_END_NUMBER", "sao_end_number", "int"),
        ("SAO_END_SUFFIX", "sao_end_suffix", "str"),
        ("SAO_TEXT", "sao_text", "str"),
        ("PAO_START_NUMBER", "pao_start_number", "int"),
        ("PAO_START_SUFFIX", "pao_start_suffix", "str"),
        ("PAO_END_NUMBER", "pao_end_number", "int"),
        ("PAO_END_SUFFIX", "pao_end_suffix", "str"),
        ("PAO_TEXT", "pao_text", "str"),
        ("USRN", "usrn", "int"),
        ("AREA_NAME", "area_name", "str"),
        ("LEVEL", "level", "str"),
        ("CLASSIFICATION_CODE", "classification_code", "str"),
    )

    CL_FIELDS = (
        "Class_Desc",
        "Primary_Code",
        "Secondary_Code",
        "Tertiary_Code",
        "Quaternary_Code",
        "Primary_Desc",
        "Secondary_Desc",
        "Tertiary_Desc",
        "Quaternary_Desc",
    )

    def download_data(self):
        fs = FileService()
        temp_zip = fs.get_file_object(self.DATA_S3_BUCKET, self.DATA_S3_KEY)
        DATA_PATH = os.path.expanduser(self.DATA_SAVE_PATH)

        with zipfile.ZipFile(temp_zip) as zfile:
            if os.path.exists(DATA_PATH) and os.path.isdir(DATA_PATH):
                shutil.rmtree(DATA_PATH)

            os.mkdir(DATA_PATH)
            zfile.extractall(DATA_PATH)

        temp_zip.close()

    def import_addresses(self):
        """
        Import all addresses and their associated information.
        """

        DATA_PATH = os.path.expanduser(self.DATA_SAVE_PATH)

        # Load all the data
        blpu = pd.read_csv(os.path.join(DATA_PATH, f"{self.BLPU}.csv"))
        lpi = pd.read_csv(os.path.join(DATA_PATH, f"{self.LPI}.csv"))
        classes = pd.read_csv(os.path.join(DATA_PATH, f"{self.CLASS}.csv"))
        class_def = pd.read_csv(os.path.join(DATA_PATH, f"{self.CLASS_DEF}.csv"))
        streets = pd.read_csv(os.path.join(DATA_PATH, f"{self.STREET}.csv"))
        street_descr = pd.read_csv(os.path.join(DATA_PATH, f"{self.STREET_DESC}.csv"))
        postcodes = pd.read_csv(os.path.join(DATA_PATH, f"{self.POSTCODES}.csv"))
        bdry = pd.read_csv(os.path.join(DATA_PATH, f"{self.BOUNDARIES}.csv"))

        # Remove streets that no longer exist
        streets = streets[["USRN", "STREET_END_DATE"]]
        streets = streets[streets["STREET_END_DATE"].isnull()]

        # Save the classifications to the database
        with click.progressbar(
            label="Classifications (reference)".ljust(35), length=len(class_def.index)
        ) as pb:
            for row in class_def.to_dict(orient="records"):
                cl = Classification(row["Concatenated"])

                pb.update(1)
                if db.query(Classification).get(row["Concatenated"]) is not None:
                    continue

                for prop in self.CL_FIELDS:
                    if pd.isnull(row[prop]):
                        continue

                    setattr(cl, prop.lower(), row[prop])

                db.add(cl)

        db.commit()

        # Save the postcodes to the database
        postcodes = postcodes[postcodes["pcds"].str.match(r"^[A-Z]{2}[1-9]{1}\s")]
        pc_cols = postcodes.columns.values.tolist()
        pc_cols = pc_cols[3:]
        with click.progressbar(
            label="Postcodes (reference)".ljust(35), length=len(postcodes.index)
        ) as pb:
            for pc in postcodes.to_dict(orient="records"):
                pb.update(1)

                if db.query(Postcode).get(pc["pcds"]) is not None:
                    continue

                new_pc = Postcode(pc["pcds"])
                for col in pc_cols:
                    new_pc.add_code(str(pc[col]))

                db.add(new_pc)
        db.commit()

        # Save the boundaries (ward boundaries etc) to the database
        for b in bdry.to_dict(orient="records"):
            if db.query(Boundary).get(b["code"]) is not None:
                continue
            new_bdry = Boundary(**b)
            db.add(new_bdry)

        db.commit()

        # Do the addresses!
        blpu = blpu[
            [
                "UPRN",
                "LOGICAL_STATUS",
                "BLPU_STATE",
                "PARENT_UPRN",
                "LATITUDE",
                "LONGITUDE",
                "POSTCODE_LOCATOR",
                "MULTI_OCC_COUNT",
            ]
        ]

        blpu = blpu[blpu["LOGICAL_STATUS"] == 1]
        blpu = blpu.drop(columns="LOGICAL_STATUS")
        blpu = blpu[blpu["POSTCODE_LOCATOR"].isin(postcodes["pcds"])]

        lpi = lpi[
            [
                "UPRN",
                "LOGICAL_STATUS",
                "SAO_START_NUMBER",
                "SAO_START_SUFFIX",
                "SAO_END_NUMBER",
                "SAO_END_SUFFIX",
                "SAO_TEXT",
                "PAO_START_NUMBER",
                "PAO_START_SUFFIX",
                "PAO_END_NUMBER",
                "PAO_END_SUFFIX",
                "PAO_TEXT",
                "USRN",
                "AREA_NAME",
                "LEVEL",
            ]
        ]

        lpi = lpi[lpi["LOGICAL_STATUS"] == 1]
        lpi = lpi[lpi["UPRN"].isin(blpu["UPRN"])]
        lpi = lpi[lpi["USRN"].isin(streets["USRN"])]
        lpi = lpi.drop(columns=["LOGICAL_STATUS"])

        addresses = pd.merge(blpu, lpi, on="UPRN", sort=False)
        classes = classes[["UPRN", "CLASSIFICATION_CODE", "END_DATE", "CLASS_SCHEME"]]
        classes = classes[
            classes["CLASS_SCHEME"] == "AddressBase Premium Classification Scheme"
        ]
        classes = classes[classes["END_DATE"].isna()]
        classes = classes.drop(columns=["END_DATE", "CLASS_SCHEME"])
        addresses = pd.merge(addresses, classes, on="UPRN", how="left")

        for cl in ("L", "P"):
            addresses = addresses[~addresses["CLASSIFICATION_CODE"].str.startswith(cl)]

        addresses = addresses.sort_values(by=["PARENT_UPRN"], na_position="first")

        # Import streets
        streets = pd.read_csv(os.path.join(DATA_PATH, f"{self.STREET}.csv"))
        streets = pd.merge(streets, street_descr, on="USRN", sort=False)

        with click.progressbar(
            label="Streets".ljust(35), length=len(streets.index)
        ) as pb:
            for row in streets.to_dict(orient="records"):
                pb.update(1)
                if db.query(Street).get(int(row["USRN"])) is not None:
                    continue

                new_street = Street(row["USRN"])
                if not pd.isna(row["STREET_END_DATE"]):
                    continue

                if not pd.isna(row["STATE"]):
                    new_street.state_code = row["STATE"]

                if not pd.isna(row["STREET_SURFACE"]):
                    new_street.surface_code = row["STREET_SURFACE"]

                if not pd.isna(row["STREET_CLASSIFICATION"]):
                    new_street.classification_code = row["STREET_CLASSIFICATION"]

                if not pd.isna(row["STREET_DESCRIPTION"]):
                    new_street.description = row["STREET_DESCRIPTION"]

                if not pd.isna(row["LOCALITY"]):
                    new_street.locality = row["LOCALITY"]

                if not pd.isna(row["TOWN_NAME"]):
                    new_street.town = row["TOWN_NAME"]

                if not pd.isna(row["ADMINISTRATIVE_AREA"]):
                    new_street.admin_area = row["ADMINISTRATIVE_AREA"]

                db.add(new_street)

            db.commit()

            # Finish addresses
            x = 0
            with click.progressbar(
                label="Addresses".ljust(35), length=len(addresses.index)
            ) as pb:
                for addr in addresses.to_dict(orient="records"):
                    pb.update(1)
                    x += 1

                    addr_object = db.query(Address).get(int(addr["UPRN"]))
                    if addr_object is not None:
                        continue

                    addr_object = Address(int(addr["UPRN"]))

                    for attribute, prop, dtype in self.FIELD_MAP:
                        if pd.isnull(addr[attribute]):
                            continue

                        if attribute == "PARENT_UPRN":
                            parent = db.query(Address).get(addr[attribute])
                            if parent is None:
                                continue
                            addr_object.parent = parent
                            continue

                        if dtype == "str":
                            setattr(addr_object, prop, str(addr[attribute]))
                            continue

                        if dtype == "int":
                            setattr(addr_object, prop, int(addr[attribute]))
                            continue

                        if dtype == "float":
                            setattr(addr_object, prop, float(addr[attribute]))
                            continue

                    db.add(addr_object)

                    if x % 1000 == 0:
                        db.commit()

                db.commit()

            click.echo(click.style("Done!", fg="green"))
