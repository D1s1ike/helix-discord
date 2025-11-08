# Helix Discord Linker

A small Flask service that links a Discord account to a Helix ID using a one-time code and Discord OAuth2.

## Features
- Discord OAuth2 login
- Two API keys: one for code generation, one for reading users
- SQLite by default; PostgreSQL/MySQL supported
- Rate limiting (Flask-Limiter) + CSRF (Flask-WTF)
- Optional domain restriction & HTTPS

## Usage (Production)
1. Install dependencies:
```cmd
pip install --upgrade pip
pip install -r requirements.txt
```
2. Create a `.env` file (example below) with all required settings.
3. Run the server:
```cmd
python app.py
```
`FLASK_ENV=production` in `.env` makes the app use `waitress` automatically.

### Example `.env`
```env
# Discord OAuth
DISCORD_CLIENT_ID=123456789012345678
DISCORD_CLIENT_SECRET=your_client_secret
DISCORD_REDIRECT_URI=https://your.domain/login-callback
DISCORD_APPLICATION_TOKEN=your_bot_token

# API keys (raw values sent by clients; server hashes internally)
API_KEY=main_api_key_value
CODE_REQUEST_API_KEY=code_generation_key_value

# Flask / App
FLASK_ENV=production # development or production
SECRET_KEY=strong_flask_secret
SITE_TITLE=Helix Discord Linker
TIMEZONE=UTC
DEFAULT_LIMITS=100/hour,10/minute
ALLOWED_DOMAIN=your.domain            # optional

# Database (SQLite default)
DB_TYPE=sqlite
SQLITE_DB_NAME=database.db
# PostgreSQL (uncomment and switch DB_TYPE):
# DB_TYPE=postgresql
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=postgres
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_DB_NAME=helix
# MySQL (uncomment and switch DB_TYPE):
# DB_TYPE=mysql
# MYSQL_USER=root
# MYSQL_PASSWORD=secret
# MYSQL_HOST=localhost
# MYSQL_PORT=3306
# MYSQL_DB_NAME=helix

# Optional HTTPS (self-hosted certs)
FLASK_ENABLE_CERTS=false
CERTS_DIR=C:\\path\\to\\certs   # contains cert.pem & key.pem when FLASK_ENABLE_CERTS=true
```

## Auth
- Clients send a raw API key in header: `X-API-KEY: <key>`.
- Two distinct keys:
  - `API_KEY`: access to general data (`/api/users`).
  - `CODE_REQUEST_API_KEY`: required to generate linking codes (`/api/get-code/<helix_id>`).
## Endpoints
### Public UI / Flow
- `GET /` or `GET /<code>`: Landing page; if `<code>` valid it is stored in session.
- `GET /login`: Redirects user to Discord OAuth.
- `GET /login-callback`: Handles Discord redirect; starts async linking process and sets `token` cookie.
- `GET /login/status`: Returns JSON `{status: success|wait|fail}` based on linking progress.
- `GET /linked`: Simple confirmation page after success.

### API (Requires Header `X-API-KEY`)
- `GET /api/get-code/<helix_id>` (requires `CODE_REQUEST_API_KEY`)
  - Response: `{ "helix_id": "...", "code": "..." }`
  - Validates Helix ID format (hex groups with dashes).
- `GET /api/users` (requires `API_KEY`)
  - Optional JSON body: `{ "users": ["<discord_id>", ...] }` to filter.
  - Response: `{ "users": [ { "discord_id": "...", "helix_id": "..." }, ... ] }`
## Notes
- Ensure Discord application redirect matches `DISCORD_REDIRECT_URI`.
- Provide strong `SECRET_KEY` and never expose raw API keys publicly.
- For large scale, add pagination + caching to `/api/users`.

## Credits
Made with 💞 by Dislike's Lab — https://discord.gg/ey8bMnBcZA

## License
MIT License