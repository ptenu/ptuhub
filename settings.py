import os
import configparser

config = configparser.ConfigParser()

DEFAULT_FILE = "default.env.ini"
TEST_FILE = "test.env.ini"
PROD_FILE = "prod.env.ini"
LOCAL_FILE = "local.env.ini"

any_file = False
if os.path.isfile(DEFAULT_FILE):
    config.read(DEFAULT_FILE)
    any_file = True

if os.path.isfile(TEST_FILE):
    config.read(TEST_FILE)
    any_file = True

if os.path.isfile(PROD_FILE):
    config.read(PROD_FILE)
    any_file = True

if os.path.isfile(LOCAL_FILE):
    config.read(LOCAL_FILE)
    any_file = True

if not any_file:
    raise Exception("No configuration file found.")


DATABASE = {
    "engine": config["database"].get("engine", "postgresql"),
    "username": config["database"].get("username", "root"),
    "password": config["database"].get("password", ""),
    "host": config["database"].get("host", "localhost"),
    "port": config["database"].get("port", "5432"),
    "db_name": config["database"].get("db_name", "api"),
}
