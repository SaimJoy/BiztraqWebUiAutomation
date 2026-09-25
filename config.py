import os

BASE_URL = "https://biztraqonline.com/Auth/Login"
ACCOUNTS = {
    "mcc": {"username": "mcc.support", "password": "MCC.COBAIT.123"},
    "joy": {"username": "joy.triulta", "password": "12345678"},
}
ACTIVE_ACCOUNT = "mcc"

USERNAME = ACCOUNTS[ACTIVE_ACCOUNT]["username"]
PASSWORD = ACCOUNTS[ACTIVE_ACCOUNT]["password"]
DATE_OF_BIRTH = "11111990"

BIZDRIVE_FOLDER_COUNT = int(os.environ.get("BIZDRIVE_FOLDER_COUNT", "500"))
BIZDRIVE_NESTED_PER_FOLDER = int(os.environ.get("BIZDRIVE_NESTED_PER_FOLDER", "5"))
BIZDRIVE_TOTAL_FILES = int(os.environ.get("BIZDRIVE_TOTAL_FILES", "5000"))
BIZDRIVE_LOCAL_ROOT = os.environ.get("BIZDRIVE_LOCAL_ROOT", r"D:\BizdriveLoadTest")
BIZDRIVE_SLOW_MS = int(os.environ.get("BIZDRIVE_SLOW_MS", "5000"))

DEFAULT_TIMEOUT_MS = 20000
NAVIGATION_TIMEOUT_MS = 90000

os.environ.setdefault(
    "PLAYWRIGHT_BROWSERS_PATH",
    os.path.join(os.path.expanduser("~"), "AppData", "Local", "ms-playwright"),
)
