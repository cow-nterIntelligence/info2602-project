"""
Migration script: Add 'status' column to the friend table.

Run this once before starting the app after the friend model update.
Usage (from project root):
    python migrate_friend_status.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "test.db")

def run():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(friend)")
    columns = [row[1] for row in cursor.fetchall()]

    if "status" not in columns:
        print("Adding 'status' column to 'friend' table...")
        cursor.execute("ALTER TABLE friend ADD COLUMN status TEXT NOT NULL DEFAULT 'accepted'")
        # Existing rows are treated as already-accepted friendships
        cursor.execute("UPDATE friend SET status = 'accepted'")
        conn.commit()
        print("Migration complete. Existing friendships marked as 'accepted'.")
    else:
        print("'status' column already exists — nothing to do.")

    conn.close()

if __name__ == "__main__":
    run()
