from flask import Flask, request, jsonify
from flask_cors import CORS 
import time
import mysql.connector
import random
import os

app = Flask(__name__)
CORS(app) 

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "root")
DB_NAME = os.environ.get("DB_NAME", "tic-tac-db")

def get_db_connection():
    while True:
        try:
            connection = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                autocommit=True
            )
            print("Successfully connected to the database!")
            return connection
        except Exception as e:
            print(f"Database not ready... {e}. Retrying in 2 seconds.")
            time.sleep(2)

# Initial connection
conn = get_db_connection()

def get_db():
    global conn
    try:
        if conn is None or not conn.is_connected():
            conn = get_db_connection()
        else:
            conn.ping(reconnect=True, attempts=2, delay=1)
    except Exception:
        conn = get_db_connection()
    return conn

# Global Variables
board = [""] * 9
current_player = "X"
players = ["Guest 1", "Guest 2"]

def check_winner():
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a,b,c in wins:
        if board[a] == board[b] == board[c] != "":
            return board[a]
    if "" not in board:
        return "Draw"
    return None

def update_stats(username, result):
    try:
        db = get_db()
        cursor = db.cursor()
        if result == "win":
            cursor.execute("UPDATE players SET wins = wins + 1 WHERE username=%s", (username,))
        elif result == "loss":
            cursor.execute("UPDATE players SET losses = losses + 1 WHERE username=%s", (username,))
        elif result == "draw":
            cursor.execute("UPDATE players SET draws = draws + 1 WHERE username=%s", (username,))
        db.commit()
    except Exception as e:
        print(f"Error updating stats for {username}: {e}")

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Online", "message": "Tic Tac Toe API"}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route("/start", methods=["POST"])
def new_game():
    global board, current_player, players
    data = request.json or {}
    mode = data.get("mode", "pvp")
    player1 = str(data.get("player1", "Guest 1")).strip() or "Guest 1"
    player2 = "Bot" if mode == "bot" else (str(data.get("player2", "Guest 2")).strip() or "Guest 2")
    confirm = data.get("confirm", False)
    confirm2 = data.get("confirm2", False)

    try:
        db = get_db()
        cursor = db.cursor()
        # Check if player1 already exists
        cursor.execute("SELECT 1 FROM players WHERE username = %s", (player1,))
        exists = cursor.fetchone() is not None
        if exists and not confirm:
            return jsonify({
                "exists": True,
                "message": f"Username '{player1}' already exists. Are you this user?",
                "prompt": "confirm"
            }), 200

        if mode == "pvp":
            cursor.execute("SELECT 1 FROM players WHERE username = %s", (player2,))
            exists2 = cursor.fetchone() is not None
            if exists2 and not confirm2:
                return jsonify({
                    "exists": True,
                    "message": f"Username '{player2}' already exists. Are you this user?",
                    "prompt": "confirm2"
                }), 200

        cursor.execute("INSERT IGNORE INTO players (username) VALUES (%s)", (player1,))
        if mode == "pvp":
            cursor.execute("INSERT IGNORE INTO players (username) VALUES (%s)", (player2,))
        db.commit()
    except Exception as e:
        print(f"DB Error: {e}")

    players = [player1, player2]
    board = [""] * 9
    current_player = "X"
    return jsonify({
        "message": "New game started",
        "board": board,
        "players": players,
        "current_player": current_player
    })

@app.route("/check_username/<username>", methods=["GET"])
def check_username(username):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1 FROM players WHERE username = %s", (username,))
        result = cursor.fetchone()
        return jsonify({"exists": bool(result)})
    except Exception as e:
        print(f"Check Username DB Error: {e}")
        return jsonify({"exists": False, "error": str(e)}), 500

@app.route("/move", methods=["POST"])
def move():
    global board, current_player, players
    data = request.json or {}
    pos = data.get("position")

    if pos is None or not isinstance(pos, int) or pos < 0 or pos > 8:
        return jsonify({"error": "Invalid position"}), 400

    if len(players) < 2:
        players = ["Player 1", "Player 2"]

    existing_winner = check_winner()
    if existing_winner:
        return jsonify({
            "board": board,
            "winner": existing_winner,
            "next": current_player,
            "players": players,
            "message": "Game already ended"
        })

    if board[pos] == "":
        board[pos] = current_player
        winner = check_winner()
        
        # Determine winning/losing players
        if winner and winner != "Draw":
            winning_username = players[0] if current_player == "X" else players[1]
            losing_username = players[1] if current_player == "X" else players[0]
            if winning_username != "Bot":
                update_stats(winning_username, "win")
            if losing_username != "Bot":
                update_stats(losing_username, "loss")
        elif winner == "Draw":
            if players[0] != "Bot":
                update_stats(players[0], "draw")
            if players[1] != "Bot":
                update_stats(players[1], "draw")

        current_player = "O" if current_player == "X" else "X"
        
        # Bot move if bot mode is active, it's O's turn, game not over, and empty spaces exist
        if players[1] == "Bot" and current_player == "O" and not winner and "" in board:
            available = [i for i, cell in enumerate(board) if cell == ""]
            if available:
                bot_move = random.choice(available)
                board[bot_move] = "O"
                winner = check_winner()
                if winner == "O":
                    if players[0] != "Bot":
                        update_stats(players[0], "loss")
                elif winner == "Draw":
                    if players[0] != "Bot":
                        update_stats(players[0], "draw")
                current_player = "X"
                
        return jsonify({
            "board": board,
            "winner": winner,
            "next": current_player,
            "players": players
        })
    return jsonify({"error": "Invalid move"}), 400

@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT username, wins, losses, draws FROM players ORDER BY wins DESC, draws DESC, id ASC")
        return jsonify(cursor.fetchall())
    except Exception as e:
        print(f"Leaderboard DB Error: {e}")
        return jsonify([])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
