from flask import Flask, request, jsonify
from flask_cors import CORS 
import mysql.connector
import random

app = Flask(__name__)
CORS(app) 

# 1. Database Connection (Move this UP)
# Change host to "localhost" if you are not using Docker right now
try:
    conn = mysql.connector.connect(
        host="localhost", 
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

@app.route("/start", methods=["POST"]) # Changed to match your script.js
def new_game():
    global board, current_player, players
    data = request.json
    username = data.get("username", "Guest")

    cursor = conn.cursor()
    try:
        cursor.execute("INSERT IGNORE INTO players (username) VALUES (%s)", (username,))
        conn.commit()
    except Exception as e:
        print(f"DB Error: {e}")

    players = [username]
    board = [""] * 9
    current_player = "X"
    return jsonify({"message": "New game started", "board": board})

@app.route("/move", methods=["POST"])
def move():
    global board, current_player
    data = request.json
    pos = data.get("position")
    username = data.get("username")

    if board[pos] == "":
        board[pos] = current_player
        winner = check_winner()
        if winner:
            update_stats(username, "win")
        current_player = "O" if current_player == "X" else "X"
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
