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
    
    # H is like the horizontal sides of the cards, v is the vertical
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
        


# Denoting functions now ( Setters/Getters and Theme helpers )

def setActiveTheme(name, path=DB_PATH):
    connect = sqlite3.connect(path)
    cursor = connect.cursor()
    cursor.execute("SELECT 1 FROM themes WHERE name=?", (name,))
    if not cursor.fetchone():
        connect.close()
        raise ValueError(f"Theme '{name}' does not exist")
    cursor.execute("REPLACE INTO settings(key, value) VALUES('active_theme', ?)", (name,))
    connect.commit()
    connect.close()

def getActiveTheme(path=DB_PATH):
    connect = sqlite3.connect(path)
    cursor = connect.cursor()
    cursor.execute("SELECT value FROM setting WHERE key='active_theme'")
    themeName = cursor.fetchone()[0]
    cursor.execute("""
            SELECT name, spade, heart, diamond, club, top_left, top_right, bottom_left, bottom_right, h, v
            FROM themes WHERE name=?
                   """, (themeName,))
    row = cursor.fetchone()
    connect.close()
    if not row:
        raise RuntimeError("Active theme not found")
    keys = ["name","spade","heart","diamond","club","tl","tr","bl","br","h","v"]
    return dict(zip(keys, row))

# Load and Render Template Functions
def _loadTemplate(name, path=DB_PATH):
    connect = sqlite3.connect(path)
    cursor = connect.cursor()
    cursor.execute("SELECT template FROM card_templates WHERE name=?", (name,))
    row = cursor.fetchone()
    connect.close()
    if not row:
        raise ValueError(f"Template '{name}' not found")
    return row[0]

# Rank --> value of the card, suit --> spade, heart, diamond, club
def renderCard(rank, suit, hidden=False, path=DB_PATH):
    """
    rank: 'A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'
    suit: 'S', 'H', 'D', 'C'
    """
    theme = getActiveTheme(path)
    if hidden:
        tmpl = _loadTemplate("face_down", path)
    else:
        tmpl = _loadTemplate("face_up", path)

    suit_char = {
        "S": theme["spade"],
        "H": theme["heart"],
        "D": theme["diamond"],
        "C": theme["club"],
    }[suit]

    rank_l = rank.ljust(2)
    rank_r = rank.rjust(2)

    out = tmpl.format(
        rank_l=rank_l,
        rank_r=rank_r,
        suit=suit_char,
        tl=theme["tl"], tr=theme["tr"], bl=theme["bl"], br=theme["br"],
        h=theme["h"], v=theme["v"]
    )
    return out.splitlines()

def renderHand(cards, hideFirst=False, path=DB_PATH):
    """
    cards: list of (rank, suit) e.g. [('A', 'S'), ('10', 'H')]
    return a single string with cards "side by side"
    """

    blocks = [
        renderCard(r,s,hidden=(hideFirst and i == 0), path=path)
        for i, (r,s) in enumerate(cards)
    ]
    lines = []
    rows = len(blocks[0])
    for row in range(rows):
        lines.append("  ".join(block[row] for block in blocks))
    return "\n".join(lines)


# For stats; Record and Query

def record_round(playerID, bet, outcome, delta, playerTotal=None, dealerTotal=None, notes=None, path=DB_PATH):
    """
    outcome: 'win', 'lose', 'push', 'blackjack'
    delta: net chip change (e.g., +10 for win, -10 for lose, +15 for blackjack if 3:2 on 10 bet, etc.)
    """
    connect = sqlite3.connect(path)
    cursor = connect.cursor()
    cursor.execute("""
        INSERT INTO rounds(ts, player_id, bet, outcome, delta, player_total, dealer_total, notes)
        VALUES(?,?,?,?,?,?,?,?)
    """, (
        datetime.utcnow().isoformat(timespec="seconds") + "Z",
        playerID, bet, outcome, delta, playerTotal, dealerTotal, notes
    ))
    connect.commit()
    connect.close()

# return dict of stats (saves over time)
def getPlayerStats(playerID, path=DB_PATH):
    connect = sqlite3.connect(path)
    cursor = connect.cursor()

    cursor.execute("SELECT COUNT(*), COALESCE(SUM(bet),0), COALESCE(SUM(delta),0) FROM rounds WHERE player_id=?", (playerID,))
    games, total_bet, net = cursor.fetchone()

    cursor.execute("""
        SELECT outcome, COUNT(*)
        FROM rounds
        WHERE player_id=?
        GROUP BY outcome
    """, (playerID,))
    counts = dict(cursor.fetchall())
    wins = counts.get("win", 0) + counts.get("blackjack", 0)
    losses = counts.get("lose", 0)
    pushes = counts.get("push", 0)
    blackjacks = counts.get("blackjack", 0)
    winRate = (wins / games) if games else 0.0
    averageBet = (total_bet / games ) if games else 0.0

    connect.close()
    return {
        "games": games,
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "blackjacks": blackjacks,
        "win_rate": round(winRate, 3),
        "avg_bet": round(averageBet, 2),
        "net": net,
        "total_bet": total_bet,
    }
    