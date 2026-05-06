const boardDiv = document.getElementById("board");
const dashboardDiv = document.getElementById("dashboard");
const gameDiv = document.getElementById("game");
const statusDisplay = document.getElementById("status-display");

const usernameModal = document.getElementById("username-modal");
const player1Input = document.getElementById("player1-input");
const player2Input = document.getElementById("player2-input");
const player2Group = document.getElementById("player2-group");
const startMatchBtn = document.getElementById("start-match-btn");

const confirmModal = document.getElementById("confirm-modal");
const confirmMessage = document.getElementById("confirm-message");
const confirmYesBtn = document.getElementById("confirm-yes-btn");
const confirmNoBtn = document.getElementById("confirm-no-btn");

let botMode = false;
let player1Name = "";
let player2Name = "";

window.onload = () => {
  console.log("Page loaded, fetching leaderboard...");
  updateLeaderboard();
};

function updateLeaderboard() {
  fetch("http://65.0.239.221:5000/leaderboard")
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

function showToast(msg, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return alert(msg);

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${msg}</span>`;
  
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add("fade-out");
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function startNewGame(isRematch = false) {
  botMode = false;
  if (!isRematch) {
    openModal("pvp");
    return;
  }
  startMatchOnServer();
}

function playWithBot(isRematch = false) {
  botMode = true;
  if (!isRematch) {
    openModal("bot");
    return;
  }
  startMatchOnServer();
}

function openModal(mode) {
  usernameModal.style.display = "flex";
  player1Input.value = "";
  player2Input.value = "";
  if (mode === "bot") {
    player2Group.style.display = "none";
  } else {
    player2Group.style.display = "flex";
  }
  
  startMatchBtn.onclick = async () => {
    const p1 = player1Input.value.trim();
    const p2 = botMode ? "Bot" : player2Input.value.trim();
    
    if (!p1 || (!botMode && !p2)) {
      alert("Please enter username(s)!");
      return;
    }
    
    if (!botMode && p1 === p2) {
      alert("Player 1 and Player 2 must have different usernames!");
      return;
    }

    // Check DB
    try {
      let res = await fetch(`http://65.0.239.221:5000/check_username/${p1}`);
      if (res.ok) {
        let data = await res.json();
        if (data.exists) {
          const isExisting = await showCustomConfirm(`The username '${p1}' already exists. Are you the existing user '${p1}'?`);
          if (!isExisting) {
            player1Input.value = "";
            player1Input.focus();
            showToast("Please enter another name.");
            return;
          }
        }
      } else {
        console.warn("/check_username not found or error. Is the backend rebuilt?");
      }

      if (!botMode) {
        res = await fetch(`http://65.0.239.221:5000/check_username/${p2}`);
        if (res.ok) {
          let data = await res.json();
          if (data.exists) {
            const isExisting = await showCustomConfirm(`The username '${p2}' already exists. Are you the existing user '${p2}'?`);
            if (!isExisting) {
              player2Input.value = "";
              player2Input.focus();
              showToast("Please enter another name.");
              return;
            }
          }
        }
      }
    } catch(err) {
      console.error("Error checking username:", err);
      // We will allow it to continue if fetch fails, so the user isn't stuck if the backend isn't rebuilt
    }

    player1Name = p1;
    player2Name = p2;
    closeModal();
    startMatchOnServer();
  };
}

function closeModal() {
  usernameModal.style.display = "none";
}

function showCustomConfirm(msg) {
  return new Promise((resolve) => {
    confirmMessage.textContent = msg;
    confirmModal.style.display = "flex";
    
    confirmYesBtn.onclick = () => {
      confirmModal.style.display = "none";
      resolve(true);
    };
    
    confirmNoBtn.onclick = () => {
      confirmModal.style.display = "none";
      resolve(false);
    };
  });
}

async function startMatchOnServer() {
  try {
    const res = await fetch("http://65.0.239.221:5000/start", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ player1: player1Name, player2: player2Name, mode: botMode ? "bot" : "pvp" })
    });
    const data = await res.json();
    renderBoard(data.board);
    dashboardDiv.style.display = "none";
    gameDiv.style.display = "block";
    statusDisplay.textContent = `Turn: ${player1Name} (X)`;
  } catch (err) {
    console.error("Could not start game:", err);
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
    const res = await fetch("http://65.0.239.221:5000/move", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ position: pos })
    });
    const data = await res.json();

    if (data.error) {
      console.warn(data.error);
    } else {
      renderBoard(data.board);
      if (data.winner) {
        statusDisplay.textContent = data.winner === "Draw" ? "It's a Draw!" : `Winner: ${data.winner}`;
        setTimeout(() => location.reload(), 3000);
      } else {
        const nextName = data.next === "X" ? player1Name : player2Name;
        statusDisplay.textContent = `Turn: ${nextName} (${data.next})`;
      }
    }
  } catch (err) {
    console.error("Move failed:", err);
  }
}

function resetGame() {
    botMode ? playWithBot(true) : startNewGame(true);
}

