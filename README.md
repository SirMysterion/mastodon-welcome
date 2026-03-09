# mastodon-welcome

A simple bot that welcomes new users to a Mastodon instance.

## Setup

1. Create a bot account on your Mastodon instance with admin privileges
2. Generate an access token:
   - Go to **Preferences → Development → New application**
   - Give it a name (e.g., "welcome-bot")
   - Select scopes: `write:statuses` and `admin:read:accounts`
   - Click **Create**
   - Click on the application and copy the **Access token**
3. Copy `config.example.toml` to `config.toml`
4. Edit `config.toml`:
   - Set `base_url` to your instance URL
   - Set `access_token` to the token you copied
   - Customize your welcome messages

## Usage with Docker

```bash
# Build
docker compose build

# Run
docker compose run --rm mastodon-welcome
```

## Configuration

```toml
[mastodon]
base_url = "https://your-instance.social"
access_token = "your_access_token_here"
# Visibility: public, unlisted, private, direct (default: unlisted)
visibility = "unlisted"

[database]
sqlite_path = "/data/database.db"

[[messages]]
content = """
Welcome to our instance!
"""
```

### Visibility Options

- `public` - Posts appear in local/public timelines (everyone sees new member announcements)
- `unlisted` - Visible publicly but not in timelines (default)
- `private` - Followers only
- `direct` - Mentioned accounts only

### Content Warnings

Add `content_warning` to any message:

```toml
[[messages]]
content = "Your message here"
content_warning = "Content warning text"
```

## Notes

- The bot account must have `admin:read:accounts` scope
- On first run, existing users are marked as already welcomed
- The database tracks which users have been welcomed