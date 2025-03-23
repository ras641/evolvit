const canvas = document.getElementById("world");
const ctx = canvas.getContext("2d");

const spriteColors = [
  "#3498db", "#e74c3c", "#2ecc71", "#f1c40f", "#9b59b6", "#1abc9c", "#e67e22"
];

function getColorForSprite(sprite_id) {
  return spriteColors[sprite_id % spriteColors.length] || "#95a5a6";
}

function drawFrame() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Draw food
  ctx.fillStyle = "green";
  for (const f of FOOD) {
    const [x, y] = f;
    ctx.beginPath();
    ctx.arc(x, y, 2, 0, 2 * Math.PI);
    ctx.fill();
  }

  // Draw creatures
  for (const c of CREATURES) {
    const [x, y] = c.position;
    const angle = Math.atan2(c.direction[1], c.direction[0]);

    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(angle);
    ctx.fillStyle = getColorForSprite(c.sprite_id);
    ctx.beginPath();
    ctx.moveTo(0, -6);
    ctx.lineTo(5, 5);
    ctx.lineTo(-5, 5);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  document.getElementById("info").textContent =
    `Creatures: ${CREATURES.length} | Food: ${FOOD.length}`;
}

drawFrame();
