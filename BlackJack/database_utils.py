import sqlite3
from textwrap import dedent
from datetime import datetime

DB_PATH = "blackjack.db"

def init_db(path=DB_PATH):
    connect = sqlite3.connect(path)
    cursor = connect.cursor()

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                   key TEXT PRIMARY KEY,
                   value TEXT NOT NULL
                   );
                   """)
    
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS themes (
                   name TEXT PRIMARY KEY,
                   spade TEXT NOT NULL,
                   heart TEXT NOT NULL,
                   diamond TEXT NOT NULL,
                   club TEXT NOT NULL,
                   top_left TEXT NOT NULL,
                   top_right TEXT NOT NULL,
                   bottom_left TEXT NOT NULL,
                   bottom_right TEXT NOT NULL,
                   h TEXT NOT NULL,
                   v TEXT NOT NULL
                   );
                   """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS card_templates (
                   name TEXT PRIMARY KEY,
                   template TEXT NOT NULL
                   );
                   """)
    
    # Creating a statistics table (just to track wins, losses, perfect hits, etc)
    # Outcome = win, loss, push, blackjack
    # Delta is the net cash won/loss (if bets are to be implemented)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS rounds (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   ts TEXT NOT NULL,
                   player_id TEXT NOT NULL,
                   bet INTEGER NOT NULL,
                   outcome TEXT NOT NULL,
                   delte INTEGER NOT NULL,
                   player_total INTEGER,
                   dealer_total INTEGER,
                   notes TEXT
                   );
                   """)
    

    # Default theming, provide a unicode for cuter objects as well as a fallback ascii
    cursor.execute("SELECT COUNT(*) FROM themes;")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
                    INSERT INTO themes(name, spade, heart, diamond, club, top_left, top_right, bottom_left, bottom_right, h, v)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """, [
                        ("unicode", "♠", "♥", "♦", "♣", "┌", "┐", "└", "┘", "─", "│"),
                        ("ascii",  "^", "v", "<>", "()", "+", "+", "+", "+", "-", "|"),
                    ])
        

    cursor.execute("SELECT COUNT(*) FROM card_templates;")
    if cursor.fetchone()[0] == 0:
        face_up = dedent("""\
        {tl}{h}{h}{h}{h}{h}{h}{h}{h}{tr}
        {v}{rank_1}       {v}
        {v}         {v}
        {v}    {suit}    {v}
        {v}         {v}
        {v}         {v}
        {v}       {rank_r}{v}
        {bl}{h}{h}{h}{h}{h}{h}{h}{h}{br}""")
        face_down = dedent("""\
            {tl}{h}{h}{h}{h}{h}{h}{h}{h}{tr}
            {v}░░░░░░░░░{v}
            {v}░░░░░░░░░{v}
            {v}░ H I D ░{v}
            {v}░ D E N ░{v}
            {v}░░░░░░░░░{v}
            {v}░░░░░░░░░{v}
            {bl}{h}{h}{h}{h}{h}{h}{h}{h}{br}
        """)

        cursor.executemany("""
            INSERT INTO card_templates(name, template) VALUES(?,?)
            """,[
                ("face_up", face_up),
                ("face_down", face_down),
            ])