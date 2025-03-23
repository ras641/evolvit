// @typedef {import('../src/message.ts').DevvitSystemMessage} DevvitSystemMessage
// @typedef {import('../src/message.ts').WebViewMessage} WebViewMessage

let CREATURES = [];
let FOOD = [];
let SPRITES = [];

let USERNAME = null;
let COUNTER = 0;

// Canvas setup
const canvas = document.getElementById("world");
const ctx = canvas.getContext("2d");

// Devvit Integration — receive messages
addEventListener("message", onDevvitMessage);

// Notify Devvit when WebView is ready
addEventListener("load", () => {
  postWebViewMessage({ type: "webViewReady" });
});

// Optional: triggerable counter commands (not used in this UI)
function increaseCounter() {
  postWebViewMessage({ type: "setCounter", data: { newCounter: COUNTER + 1 } });
}

function decreaseCounter() {
  postWebViewMessage({ type: "setCounter", data: { newCounter: COUNTER - 1 } });
}

/**
 * @param {WebViewMessage} msg
 */
function postWebViewMessage(msg) {
  parent.postMessage(msg, "*");
}

/**
 * @param {MessageEvent<DevvitSystemMessage>} ev
 */
function onDevvitMessage(ev) {
  if (ev.data?.type !== "devvit-message") return;

  const { message } = ev.data.data;

  switch (message.type) {
    case "initialData": {
      const { username, currentCounter } = message.data;
      USERNAME = username;
      COUNTER = currentCounter;
      break;
    }
    case "updateCounter": {
      COUNTER = message.data.currentCounter;
      break;
    }
    default:
      break;
  }
}

async function fetchData() {
  try {
    const res = await fetch("/viewer/data");
    const data = await res.json();
    CREATURES = data.creatures;
    FOOD = data.food;
    SPRITES = data.sprites;
  } catch (err) {
    console.error("State fetch error:", err);
  }
}

function drawFrame() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Draw food
  ctx.fillStyle = "green";
  for (const [x, y] of FOOD) {
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, 2 * Math.PI);
    ctx.fill();
  }

  // Draw creatures
  for (const c of CREATURES) {
    const angle = c.direction; // radians
    const cos = Math.cos(angle);
    const sin = Math.sin(angle);

    const layout = SPRITES[c.sprite_id];
    if (!layout) continue;

    const organs = layout
      .split("|")
      .filter(Boolean)
      .map(line => {
        const [type, x, y, size] = line.split(",");
        return { type, x: parseFloat(x), y: parseFloat(y), size: parseFloat(size) };
      });

    const body = organs.find(o => o.type === "body");
    if (!body) continue;

    const body_rx = body.x * cos - body.y * sin;
    const body_ry = body.x * sin + body.y * cos;
    const cx = c.position[0] + body_rx;
    const cy = c.position[1] + body_ry;

    for (const organ of organs) {
      if (organ.type === "body") continue;

      const rx = organ.x * cos - organ.y * sin;
      const ry = organ.x * sin + organ.y * cos;
      const ox = c.position[0] + rx;
      const oy = c.position[1] + ry;

      switch (organ.type) {
        case "spike": ctx.fillStyle = "red"; break;
        case "mouth": ctx.fillStyle = "yellow"; break;
        case "eye": ctx.fillStyle = "white"; break;
        case "flipper": ctx.fillStyle = "orange"; break;
        default: ctx.fillStyle = "#ccc"; break;
      }

      ctx.strokeStyle = "#000";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(ox, oy);
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(ox, oy, organ.size * 0.5, 0, 2 * Math.PI);
      ctx.fill();
    }

    // Draw body
    ctx.fillStyle = "#3498db";
    ctx.beginPath();
    ctx.arc(cx, cy, 8, 0, 2 * Math.PI);
    ctx.fill();
  }
}

// Animation Loop
let lastFrameTime = 0;
const FRAME_INTERVAL = 1000 / 10;

async function drawLoop(timestamp) {
  if (timestamp - lastFrameTime >= FRAME_INTERVAL) {
    await fetchData();
    drawFrame();
    lastFrameTime = timestamp;
  }
  requestAnimationFrame(drawLoop);
}

requestAnimationFrame(drawLoop);
