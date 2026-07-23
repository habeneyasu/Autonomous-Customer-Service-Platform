(() => {
  const els = {
    conversation: document.getElementById("conversation"),
    suggestions: document.getElementById("suggestions"),
    composer: document.getElementById("composer"),
    message: document.getElementById("message"),
    send: document.getElementById("btn-send"),
    status: document.getElementById("status"),
    health: document.getElementById("health"),
    settingsBtn: document.getElementById("btn-settings"),
    newBtn: document.getElementById("btn-new"),
    settings: document.getElementById("settings"),
    mode: document.getElementById("mode"),
    intent: document.getElementById("intent"),
    trace: document.getElementById("trace"),
  };

  const state = {
    sessionId: "",
    busy: false,
    thread: null,
    turnCount: 0,
  };

  function setHealth(health) {
    els.health.textContent = health.label;
    els.health.classList.toggle("ok", !!health.ok);
    els.health.classList.toggle("bad", !health.ok);
    els.health.title = health.url || "";
  }

  function setStatus(text) {
    els.status.textContent = text;
  }

  function setBusy(busy) {
    state.busy = busy;
    els.send.disabled = busy || !els.message.value.trim();
    els.message.disabled = busy;
  }

  function ensureThread() {
    if (!state.thread) {
      state.thread = document.createElement("div");
      state.thread.className = "thread";
      els.conversation.appendChild(state.thread);
    }
    return state.thread;
  }

  function clearConversation() {
    els.conversation.innerHTML = "";
    state.thread = null;
    state.turnCount = 0;
  }

  function appendMessage(role, text, options = {}) {
    const thread = ensureThread();
    const row = document.createElement("div");
    row.className = `msg ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = role === "user" ? "Y" : "A";

    const body = document.createElement("div");
    body.className = "msg-body";

    const meta = document.createElement("div");
    meta.className = "msg-meta";
    const name = document.createElement("span");
    name.textContent = role === "user" ? "You" : "ACSP Care";
    meta.appendChild(name);

    if (options.via) {
      const via = document.createElement("span");
      via.className = "via";
      via.textContent = `via ${options.via}`;
      meta.appendChild(via);
    }

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;

    body.appendChild(meta);
    body.appendChild(bubble);
    row.appendChild(avatar);
    row.appendChild(body);
    thread.appendChild(row);
    els.conversation.scrollTop = els.conversation.scrollHeight;
    return row;
  }

  function showTyping() {
    const thread = ensureThread();
    const row = document.createElement("div");
    row.className = "msg assistant typing";
    row.id = "typing";
    row.innerHTML = `
      <div class="avatar" aria-hidden="true">A</div>
      <div class="msg-body">
        <div class="msg-meta"><span>ACSP Care</span></div>
        <div class="bubble">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>
      </div>`;
    thread.appendChild(row);
    els.conversation.scrollTop = els.conversation.scrollHeight;
  }

  function hideTyping() {
    document.getElementById("typing")?.remove();
  }

  function renderSuggestions(examples) {
    els.suggestions.innerHTML = "";
    if (!examples?.length) {
      els.suggestions.hidden = true;
      return;
    }
    examples.forEach((item) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chip";
      btn.textContent = item.label;
      btn.addEventListener("click", () => sendMessage(item.prompt));
      els.suggestions.appendChild(btn);
    });
    els.suggestions.hidden = false;
  }

  function fillIntents(intents) {
    els.intent.innerHTML = "";
    (intents || []).forEach((item) => {
      const opt = document.createElement("option");
      opt.value = item.label;
      opt.textContent = item.label;
      els.intent.appendChild(opt);
    });
  }

  function autoGrow() {
    els.message.style.height = "auto";
    els.message.style.height = `${Math.min(els.message.scrollHeight, 120)}px`;
    els.send.disabled = state.busy || !els.message.value.trim();
  }

  async function startSession() {
    setBusy(true);
    setStatus("Starting session…");
    try {
      const res = await fetch("/api/session");
      if (!res.ok) throw new Error("Could not start session");
      const data = await res.json();
      state.sessionId = data.session_id;
      clearConversation();
      appendMessage("assistant", data.welcome);
      renderSuggestions(data.examples);
      fillIntents(data.intents);
      els.trace.value = data.trace || "";
      setHealth(data.health);
      setStatus(data.status || "Ready");
    } catch (err) {
      setStatus(err.message || "Session failed");
      setHealth({ ok: false, label: "Secure tools offline", url: "" });
    } finally {
      setBusy(false);
      autoGrow();
      els.message.focus();
    }
  }

  async function sendMessage(raw) {
    const text = (raw || "").trim();
    if (!text || state.busy) return;

    els.suggestions.hidden = true;
    state.turnCount += 1;
    ensureThread().classList.add("has-history");
    appendMessage("user", text);
    els.message.value = "";
    autoGrow();
    setBusy(true);
    setStatus("Working…");
    showTyping();

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          session_id: state.sessionId,
          mode: els.mode.value,
          intent: els.intent.value || "Auto-detect",
        }),
      });
      const data = await res.json().catch(() => ({}));
      hideTyping();
      if (!res.ok) {
        const detail = data.detail || "Request failed";
        appendMessage(
          "assistant",
          "I’m unable to complete that request right now. Please try again in a moment."
        );
        setStatus(typeof detail === "string" ? detail : "Request failed");
        return;
      }
      appendMessage("assistant", data.reply, { via: data.via || null });
      els.trace.value = data.trace || "";
      if (data.session_id) state.sessionId = data.session_id;
      setStatus(data.status || "Done");
    } catch (err) {
      hideTyping();
      appendMessage(
        "assistant",
        "I’m unable to complete that request right now. Please try again in a moment."
      );
      setStatus(err.message || "Network error");
    } finally {
      setBusy(false);
      els.message.focus();
    }
  }

  els.composer.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage(els.message.value);
  });

  els.message.addEventListener("input", autoGrow);

  els.message.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage(els.message.value);
    }
  });

  els.newBtn.addEventListener("click", () => startSession());
  els.settingsBtn.addEventListener("click", () => els.settings.showModal());

  startSession();
  setInterval(async () => {
    try {
      const res = await fetch("/api/health");
      if (res.ok) setHealth(await res.json());
    } catch {
      /* ignore */
    }
  }, 15000);
})();
