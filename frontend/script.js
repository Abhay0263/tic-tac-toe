const boardDiv = document.getElementById("board");
const dashboardDiv = document.getElementById("dashboard");
const gameDiv = document.getElementById("game");
const statusDisplay = document.getElementById("status-display");

let currentUser = "Abhay Rana";
let botMode = false;

window.onload = () => {
  console.log("Page loaded, fetching leaderboard...");
  updateLeaderboard();
};

function updateLeaderboard() {
  fetch("http://localhost:5000/leaderboard")
    .then(res => res.json())
    .then(data => {
      const list = document.getElementById("leaderboard-list");
      if (list) {
        if (data.length === 0) {
            list.innerHTML = "<li>No stats yet</li>";
        } else {
            list.innerHTML = data.map(p =>
              `<li><span>${p.username}</span> <span>${p.wins} Wins</span></li>`
            ).join("");
        }
      }
    })
    .catch((err) => {
      console.error("Leaderboard fetch failed:", err);
      document.getElementById("leaderboard-list").innerHTML = "<li>Server Offline</li>";
    });
}

async function startNewGame() {
  console.log("Starting new game...");
  botMode = false;
  try {
    const res = await fetch("http://localhost:5000/start", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ username: currentUser, mode: "pvp" })
    });
    const data = await res.json();
    renderBoard(data.board);
    dashboardDiv.style.display = "none";
    gameDiv.style.display = "block";
  } catch (err) {
    console.error("Could not start game:", err);
  }
}

async function playWithBot() {
  console.log("Starting bot game...");
  botMode = true;
  try {
    const res = await fetch("http://localhost:5000/start", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ username: currentUser, mode: "bot" })
    });
    const data = await res.json();
    renderBoard(data.board);
    dashboardDiv.style.display = "none";
    gameDiv.style.display = "block";
  } catch (err) {
    console.error("Could not start bot game:", err);
  }
}

function renderBoard(board) {
  boardDiv.innerHTML = "";
  board.forEach((cell, i) => {
    const div = document.createElement("div");
    div.className = "cell";
    div.textContent = cell;
    div.onclick = () => makeMove(i);
    boardDiv.appendChild(div);
  });
}

async function makeMove(pos) {
  try {
    const res = await fetch("http://localhost:5000/move", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ position: pos, username: currentUser })
    });
    const data = await res.json();

    if (data.error) {
      console.warn(data.error);
    } else {
      renderBoard(data.board);
      if (data.winner) {
        statusDisplay.textContent = data.winner === "Draw" ? "It's a Draw!" : `Winner: ${data.winner}`;
        setTimeout(() => location.reload(), 3000);
      }
    }
  } catch (err) {
    console.error("Move failed:", err);
  }
}

function resetGame() {
    botMode ? playWithBot() : startNewGame();
}
