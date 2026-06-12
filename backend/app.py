from flask import Flask, request, jsonify
from flask_cors import CORS 
import time
import mysql.connector
import random

app = Flask(__name__)
CORS(app) 

import os

# 1. Database Connection (Move this UP)
# Change host to "localhost" if you are not using Docker right now
DB_HOST = os.environ.get("DB_HOST", "localhost")

def get_db_connection():
    while True:
        try:
            connection = mysql.connector.connect(
                host=DB_HOST,
                user="root",
                password="root",
                database="tic-tac-db",
                autocommit=True
            )
            print("Successfully connected to the database!")
            return connection
        except Exception as e:
            print(f"Database not ready... {e}. Retrying in 2 seconds.")
            time.sleep(2)

# Establish initial connection
conn = get_db_connection()

try:
    conn = mysql.connector.connect(
        host=DB_HOST, 
        user="root",
        password="root",
        database="tic-tac-db"
    )
except Exception as e:
    print(f"Error connecting to DB: {e}")

# 2. Global Variables
board = [""] * 9
current_player = "X"
players = []

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Online", "message": "Tic Tac Toe API"}), 200

@app.route("/start", methods=["POST"])
def new_game():
    global board, current_player, players
    data = request.json
    mode = data.get("mode", "pvp")
    player1 = data.get("player1", "Guest 1")
    player2 = data.get("player2", "Bot") if mode == "bot" else data.get("player2", "Guest 2")
    # Optional flag from client indicating user confirmed existing username
    confirm = data.get("confirm", False)

    cursor = conn.cursor()
    # Check if player1 already exists
    cursor.execute("SELECT 1 FROM players WHERE username = %s", (player1,))
    exists = cursor.fetchone() is not None
    if exists and not confirm:
        # Prompt client to confirm identity
        return jsonify({
            "exists": True,
            "message": f"Username '{player1}' already exists. Are you this user?",
            "prompt": "confirm"
        }), 200
    # Insert or ignore player records
    # If player2 exists (in pvp mode), handle confirmation similarly
    if mode == "pvp":
        cursor.execute("SELECT 1 FROM players WHERE username = %s", (player2,))
        exists2 = cursor.fetchone() is not None
        confirm2 = data.get("confirm2", False)
        if exists2 and not confirm2:
            return jsonify({
                "exists": True,
                "message": f"Username '{player2}' already exists. Are you this user?",
                "prompt": "confirm2"
            }), 200
    try:
        cursor.execute("INSERT IGNORE INTO players (username) VALUES (%s)", (player1,))
        if mode == "pvp":
            cursor.execute("INSERT IGNORE INTO players (username) VALUES (%s)", (player2,))
        conn.commit()
    except Exception as e:
        print(f"DB Error: {e}")

    players = [player1, player2]
    board = [""] * 9
    current_player = "X"
    return jsonify({"message": "New game started", "board": board})

@app.route("/check_username/<username>", methods=["GET"])
def check_username(username):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM players WHERE username = %s", (username,))
        result = cursor.fetchone()
        return jsonify({"exists": bool(result)})
    except Exception as e:
        print(f"Check Username DB Error: {e}")
        return jsonify({"exists": False, "error": str(e)}), 500

@app.route("/move", methods=["POST"])
def move():
    global board, current_player, players
    data = request.json
    pos = data.get("position")

    if board[pos] == "":
        board[pos] = current_player
        winner = check_winner()
        
        # Determine the username of the winning player
        winning_username = players[0] if current_player == "X" else players[1]
        
        if winner:
            if winning_username != "Bot":
                update_stats(winning_username, "win")
                
        current_player = "O" if current_player == "X" else "X"
        
        # Extremely basic bot implementation if bot mode is active and it's O's turn
        if players[1] == "Bot" and current_player == "O" and not winner and "" in board:
            available = [i for i, cell in enumerate(board) if cell == ""]
            if available:
                bot_move = random.choice(available)
                board[bot_move] = "O"
                winner = check_winner()
                if winner: # Bot wins, no stats update needed
                    pass
                current_player = "X"
                
        return jsonify({"board": board, "winner": winner, "next": current_player})
    return jsonify({"error": "Invalid move"}), 400

@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT username, wins FROM players ORDER BY wins DESC")
        return jsonify(cursor.fetchall())
    except Exception as e:
        return jsonify([])

def check_winner():
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a,b,c in wins:
        if board[a] == board[b] == board[c] != "":
            return board[a]
    return None

def update_stats(username, result):
    cursor = conn.cursor()
    if result == "win":
        cursor.execute("UPDATE players SET wins = wins + 1 WHERE username=%s", (username,))
    conn.commit()

# 3. THE SERVER START (MUST BE AT THE VERY BOTTOM)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
