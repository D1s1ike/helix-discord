import re

pattern_digits_and_uppercase = re.compile(r'[^0-9A-Z]')
pattern_digits_and_lowercase_and_dash = re.compile(r'[^0-9a-z-]')
pattern_digits = re.compile(r'[^0-9]')

def sanitize_code(code: str) -> str:
    return pattern_digits_and_uppercase.sub('', code).upper()

def sanitize_helix_id(helix_id: str) -> str:
    return pattern_digits_and_lowercase_and_dash.sub('', helix_id).lower()

def sanitize_discord_id(discord_id: str) -> str:
    return pattern_digits.sub('', discord_id)
