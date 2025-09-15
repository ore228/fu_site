// 迷路ゲーム本体 (静的HTML用)
const CELL_SIZE = 24;
const MAZE_W = 25, MAZE_H = 25;
const markChoices = ['🔵', '💩', '🐸', '🐶', '🐱'];
const timeOptions = [
  { label: 'やさしい(60秒)', sec: 60 },
  { label: 'ふつう(30秒)', sec: 30 },
  { label: 'むずかしい(20秒)', sec: 20 }
];
let selectedMark = markChoices[0];
let selectedTime = 30;
let maze = [], startPos, goalPos;
let poopMarks = new Set();
let wallHitCount = 0, lastWallPos = null;
let timer = null, timeLeft = 0, timerRunning = false;
let cleared = false;

window.onload = () => {
  setupStartScreen();
  document.getElementById('start-screen').style.display = '';
}

// タッチイベント対応
let lastTouchCell = null;
function setupTouchEvents() {
  const canvas = document.getElementById('maze-canvas');
  if (!canvas) return;
  canvas.ontouchstart = function(e) {
    if (cleared || !timerRunning) return;
    e.preventDefault();
    lastTouchCell = getTouchCell(e);
    if (lastTouchCell) markCellWithWallCheck(lastTouchCell[0], lastTouchCell[1]);
  };
  canvas.ontouchmove = function(e) {
    if (cleared || !timerRunning) return;
    e.preventDefault();
    const cell = getTouchCell(e);
    if (cell && lastTouchCell) {
      markLineCells(lastTouchCell[0], lastTouchCell[1], cell[0], cell[1]);
    }
    lastTouchCell = cell;
  };
  canvas.ontouchend = function(e) {
    lastWallPos = null;
    lastTouchCell = null;
    e.preventDefault();
  };
}

function getTouchCell(e) {
  const canvas = e.target;
  const rect = canvas.getBoundingClientRect();
  const touch = e.touches[0] || e.changedTouches[0];
  const x = Math.floor((touch.clientX - rect.left) / CELL_SIZE);
  const y = Math.floor((touch.clientY - rect.top) / CELL_SIZE);
  if (!(0 <= x && x < MAZE_W && 0 <= y && y < MAZE_H)) return null;
  return [x, y];
}

function markLineCells(x0, y0, x1, y1) {
  const dx = Math.abs(x1 - x0), dy = Math.abs(y1 - y0);
  const sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
  let err = dx - dy;
  let x = x0, y = y0;
  while (true) {
    markCellWithWallCheck(x, y);
    if (x === x1 && y === y1) break;
    const e2 = 2 * err;
    if (e2 > -dy) { err -= dy; x += sx; }
    if (e2 < dx) { err += dx; y += sy; }
  }
}

function markCellWithWallCheck(x, y) {
  if (!(0 <= x && x < MAZE_W && 0 <= y && y < MAZE_H)) return;
  // 壁ヒット判定
  if (maze[y][x] === 1) {
    if (!lastWallPos || lastWallPos[0] !== x || lastWallPos[1] !== y) {
      wallHitCount++;
      lastWallPos = [x, y];
      if (wallHitCount === 1) {
        document.getElementById('warn').textContent = 'あと2回までOK';
      } else if (wallHitCount === 2) {
        document.getElementById('warn').textContent = 'あと1回までOK';
      } else if (wallHitCount >= 3) {
        timerRunning = false;
        cleared = true;
        document.getElementById('warn').textContent = '';
        showResult('NG', 'red');
      }
    }
    return;
  } else {
    lastWallPos = null;
    document.getElementById('warn').textContent = '';
  }
  // マーク追加
  const key = `${x},${y}`;
  if (!poopMarks.has(key)) {
    poopMarks.add(key);
    drawMaze();
  }
  // ゴール判定
  if (x === goalPos[0] && y === goalPos[1]) {
    if (checkPoopPath()) {
      timerRunning = false;
      cleared = true;
      showResult('OK', 'orange');
    } else {
      timerRunning = false;
      cleared = true;
      showResult('NG', 'red');
    }
  }
}

