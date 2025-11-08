from flask_sqlalchemy import SQLAlchemy
from pytz import timezone
from os import getenv
from datetime import datetime

TIMEZONE = timezone(getenv("TIMEZONE", "Asia/Jerusalem"))

db = SQLAlchemy()
db.timezone = TIMEZONE

class Code(db.Model):
    __tablename__ = "codes"
    helix_id = db.Column(db.String(255), primary_key=True, nullable=False, unique=True)
    code = db.Column(db.String(64), unique=True, nullable=False)
    creator_ip = db.Column(db.String(45), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(TIMEZONE), nullable=False)

class User(db.Model):
    __tablename__ = "users"
    discord_id = db.Column(db.String(32), primary_key=True, nullable=False)
    helix_id = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(TIMEZONE), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(TIMEZONE), onupdate=lambda: datetime.now(TIMEZONE), nullable=False)

    def to_dict(self):
        return {
            "discord_id": self.discord_id,
            "helix_id": self.helix_id,
            "created_at": self.created_at.astimezone(TIMEZONE).isoformat(),
            "updated_at": self.updated_at.astimezone(TIMEZONE).isoformat()
        }

def get_db():
    return db

