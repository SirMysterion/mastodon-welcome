import argparse
from mastodon import Mastodon
import sqlite3
import tomllib

ACCOUNT_FETCH_LIMIT = 100000

def check_db_exists(cursor: sqlite3.Cursor) -> bool:
    res = cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='welcome_log'")
    if res.fetchone()[0] == 0:
        cursor.execute("CREATE TABLE welcome_log (id INTEGER PRIMARY KEY, username TEXT, userdb_id INTEGER, welcomed INTEGER DEFAULT 0)")
        return False
    return True

def user_exists(cursor: sqlite3.Cursor, userid: int) -> bool:
    res = cursor.execute("SELECT COUNT(*) FROM welcome_log WHERE userdb_id = ?", (userid,))
    return res.fetchone()[0] > 0

def user_welcomed(cursor: sqlite3.Cursor, userid: int) -> bool:
    res = cursor.execute("SELECT COUNT(*) FROM welcome_log WHERE userdb_id = ? AND welcomed = 1", (userid,))
    return res.fetchone()[0] > 0

def set_user_welcomed(cursor: sqlite3.Cursor, userid: int):
    cursor.execute("UPDATE welcome_log SET welcomed = 1 WHERE userdb_id = ?", (userid, ))

def create_user(cursor: sqlite3.Cursor, userid: int, username: str):
    cursor.execute("INSERT INTO welcome_log (userdb_id, username) VALUES(?, ?)", (userid, username))


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description = "Welcomes users to the Mastodon instance",
        epilog = "Note: the user this bot logs in as must have admin:read:accounts access"
    )
    arg_parser.add_argument('--config', default="config.toml")
    args = arg_parser.parse_args()

    config = None
    with open(args.config, "rb") as toml_file:
        config = tomllib.load(toml_file)

    print(f"Connecting to {config['mastodon']['base_url']}...")

    mastodon = Mastodon(
        access_token = config['mastodon']['access_token'],
        api_base_url = config['mastodon']['base_url']
    )

    visibility = config['mastodon'].get('visibility', 'unlisted')
    print(f"Visibility mode: {visibility}")

    connection = sqlite3.connect(config['database']['sqlite_path'])
    cursor = connection.cursor()
    
    fresh_database = not check_db_exists(cursor) 
    if fresh_database:
        print("Database initialized - marking existing users as welcomed")

    print("Fetching accounts...")
    all_accounts = mastodon.admin_accounts(remote=False, status='active', limit=ACCOUNT_FETCH_LIMIT)
    
    accounts_total = len(all_accounts)
    users_welcomed = 0
    users_added = 0

    for account in all_accounts:
        if not (account.confirmed and account.approved) or account.disabled or account.suspended or account.silenced:
            continue
        
        if not user_exists(cursor, account.id):
            create_user(cursor, account.id, account.username)
            connection.commit()
            users_added += 1
        
        if fresh_database:
            set_user_welcomed(cursor, account.id)
            connection.commit()
        
        elif not user_welcomed(cursor, account.id):
            print(f"Welcoming @{account.username}...")
            
            result_id = None
            for message in config['messages']:
                content_warning = message['content_warning'] if 'content_warning' in message else None
                result = mastodon.status_post(status=f"@{account.username}, {message['content']}", in_reply_to_id=result_id, visibility=visibility, spoiler_text=content_warning)
                result_id = result.id
            
            set_user_welcomed(cursor, account.id)
            connection.commit()
            users_welcomed += 1
            print(f"  ✓ Welcome sent to @{account.username}")

    print(f"\nSummary:")
    print(f"  Accounts processed: {accounts_total}")
    print(f"  New users added: {users_added}")
    print(f"  Welcome messages sent: {users_welcomed}")