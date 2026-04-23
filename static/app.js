(() => {
  const $ = (id) => document.getElementById(id);

  const usernameInput = $("usernameInput");
  const roomInput = $("roomInput");
  const apiKeyInput = $("apiKeyInput");
  const baseUrlInput = $("baseUrlInput");
  const modelInput = $("modelInput");
  const rememberKeyCheck = $("rememberKeyCheck");
  const connectBtn = $("connectBtn");
  const disconnectBtn = $("disconnectBtn");
  const connBadge = $("connBadge");
  const roomLabel = $("roomLabel");
  const onlineCount = $("onlineCount");
  const onlineList = $("onlineList");
  const messages = $("messages");
  const composer = $("composer");
  const messageInput = $("messageInput");
  const sendBtn = $("sendBtn");

  const storage = window.localStorage;

  function loadDefaults() {
    usernameInput.value = storage.getItem("chat.username") || "";
    roomInput.value = storage.getItem("chat.room") || "lobby";
    baseUrlInput.value = storage.getItem("chat.base_url") || "";
    modelInput.value = storage.getItem("chat.model") || "";

    const remember = storage.getItem("chat.remember_key") === "1";
    rememberKeyCheck.checked = remember;
    if (remember) {
      apiKeyInput.value = storage.getItem("chat.api_key") || "";
    } else {
      apiKeyInput.value = "";
    }
  }

  function saveDefaults() {
    storage.setItem("chat.username", usernameInput.value.trim());
    storage.setItem("chat.room", roomInput.value.trim() || "lobby");
    storage.setItem("chat.base_url", baseUrlInput.value.trim());
    storage.setItem("chat.model", modelInput.value.trim());

    const remember = !!rememberKeyCheck.checked;
    storage.setItem("chat.remember_key", remember ? "1" : "0");
    if (remember) {
      storage.setItem("chat.api_key", apiKeyInput.value.trim());
    } else {
      storage.removeItem("chat.api_key");
    }
  }

  function setConnected(isConnected) {
    connBadge.textContent = isConnected ? "Connected" : "Disconnected";
    connBadge.classList.toggle("badge-on", isConnected);
    connBadge.classList.toggle("badge-off", !isConnected);
    connectBtn.disabled = isConnected;
    disconnectBtn.disabled = !isConnected;
    sendBtn.disabled = !isConnected;
  }

  function clearMessages() {
    messages.innerHTML = "";
  }

  function appendMessage({ type, from, text, ts, selfName, aiName }) {
    const el = document.createElement("div");
    el.className = "msg";

    if (type === "system") el.classList.add("msg-system");
    if (type === "chat" && from === aiName) el.classList.add("msg-ai");
    if (type === "chat" && from === selfName) el.classList.add("msg-self");

    const meta = document.createElement("div");
    meta.className = "meta";

    const tsEl = document.createElement("span");
    tsEl.textContent = ts || "";

    const fromEl = document.createElement("span");
    fromEl.className = "from";
    fromEl.textContent = type === "chat" ? from || "-" : "System";

    meta.appendChild(tsEl);
    meta.appendChild(fromEl);

    const textEl = document.createElement("div");
    textEl.className = "text";
    textEl.textContent = text || "";

    el.appendChild(meta);
    el.appendChild(textEl);
    messages.appendChild(el);

    // keep scrolled near bottom
    messages.scrollTop = messages.scrollHeight;
  }

  function renderOnline(users) {
    onlineList.innerHTML = "";
    (users || []).forEach((u) => {
      const pill = document.createElement("span");
      pill.className = "pill";
      pill.textContent = u;
      onlineList.appendChild(pill);
    });
  }

  function wsUrl(username, room) {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const u = new URL(`${proto}://${window.location.host}/ws`);
    u.searchParams.set("username", username);
    u.searchParams.set("room", room);
    return u.toString();
  }

  let ws = null;
  let selfName = "";
  let currentRoom = "";
  let aiName = "AI";
  let aiAutoReply = true;

  async function loadConfig() {
    try {
      const resp = await fetch("/config");
      if (!resp.ok) return;
      const data = await resp.json();
      if (data && typeof data.ai_name === "string" && data.ai_name.trim()) {
        aiName = data.ai_name.trim();
      }
      if (data && typeof data.ai_auto_reply === "boolean") {
        aiAutoReply = data.ai_auto_reply;
      }
      if (data && typeof data.openai_base_url === "string" && !baseUrlInput.value.trim()) {
        baseUrlInput.value = data.openai_base_url;
      }
      if (data && typeof data.openai_model === "string" && !modelInput.value.trim()) {
        modelInput.value = data.openai_model;
      }
    } catch {
      // ignore
    }
  }

  function sendConfig() {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(
      JSON.stringify({
        type: "config",
        openai_api_key: apiKeyInput.value.trim(),
        openai_base_url: baseUrlInput.value.trim(),
        openai_model: modelInput.value.trim(),
      }),
    );
  }

  function connect() {
    const username = usernameInput.value.trim() || "guest";
    const room = roomInput.value.trim() || "lobby";
    saveDefaults();

    selfName = username;
    currentRoom = room;
    roomLabel.textContent = room;

    clearMessages();
    renderOnline([]);
    onlineCount.textContent = "0";

    const url = wsUrl(username, room);
    ws = new WebSocket(url);

    ws.addEventListener("open", () => {
      setConnected(true);
      sendConfig();
      messageInput.focus();
    });

    ws.addEventListener("close", () => {
      setConnected(false);
    });

    ws.addEventListener("error", () => {
      setConnected(false);
    });

    ws.addEventListener("message", (ev) => {
      let data = null;
      try {
        data = JSON.parse(ev.data);
      } catch {
        return;
      }

      if (!data || typeof data !== "object") return;

      if (data.type === "welcome") {
        if (typeof data.ai_name === "string" && data.ai_name.trim()) {
          aiName = data.ai_name.trim();
        }
        if (typeof data.ai_auto_reply === "boolean") {
          aiAutoReply = data.ai_auto_reply;
        }
        if (typeof data.username === "string" && data.username.trim()) {
          selfName = data.username.trim();
        }
        if (typeof data.room === "string" && data.room.trim()) {
          currentRoom = data.room.trim();
          roomLabel.textContent = currentRoom;
        }
        if (typeof data.openai_base_url === "string" && !baseUrlInput.value.trim()) {
          baseUrlInput.value = data.openai_base_url;
        }
        if (typeof data.openai_model === "string" && !modelInput.value.trim()) {
          modelInput.value = data.openai_model;
        }
        appendMessage({
          type: "system",
          text: `Connected as ${selfName} in room ${currentRoom} (AI auto-reply: ${aiAutoReply ? "on" : "off"})`,
          ts: "",
          selfName,
          aiName,
        });
        return;
      }

      if (data.type === "config_ack") {
        if (data.ok) {
          if (typeof data.openai_base_url === "string") baseUrlInput.value = data.openai_base_url;
          if (typeof data.openai_model === "string") modelInput.value = data.openai_model;
          appendMessage({
            type: "system",
            text: `Config updated (API key: ${data.has_key ? "set" : "empty"})`,
            ts: "",
            selfName,
            aiName,
          });
        } else {
          appendMessage({
            type: "system",
            text: `Config error: ${data.error || "unknown"}`,
            ts: "",
            selfName,
            aiName,
          });
        }
        return;
      }

      if (data.type === "history" && Array.isArray(data.messages)) {
        clearMessages();
        data.messages.forEach((m) => {
          appendMessage({
            type: m.type,
            from: m.from,
            text: m.text,
            ts: m.ts,
            selfName,
            aiName,
          });
        });
        return;
      }

      if (data.type === "presence") {
        onlineCount.textContent = String(data.count || 0);
        renderOnline(data.users || []);
        return;
      }

      if (data.type === "chat" || data.type === "system") {
        appendMessage({
          type: data.type,
          from: data.from,
          text: data.text,
          ts: data.ts,
          selfName,
          aiName,
        });
      }
    });
  }

  function disconnect() {
    if (ws) {
      ws.close();
      ws = null;
    }
  }

  function send(text) {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ type: "chat", text }));
  }

  connectBtn.addEventListener("click", () => connect());
  disconnectBtn.addEventListener("click", () => disconnect());

  composer.addEventListener("submit", (ev) => {
    ev.preventDefault();
    const text = messageInput.value.trim();
    if (!text) return;
    send(text);
    messageInput.value = "";
    messageInput.focus();
  });

  loadDefaults();
  loadConfig();
  setConnected(false);
})();
