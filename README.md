
# Kick API Client (Python)

A simple, reusable Python client for Kick.com's public API using OAuth2 + PKCE.

**Currently supports:**
- User authentication (user access tokens)
- Getting your own user info (`user:read`)
- Getting your own channel info (title, category, tags, slug…)
- Updating stream title, category, and custom tags

**Important:** This is **not** an official library — it's a community tool.

## Features

- Full OAuth2 Authorization Code flow with PKCE
- Automatic token refresh
- Persistent token storage (`kick_tokens.json` by default)
- Clean class-based API: `KickClient`
- Minimal dependencies (`requests`, `flask`)

## Installation

### Option 1: Editable install (recommended for development)

Clone the repo and install in editable mode:

```bash
git clone https://github.com/mardssss/kick-python-client.git
cd kick-python-client

# Install dependencies
pip install requests flask python-dotenv

# Install the package in editable mode
pip install -e .
```

Now you can import it from anywhere:

```python
from kick import KickClient
```

### Option 2: Copy the library folder into your project

Just copy the `kick/` folder into your project:

```
your-project/
├── kick/
│   ├── __init__.py
│   └── client.py
```

Then import like this:

```python
from kick import KickClient
```

### Option 3: Use as a git submodule or vendored dependency 

```bash
git submodule add https://github.com/mardssss/kick-python-client.git libs/kick
```

Then import:

```python
from libs.kick import KickClient
```

## Setup

1. Copy `.env.example` → `.env` and fill in your real values  
   **Never commit `.env` or `kick_tokens.json` to git!**

2. Install recommended helper (optional but very useful):

```bash
pip install python-dotenv
```

## Quick Start

```python
# bot.py
from kick import KickClient
from dotenv import load_dotenv
import os

load_dotenv()

client = KickClient(
    client_id=os.getenv("KICK_CLIENT_ID"),
    client_secret=os.getenv("KICK_CLIENT_SECRET"),
    redirect_uri=os.getenv("KICK_REDIRECT_URI", "http://localhost:8080/callback"),
    token_file=os.getenv("KICK_TOKEN_FILE", "kick_tokens.json"),
)

# Authenticate (opens browser only first time or when expired)
client.get_access_token(scopes="user:read channel:read channel:write")

# Get user info
user = client.get_user()
if user:
    print(f"Logged in as: {user.get('name')} (ID: {user.get('user_id')})")

# Get current channel info
channel = client.get_channel()
if channel:
    print("\nCurrent stream info:")
    print(f"  Title:      {channel.get('stream_title', 'Not set')}")
    print(f"  Category:   {channel.get('category_id', 'N/A')}")
    print(f"  Tags:       {', '.join(channel.get('custom_tags', [])) or 'none'}")
    print(f"  Slug:       {channel.get('slug', 'N/A')}")

# Update stream (works even when offline)
client.update_channel(
    title="LIVE | Testing my Python bot",
    custom_tags="python,bot,development"
)
print("Stream settings updated!")
```

## Development / Contributing

Install dev tools:

```bash
pip install ruff pytest pre-commit python-dotenv
```

Run checks:

```bash
ruff check .
pytest
```

Feel free to open issues or pull requests!

## Current limitations

- Only **user tokens** (no app/client-credentials flow yet)
- Chat sending & moderation not implemented
- No webhook / events support
- No rate limiting or advanced retry logic

## Planned features

- Chat sending (`chat:write`)
- Moderation commands (timeout, ban, delete message)
- Stream key retrieval (`streamkey:read`)
- Better error handling & custom exceptions
- Async support (aiohttp)

## License

MIT License

See [LICENSE](LICENSE) for full text.