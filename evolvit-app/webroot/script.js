

addEventListener("message", (event) => {
  const msg = event.data?.data?.message;
  if (!msg) return;

  switch (msg.type) {
    case "stateUpdate": {
      const { creatures, food, sprites } = msg.data;

      document.getElementById("creatureCount").textContent = creatures.length;
      document.getElementById("foodCount").textContent = food.length;
      //document.getElementById("spriteOutput").textContent = JSON.stringify(sprites, null, 2);
      break;
    }

    case "error": {
      document.body.innerHTML = `<h1 style="color: red;">❌ Error</h1><p>${msg.data.message}</p>`;
      break;
    }
  }
});

// Notify the Devvit block that we're ready
addEventListener("load", () => {
  parent.postMessage({ type: "webViewReady" }, "*");
});