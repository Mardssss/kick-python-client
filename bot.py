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