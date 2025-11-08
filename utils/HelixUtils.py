import re

class HelixUtils:
    def __init__(self, app):
        self.app = app
        self.pattern = re.compile(r'^[0-9a-fA-F]+(-[0-9a-fA-F]+){4}$')

    def validate_helix_id(self, helix_id: str):
        # There is no user profile endpoint in Helix (A public one), so we just validate the format here
        return bool(self.pattern.match(helix_id))
