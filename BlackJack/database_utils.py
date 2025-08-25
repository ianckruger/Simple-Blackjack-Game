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

    # H is horizontal, v is vertical
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

    # rounds stats
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            player_id TEXT NOT NULL,
            bet INTEGER NOT NULL,
            outcome TEXT NOT NULL,   -- 'win','lose','push','blackjack'
            delta INTEGER NOT NULL,  -- net chips change
            player_total INTEGER,
            dealer_total INTEGER,
            notes TEXT
        );
    """)

    # Seed themes if empty
    cursor.execute("SELECT COUNT(*) FROM themes;")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO themes(name, spade, heart, diamond, club, top_left, top_right, bottom_left, bottom_right, h, v)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """, [
            ("unicode", "♠", "♥", "♦", "♣", "┌", "┐", "└", "┘", "─", "│"),
            ("ascii",   "^", "v", "<>", "()", "+", "+", "+", "+", "-", "|"),
        ])

    # Seed templates if empty
    cursor.execute("SELECT COUNT(*) FROM card_templates;")
    if cursor.fetchone()[0] == 0:
        face_up = dedent("""\
            {tl}{h}{h}{h}{h}{h}{h}{h}{h}{h}{tr}
            {v}{rank_l}       {v}
            {v}         {v}
            {v}    {suit}    {v}
            {v}         {v}
            {v}         {v}
            {v}       {rank_r}{v}
            {bl}{h}{h}{h}{h}{h}{h}{h}{h}{h}{br}
        """)
        face_down = dedent("""\
            {tl}{h}{h}{h}{h}{h}{h}{h}{h}{h}{tr}
            {v}░░░░░░░░░{v}
            {v}░░░░░░░░░{v}
            {v}░ H I D ░{v}
            {v}░ D E N ░{v}
            {v}░░░░░░░░░{v}
            {v}░░░░░░░░░{v}
            {bl}{h}{h}{h}{h}{h}{h}{h}{h}{h}{br}
        """)
        cursor.executemany(
            "INSERT INTO card_templates(name, template) VALUES(?,?)",
            [("face_up", face_up), ("face_down", face_down)]
        )

    # Ensure default active theme is set
    cursor.execute("INSERT OR IGNORE INTO settings(key, value) VALUES('active_theme', 'unicode');")

    connect.commit()
    connect.close()


# ----- Settings & Theme helpers -----

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
    # FIX: table name 'settings'
    cursor.execute("SELECT value FROM settings WHERE key='active_theme'")
    row = cursor.fetchone()
    if not row:
        connect.close()
        raise RuntimeError("No active_theme set in settings")
    themeName = row[0]

    cursor.execute("""
        SELECT name, spade, heart, diamond, club,
               top_left, top_right, bottom_left, bottom_right, h, v
        FROM themes WHERE name=?
    """, (themeName,))
    row = cursor.fetchone()
    connect.close()
    if not row:
        raise RuntimeError(f"Active theme '{themeName}' not found in themes")
    keys = ["name","spade","heart","diamond","club","tl","tr","bl","br","h","v"]
    return dict(zip(keys, row))


# ----- Template loader & render -----

def _loadTemplate(name, path=DB_PATH):
    connect = sqlite3.connect(path)
    cursor = connect.cursor()
    cursor.execute("SELECT template FROM card_templates WHERE name=?", (name,))
    row = cursor.fetchone()
    connect.close()
    if not row:
        raise ValueError(f"Template '{name}' not found")
    return row[0]

def renderCard(rank, suit, hidden=False, path=DB_PATH):
    """
    rank: 'A','2'..'10','J','Q','K'
    suit: 'S','H','D','C'
    """
    theme = getActiveTheme(path)
    tmpl = _loadTemplate("face_down" if hidden else "face_up", path)

    suit_char = {
        "S": theme["spade"],
        "H": theme["heart"],
        "D": theme["diamond"],
        "C": theme["club"],
    }[suit]

    rank_l = rank.ljust(2)  # handles '10'
    rank_r = rank.rjust(2)

    out = tmpl.format(
        rank_l=rank_l,
        rank_r=rank_r,
        suit=suit_char,
        tl=theme["tl"], tr=theme["tr"], bl=theme["bl"], br=theme["br"],
        h=theme["h"], v=theme["v"],
    )
    return out.splitlines()

def renderHand(cards, hideFirst=False, path=DB_PATH):
    """
    cards: list of (rank, suit) e.g. [('A','S'), ('10','H')]
    return a single string with cards side by side
    """
    blocks = [
        renderCard(r, s, hidden=(hideFirst and i == 0), path=path)
        for i, (r, s) in enumerate(cards)
    ]
    lines = []
    rows = len(blocks[0])
    for row in range(rows):
        lines.append("  ".join(block[row] for block in blocks))
    return "\n".join(lines)


# ----- Stats: record & query -----

def recordRound(playerID, bet, outcome, delta, playerTotal=None, dealerTotal=None, notes=None, path=DB_PATH):
    """
    outcome: 'win','lose','push','blackjack'
    delta: net chip change
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
    averageBet = (total_bet / games) if games else 0.0

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
