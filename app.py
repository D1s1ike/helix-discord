from random import choices
from flask import Flask, request, abort
from flask_limiter import Limiter
from flask_wtf.csrf import CSRFProtect
from functools import lru_cache
from dotenv import load_dotenv
import tempfile
from pytz import timezone
from utils.HelixUtils import HelixUtils
load_dotenv()
from utils.DisUtils import DiscordClient
from utils.DBUtils import DBUtils
from utils.DatabaseBase import get_db
from os import listdir, path, getenv
from json import load
from colorama import Fore
from waitress import serve
from hashlib import sha256
import logging

tempfile.tempdir = getenv("TMPDIR", tempfile.gettempdir())

logging.basicConfig(
    level=logging.INFO,
    format=f"{Fore.GREEN}%(asctime)s{Fore.RESET} - {Fore.LIGHTBLUE_EX}[%(levelname)s]{Fore.RESET} - {Fore.LIGHTWHITE_EX}%(message)s{Fore.RESET}",
)

logger = logging.getLogger(__name__)

db = get_db()

locals = {
    "title": getenv("SITE_TITLE", "Helix - Discord"),
}


@lru_cache(maxsize=32)
def load_json_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return load(f)


def get_sender_ip():
    addr = request.headers.get("X-Forwarded-For", request.headers.get("CF-Connecting-IP", request.remote_addr))
    return addr or "Unknown"

def set_sql_alchemy_uri(app: Flask):
    db_type = getenv("DB_TYPE", "sqlite").lower()
    if db_type == "sqlite":
        db_name = getenv("SQLITE_DB_NAME", "database.db")
        uri = f"sqlite:///{db_name}"
    elif db_type == "postgresql":
        user = getenv("POSTGRES_USER", "user")
        password = getenv("POSTGRES_PASSWORD", "password")
        host = getenv("POSTGRES_HOST", "localhost")
        port = getenv("POSTGRES_PORT", "5432")
        db_name = getenv("POSTGRES_DB_NAME", "database")
        uri = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    elif db_type == "mysql":
        user = getenv("MYSQL_USER", "user")
        password = getenv("MYSQL_PASSWORD", "password")
        host = getenv("MYSQL_HOST", "localhost")
        port = getenv("MYSQL_PORT", "3306")
        db_name = getenv("MYSQL_DB_NAME", "database")
        uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
    else:
        raise ValueError(f"Unsupported DB_TYPE: {db_type}")
    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

def get_limiter(app):
    default_limits = getenv("DEFAULT_LIMITS", '').split(',')
    print(default_limits)
    limiter = Limiter(
        key_func=get_sender_ip,
        app=app,
        strategy="fixed-window",
        default_limits=default_limits,
    )
    print(limiter)
    return limiter

def generate_random():
    return ''.join(choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=32))

class App(Flask):
    def __init__(self):
        super().__init__(__name__)
        self.config["SECRET_KEY"] = getenv("SECRET_KEY", generate_random())
        self.config["TEMPLATES_AUTO_RELOAD"] = True
        set_sql_alchemy_uri(self)
        self.locals = locals
        self.get_sender_ip = get_sender_ip
        self.csrf = CSRFProtect(self)
        self.limiter = get_limiter(self)
        self.max_file_size_mb = int(getenv("MAX_FILE_SIZE_MB", 50))
        self.timezone = db.timezone if hasattr(db, 'timezone') else timezone(getenv("TIMEZONE", "Asia/Jerusalem"))
        self.api_key = sha256(getenv("API_KEY").encode("utf-8")).hexdigest()
        self.code_api_key = sha256(getenv("CODE_REQUEST_API_KEY", generate_random()).encode("utf-8")).hexdigest()
        db.init_app(self)
        with self.app_context():
            db.create_all()
        self.dbutils = DBUtils(db, self)
        self.discord = DiscordClient(self.root_path, self.dbutils)
        self.helix_utils = HelixUtils(self)
        self.register_routes()


        allowed_domain = getenv("ALLOWED_DOMAIN")
        if allowed_domain:
            @self.before_request
            def restrict_domain():
                host = request.host.split(':')[0]
                if host != allowed_domain:
                    return abort(403)

    def register_routes(self):
        for ext in listdir("extensions"):
            if ext.endswith(".py"):
                module_name = ext[:-3]
                module = __import__(f"extensions.{module_name}", fromlist=[""])
                try:
                    module.setup(self)
                except Exception as e:
                    logging.error(f"Failed to setup {module_name}: {str(e)}")
                    raise

def create_app():
    try:
        app = App()
        return app
    except Exception as e:
        logging.critical(f"Failed to initialize app: {str(e)}")
        return None

def run_app(app: Flask):
    FLASK_ENVIRONMENT = getenv("FLASK_ENV", "development")
    FLASK_HOST = getenv("FLASK_HOST", "localhost")
    FLASK_PORT = int(getenv("FLASK_PORT", 8000))
    FLASK_DEBUG = getenv("FLASK_DEBUG", "false").lower() == "true"
    FLASK_ENABLE_CERTS = getenv("FLASK_ENABLE_CERTS", "false").lower() == "true"
    CERTS_DIR = getenv("CERTS_DIR") if FLASK_ENABLE_CERTS else None
    ssl_context = None
    if FLASK_ENABLE_CERTS:
        if not CERTS_DIR or not path.exists(CERTS_DIR):
            logging.critical("CERTS_DIR is not set or does not exist. Cannot enable SSL.")
            exit(1)
        cert_path = path.join(CERTS_DIR, "cert.pem")
        key_path = path.join(CERTS_DIR, "key.pem")
        if not path.isfile(cert_path) or not path.isfile(key_path):
            logging.critical("Certificate files not found in CERTS_DIR. Cannot enable SSL.")
            exit(1)
        ssl_context = (cert_path, key_path)
        logging.info("SSL context set with provided certificates.")

    logging.info(f"Starting app in {FLASK_ENVIRONMENT} mode on {FLASK_HOST}:{FLASK_PORT} with debug={FLASK_DEBUG}")
    if FLASK_ENVIRONMENT == "production":
        serve(app, host=FLASK_HOST, port=FLASK_PORT, threads=4, url_scheme="https" if ssl_context else "http")
    else:
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, ssl_context=ssl_context)

if __name__ == "__main__":
    app = create_app()
    if not app:
        logging.critical("Application failed to start due to initialization error.")
        exit(1)
    run_app(app)
