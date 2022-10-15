import sqlite3

DB_PATH = './data/db/DudelBotData.db'

def get_event_info(event_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute("SELECT * FROM events WHERE event_id=?", (int(event_id),)).fetchone()
    con.close()

    return result

def get_guild_channel_id(guild_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute("SELECT channel_id FROM guild_channel_id WHERE guild_id=?", (int(guild_id),)).fetchone()
    con.close()

    return result

def fetch_distinct_player_signup_events(player_id, guild_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute(
        """SELECT * FROM events 
        NATURAL JOIN signups 
        WHERE signups.player_id=? AND events.guild_id=?
        GROUP BY event_id 
        ORDER BY events.unix_timestamp ASC""",
        (int(player_id), int(guild_id))
    ).fetchall()
    con.close()

    return result

def fetch_events():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute("SELECT * FROM events").fetchall()
    con.close()

    return result

def fetch_event_ids():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute("SELECT event_id FROM events").fetchall()
    con.close()

    return result

def fetch_event_role_signup_info(event_id, role):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute("SELECT * FROM signups WHERE event_id=? AND role=?", (int(event_id), role)).fetchall()
    con.close()
    
    return result

def fetch_event_signup_distinct_player_ids(event_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute("SELECT DISTINCT player_id FROM signups WHERE event_id=?", (int(event_id),)).fetchall()
    con.close()

    return result

def fetch_event_signup_info(event_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute("SELECT * FROM signups WHERE event_id=?", (int(event_id),)).fetchall()
    con.close()
    
    return result

def fetch_guild_channel_ids():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute("SELECT * FROM guild_channel_id").fetchall()
    con.close()

    return result

def fetch_scheduled_event_ids():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute("SELECT scheduled_event_id FROM events").fetchall()
    con.close()

    return result

def set_db_event_timestamp(event_id, timestamp):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("UPDATE events SET unix_timestamp=? WHERE event_id=?", (timestamp, int(event_id)))
    con.commit()
    con.close()

def set_db_event_title(event_id, title):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("UPDATE events SET title=? WHERE event_id=?", (title, int(event_id)))
    con.commit()
    con.close()
    
def set_no_auto_delete(event_id, value):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("UPDATE events SET no_auto_delete=? WHERE event_id=?", (value, int(event_id)))
    con.commit()
    con.close()

def insert_event(event_id, user_name, user_id, unix_timestamp, title, guild_id, schdl_event_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "INSERT INTO events VALUES (?, ?, ?, ?, ?, NULL, NULL, ?, NULL, ?)", 
        (int(event_id), user_name, user_id, unix_timestamp, title, guild_id, schdl_event_id)
    )
    con.commit()
    con.close()

def insert_event_limits(event_id, dps_limit, support_limit):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        """UPDATE events 
        SET dps_limit=?, support_limit=?
        WHERE event_id=?""", 
        (dps_limit, support_limit, event_id)
    )
    con.commit()
    con.close()

def insert_event_signup(event_id, user_name, user_id, role, timestamp):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        'INSERT INTO signups VALUES(?, ?, ?, ?, ?)',
        (int(event_id), user_name, user_id, role, timestamp)
        )
    con.commit()
    con.close()

def delete_event_by_id(event_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("DELETE FROM events WHERE event_id=?",(int(event_id),))
    con.commit()
    con.close()

def delete_latest_n_role_signups(event_id, role, n):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute(
        """SELECT player_name, player_id, signup_timestamp 
        FROM signups 
        WHERE event_id=? AND role=?
        ORDER BY signup_timestamp DESC 
        LIMIT ?""",
        (event_id, role, n)
    ).fetchall()
    cur.execute(
        """DELETE FROM signups 
        WHERE event_id=? AND role=? 
        AND player_id IN (
            SELECT player_id 
            FROM signups 
            WHERE event_id=? AND role=?
            ORDER BY signup_timestamp DESC 
            LIMIT ?
            )""",
        (event_id, role, event_id, role, n)
    )
    con.commit()
    con.close()

    return result

def delete_user_from_signups(event_id, user_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "DELETE FROM signups WHERE event_id=? AND player_id=?",
        (int(event_id), user_id)
        )
    con.commit()
    con.close()

def is_signed_up_role(event_id, player_id, role):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    result = cur.execute((
        "SELECT * FROM signups "
        "WHERE event_id=? AND player_id=? AND role=?"
        ),
        (int(event_id), int(player_id), role)
    ).fetchone()
    con.close()

    return result