function setupStartScreen() {
  // マーク選択
  const markSel = document.getElementById('mark-select');
  markSel.innerHTML = '';
  markChoices.forEach((m, i) => {
    const btn = document.createElement('button');
    btn.className = 'mark-btn mark-' + i + (selectedMark===m ? ' selected':'');
    btn.textContent = m;
    btn.onclick = () => {
      selectedMark = m;
      setupStartScreen();
    };
    markSel.appendChild(btn);
  });
  // 時間制限
  const timeSel = document.getElementById('time-select');
  timeSel.innerHTML = '';
  timeOptions.forEach(opt => {
    const btn = document.createElement('button');
    btn.className = 'time-btn' + (selectedTime===opt.sec ? ' selected':'');
    btn.textContent = opt.label;
    btn.onclick = () => {
      selectedTime = opt.sec;
      setupStartScreen();
    };
    timeSel.appendChild(btn);
  });
  document.getElementById('start-btn').onclick = startGame;
}

function startGame() {
  document.getElementById('start-screen').style.display = 'none';
  document.getElementById('game-screen').style.display = '';
  document.getElementById('warn').textContent = '';
  document.getElementById('result').textContent = '';
  document.getElementById('restart-btn').style.display = 'none';
  poopMarks = new Set();
  wallHitCount = 0;
  lastWallPos = null;
  cleared = false;
  maze = generateMaze(MAZE_W, MAZE_H);
  drawMaze();
  timeLeft = selectedTime;
  timerRunning = true;
  updateTimer();
  document.getElementById('maze-canvas').onmousedown = onMouseDown;
  document.getElementById('maze-canvas').onmousemove = onMouseDrag;
  document.getElementById('maze-canvas').onmouseup = () => { lastWallPos = null; };
  setupTouchEvents();
}

function updateTimer() {
  document.getElementById('timer').textContent = `残り: ${timeLeft} 秒`;
  if (!timerRunning) return;
  if (timeLeft <= 0) {
    timerRunning = false;
    showResult('時間切れ', 'red');
    return;
  }
  timeLeft--;
  timer = setTimeout(updateTimer, 1000);
}

function showResult(msg, color) {
  document.getElementById('result').textContent = msg;
  document.getElementById('result').style.color = color;
  document.getElementById('restart-btn').style.display = '';
  document.getElementById('restart-btn').onclick = () => {
    document.getElementById('game-screen').style.display = 'none';
    document.getElementById('start-screen').style.display = '';
  };
}

function onMouseDown(e) {
  if (cleared || !timerRunning) return;
  handleDraw(e);
}
function onMouseDrag(e) {
  if (e.buttons !== 1 || cleared || !timerRunning) return;
  handleDraw(e);
}
function handleDraw(e) {
  const rect = e.target.getBoundingClientRect();
  const x = Math.floor((e.clientX - rect.left) / CELL_SIZE);
  const y = Math.floor((e.clientY - rect.top) / CELL_SIZE);
  if (!(0 <= x && x < MAZE_W && 0 <= y && y < MAZE_H)) return;
  // 壁ヒット判定
  if (maze[y][x] === 1) {
    if (!lastWallPos || lastWallPos[0] !== x || lastWallPos[1] !== y) {
      wallHitCount++;
      lastWallPos = [x, y];
      if (wallHitCount === 1) {
        document.getElementById('warn').textContent = 'あと2回までOK';
      } else if (wallHitCount === 2) {
        document.getElementById('warn').textContent = 'あと1回までOK';
      } else if (wallHitCount >= 3) {
        timerRunning = false;
        cleared = true;
        document.getElementById('warn').textContent = '';
        showResult('NG', 'red');
      }
    }
    return;
  } else {
    lastWallPos = null;
    document.getElementById('warn').textContent = '';
  }
  // マーク追加
  const key = `${x},${y}`;
  if (!poopMarks.has(key)) {
    poopMarks.add(key);
    drawMaze();
  }
  // ゴール判定
  if (x === goalPos[0] && y === goalPos[1]) {
    if (checkPoopPath()) {
      timerRunning = false;
      cleared = true;
      showResult('OK', 'orange');
    } else {
      timerRunning = false;
      cleared = true;
      showResult('NG', 'red');
    }
  }
}

