from utils.DatabaseBase import User, Code
from random import choices
from string import ascii_uppercase, digits
from utils.SanitizeText import sanitize_helix_id

DB_ERROR = "Database connection could not be established."

class DBUtils:
    def __init__(self, db, app):
        self.db = db
        self.app = app

    @staticmethod
    def _generate_random_code():
        while True:
            code = ''.join(choices(ascii_uppercase + digits, k=16))
            existing_code = Code.query.filter_by(code=code).first()
            if not existing_code:
                break
        return code

    def get_users_by_discord_ids(self, user_ids: list, to_dict: bool):
        users = []
        with self.app.app_context():
            if user_ids:
                users = User.query.filter(User.discord_id.in_(user_ids)).all()
            else:
                users = User.query.all()
        if to_dict:
            return [
                {
                    "discord_id": user.discord_id,
                    "helix_id": user.helix_id
                } for user in users
            ]
        return users

    def get_helix_id_by_code(self, code: str):
        code_entry = None
        try:
            code_entry = Code.query.filter_by(code=code).first()
        except:
            with self.app.app_context():
                code_entry = Code.query.filter_by(code=code).first()
        if code_entry:
            return code_entry.helix_id
        return None

    def get_connect_code(self, helix_id: str):
        code = Code.query.filter_by(helix_id=helix_id).first()
        if code:
            return code.code
        return None

    def generate_helix_code(self, helix_id: str, creator_ip: str):
        if not self.app.helix_utils.validate_helix_id(helix_id):
            return None
        code = self.get_connect_code(helix_id)
        if code:
            return code
        code = Code(
            helix_id=helix_id,
            code=self._generate_random_code(),
            creator_ip=creator_ip
        )
        self.db.session.add(code)
        self.db.session.commit()
        return code.code

    def create_user(self, discord_id: str, helix_id: str):
        try:
            with self.app.app_context():
                helix_id = sanitize_helix_id(helix_id)
                code_entry = Code.query.filter_by(helix_id=helix_id).first()
                if not code_entry:
                    return None
                self.db.session.delete(code_entry)
                self.db.session.commit()
                existing_user = User.query.filter_by(helix_id=helix_id).first()
                if not existing_user:
                    existing_user = User.query.filter_by(discord_id=discord_id).first()
                if existing_user:
                    if existing_user.discord_id != discord_id:
                        existing_user.discord_id = discord_id
                    if existing_user.helix_id != helix_id:
                        existing_user.helix_id = helix_id
                    self.db.session.commit()
                    return existing_user
                new_user = User(
                    discord_id=discord_id,
                    helix_id=helix_id
                )
                self.db.session.add(new_user)
                self.db.session.commit()
                return new_user
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
