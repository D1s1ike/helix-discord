import zenora
import zenora.exceptions
from os import getenv
from urllib import parse
from time import sleep
from threading import Thread
import zenora.errors
from utils.DBUtils import DBUtils
from utils.SanitizeText import sanitize_code


class Config:
    def __init__(self):
        self.client_id = getenv("DISCORD_CLIENT_ID")
        self.client_secret = getenv("DISCORD_CLIENT_SECRET")
        self.redirect_uri = getenv("DISCORD_REDIRECT_URI")
        self.oauth_url = f"https://discord.com/oauth2/authorize?client_id={self.client_id}&response_type=code&redirect_uri={parse.quote(self.redirect_uri)}&scope=identify+email+guilds"
        self.bot_token = getenv("DISCORD_APPLICATION_TOKEN")

        if not all([self.client_id, self.client_secret, self.redirect_uri, self.bot_token]):
            raise ValueError("One or more required environment variables are missing for Discord configuration.")


class OAuthTokens(object):
    def __init__(self, access_token: str, refresh_token: str, expires_in: int):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_in = expires_in

    def __repr__(self):
        return f"OAuthTokens(access_token={self.access_token}, refresh_token={self.refresh_token}, expires_in={self.expires_in})"

class DiscordClient:
    def __init__(self, root_path: str, dbutils: DBUtils):
        self.config = Config()
        self.dbutils = dbutils
        self.z_client = zenora.APIClient(token=self.config.bot_token, client_secret=self.config.client_secret)
        self.oauth_discord_url = 'https://discord.com/api/v10/oauth2/token'
        self.new_users = {}
        self.new_users_thread = Thread(target=self.new_users_loop)
        if not self.new_users_thread.is_alive():
            self.new_users_thread.start()
        self.proccesing = []

    def generate_tokens(self, code):
        try:
            tokens = self.z_client.oauth.get_access_token(code, redirect_uri=self.config.redirect_uri)
        except Exception as e:
            print(f"Failed to get access token: {e}")
            return None
        return tokens

    def new_users_loop(self):
        while True:
            for token in self.new_users:
                if self.new_users[token][0] in ["success", "fail"]:
                    continue
                if token in self.proccesing:
                    continue
                self.proccesing.append(token)
                t = Thread(target=self.login_callback, args=(token,))
                t.start()
                t.join()
            sleep(1)

    def login_callback(self, connect_code: str):
        code = self.new_users[connect_code][1]
        try:
            helix_id = self.dbutils.get_helix_id_by_code(sanitize_code(connect_code))
            if not helix_id:
                self.new_users[connect_code][0] = "fail"
                return
            tokens = self.generate_tokens(code)
            if not tokens:
                self.new_users[connect_code][0] = "fail"
                return
            bearer_client = zenora.APIClient(token=tokens.access_token, bearer=True)
            current_user = bearer_client.users.get_current_user()
            if not helix_id:
                self.new_users[connect_code][0] = "fail"
                return
            status = self.dbutils.create_user(
                discord_id=str(current_user.id),
                helix_id=helix_id
            )
            if status:
                self.new_users[connect_code][0] = "success"
            else:
                self.new_users[connect_code][0] = "fail"
                print(f'Failed to create / log in user {current_user.id} with code {code}')
        except Exception as e:
            print(f'Failed to login new user with code {code}: {e}')
            self.new_users[connect_code][0] = "fail"