function drawMaze() {
  const canvas = document.getElementById('maze-canvas');
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  // パステル壁色
  const pastel = ['#ffb7b2', '#ffe29a', '#b2ffd6', '#b2d8ff', '#e2b2ff', '#fff7b2', '#ffb2e2'];
  for (let y = 0; y < MAZE_H; y++) {
    for (let x = 0; x < MAZE_W; x++) {
      if (maze[y][x] === 1) {
        ctx.fillStyle = pastel[(x+y)%pastel.length];
      } else {
        ctx.fillStyle = '#fff';
      }
      ctx.fillRect(x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE);
    }
  }
  // スタート
  ctx.fillStyle = '#7cff7c';
  ctx.beginPath();
  ctx.arc(startPos[0]*CELL_SIZE+CELL_SIZE/2, startPos[1]*CELL_SIZE+CELL_SIZE/2, CELL_SIZE/2-2, 0, 2*Math.PI);
  ctx.fill();
  ctx.strokeStyle = 'green'; ctx.lineWidth = 2;
  ctx.stroke();
  ctx.fillStyle = '#fff';
  ctx.font = `${CELL_SIZE/2}px Arial`;
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText('S', startPos[0]*CELL_SIZE+CELL_SIZE/2, startPos[1]*CELL_SIZE+CELL_SIZE/2);
  // ゴール
  ctx.fillStyle = '#ff7c7c';
  ctx.beginPath();
  ctx.arc(goalPos[0]*CELL_SIZE+CELL_SIZE/2, goalPos[1]*CELL_SIZE+CELL_SIZE/2, CELL_SIZE/2-2, 0, 2*Math.PI);
  ctx.fill();
  ctx.strokeStyle = 'red'; ctx.lineWidth = 2;
  ctx.stroke();
  ctx.fillStyle = '#fff';
  ctx.fillText('G', goalPos[0]*CELL_SIZE+CELL_SIZE/2, goalPos[1]*CELL_SIZE+CELL_SIZE/2);
  // マーク
  ctx.font = `${CELL_SIZE-2}px Arial`;
  for (const key of poopMarks) {
    const [x, y] = key.split(',').map(Number);
    ctx.fillText(selectedMark, x*CELL_SIZE+CELL_SIZE/2, y*CELL_SIZE+CELL_SIZE/2+2);
  }
}

// --- 迷路生成（DFS） ---
function generateMaze(w, h) {
  // 1:壁, 0:道
  let maze = Array.from({length: h}, () => Array(w).fill(1));
  function shuffle(arr) {
    for (let i = arr.length-1; i > 0; i--) {
      const j = Math.floor(Math.random()*(i+1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
  }
  function carve(x, y) {
    maze[y][x] = 0;
    let dirs = [[0,-2],[0,2],[-2,0],[2,0]];
    shuffle(dirs);
    for (const [dx,dy] of dirs) {
      const nx = x+dx, ny = y+dy;
      if (ny>=0 && ny<h && nx>=0 && nx<w && maze[ny][nx] === 1) {
        maze[y+dy/2][x+dx/2] = 0;
        carve(nx, ny);
      }
    }
  }
  let sx = Math.floor(Math.random()*(w/2))*2, sy = Math.floor(Math.random()*(h/2))*2;
  carve(sx, sy);
  // スタート・ゴール
  startPos = [0, 0];
  goalPos = [w-1, h-1];
  maze[0][0] = 0; maze[h-1][w-1] = 0;
  return maze;
}

// --- 経路連結判定（BFS） ---
function checkPoopPath() {
  let q = [[startPos[0], startPos[1]]];
  let visited = new Set();
  while (q.length) {
    const [x, y] = q.shift();
    if (x === goalPos[0] && y === goalPos[1]) return true;
    for (const [dx,dy] of [[0,1],[1,0],[0,-1],[-1,0]]) {
      const nx = x+dx, ny = y+dy;
      if (nx>=0 && nx<MAZE_W && ny>=0 && ny<MAZE_H) {
        const key = `${nx},${ny}`;
        if (poopMarks.has(key) && !visited.has(key)) {
          visited.add(key);
          q.push([nx, ny]);
        }
      }
    }
  }
  return false;
}
