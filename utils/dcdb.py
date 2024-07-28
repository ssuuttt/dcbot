import sqlite3


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
            content TEXT
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



def insert_thread_to_db(thread_id,thread_type, thread_name, message, content="", debug=False):
    conn = sqlite3.connect('db/threads.db')
    c = conn.cursor()
    c.execute("INSERT INTO threads(thread_id, thread_type, thread_name,user_id, channel_id, message_id, content) VALUES (?, ?, ?, ?,?,?,?)",
                (thread_id, thread_type, thread_name, message.author.id, message.channel.id, message.id, content))
    if debug:
        print(f"insert_thread_to_db {thread_id} {thread_type} {thread_name} {message.author.id} {message.channel.id} {message.id} {content}")
    conn.commit()


def update_content(thread_id, content, debug=False):
    conn = sqlite3.connect('db/threads.db')
    c = conn.cursor()
    c.execute("UPDATE threads SET content=? WHERE thread_id=?", (thread_id, content))
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