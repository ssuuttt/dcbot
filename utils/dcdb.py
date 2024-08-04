import sqlite3
import json


def creat_db():
    conn = sqlite3.connect('db/threads.db')
    c = conn.cursor()

    # Create the threads table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS threads (
            thread_id INTEGER PRIMARY KEY,
            thread_type INTEGER,
            thread_name TEXT,
            user_id INTEGER,
            channel_id INTEGER,
            message_id INTEGER,
            summary TEXT,
            breakdown TEXT
        )
    ''')
    conn.commit()




def select_and_clear_content():
    conn = sqlite3.connect('db/threads.db')
    c = conn.cursor()

    # Select all rows with thread_type = 9 and get their content
    c.execute("SELECT thread_id,content FROM threads WHERE thread_type = 9")
    rows = c.fetchall()

    # Clear the content of all selected rows
    # c.execute("UPDATE threads SET content = '' WHERE thread_type = 9")
    # conn.commit()

    # Close the database connection
    conn.close()

    return rows



def insert_thread_to_db(thread_id,thread_type, thread_name, message, summary="", debug=False):
    conn = sqlite3.connect('db/threads.db')
    c = conn.cursor()
    c.execute("INSERT INTO threads(thread_id, thread_type, thread_name,user_id, channel_id, message_id, summary, breakdown) VALUES (?, ?, ?, ?,?,?,?,?)",
                (thread_id, thread_type, thread_name, message.author.id, message.channel.id, message.id, summary, ""))
    if debug:
        print(f"insert_thread_to_db {thread_id} {thread_type} {thread_name} {message.author.id} {message.channel.id} {message.id} {summary}")
    conn.commit()


def update_breakdown_content(thread_id, breakdown, debug=False):
    conn = sqlite3.connect('db/threads.db')
    if debug:
        print(f"update_breakdown_content {thread_id} {breakdown}")
    c = conn.cursor()
    c.execute("UPDATE threads SET breakdown=? WHERE thread_id=?", (breakdown, thread_id))
    conn.commit()

def check_thread_in_db(channel_id, debug=False):
    conn = sqlite3.connect('db/threads.db')
    c = conn.cursor()
    if debug:
        print(f"check_thread_in_db {channel_id}")
    # Check if the thread is in the database
    c.execute("SELECT * FROM threads WHERE thread_id=?", (channel_id,))
    thread_info = c.fetchone()
    if debug:
        print(f"thread_info {thread_info}")
    return thread_info

def add_thread_to_db(message):
    conn = sqlite3.connect('db/threads.db')
    c = conn.cursor()
    c.execute("UPDATE threads SET message_id=? WHERE thread_id=?", (message.id, message.channel.id))
    conn.commit()


def export_db_to_json():
    # Connect to the SQLite database
    conn = sqlite3.connect('db/threads.db')
    c = conn.cursor()

    # Query the database
    c.execute("SELECT thread_name, summary, breakdown FROM threads WHERE thread_type = 1")
    rows = c.fetchall()

    # Prepare the data
    data = []
    for row in rows:
        data.append({
            "url": row[0],
            "summary": row[1],
            "breakdown": row[2]
        })

    # Write to JSON file
    with open('web/blog_data.json', 'w') as f:
        json.dump(data, f, indent=2)

    print("Data exported to blog_data.json")

    # Close the connection
    conn.close()