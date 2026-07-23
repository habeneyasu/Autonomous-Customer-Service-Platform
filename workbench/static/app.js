(() => {
  const els = {
    status: document.getElementById("run-status"),
    customer: document.getElementById("customer-id"),
    correlation: document.getElementById("correlation-id"),
    modes: document.getElementById("modes"),
    raw: document.getElementById("raw-message"),
    tokenized: document.getElementById("tokenized-message"),
    tokenMap: document.getElementById("token-map"),
    intent: document.getElementById("intent-badge"),
    allowed: document.getElementById("allowed-tools"),
    blocked: document.getElementById("blocked-tools"),
    cards: document.getElementById("tool-cards"),
    reply: document.getElementById("reply"),
    timeline: document.getElementById("timeline"),
    buttons: [...document.querySelectorAll("[data-scenario]")],
  };

  function escapeHtml(text) {
    return String(text)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }

  function highlightRaw(text) {
    return escapeHtml(text).replace(
      /\b(?:ACC-)?\d{8,16}\b/g,
      (m) => `<span class="hl-raw">${m}</span>`
    );
  }

  function highlightTok(text) {
    return escapeHtml(text).replace(
      /\[[A-Z]+_[0-9A-F]{4}\]/g,
      (m) => `<span class="hl-tok">${m}</span>`
    );
  }

  function renderModes(modes) {
    els.modes.innerHTML = "";
    Object.entries(modes || {}).forEach(([name, value]) => {
      const pill = document.createElement("div");
      pill.className = "mode" + (String(value).includes("LISTENING") ? " otp" : "");
      pill.innerHTML = `<span class="dot"></span>${escapeHtml(name)}: ${escapeHtml(value)}`;
      els.modes.appendChild(pill);
    });
  }

  function renderList(el, items, empty) {
    el.innerHTML = "";
    if (!items?.length) {
      const li = document.createElement("li");
      li.textContent = empty;
      el.appendChild(li);
      return;
    }
    items.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      el.appendChild(li);
    });
  }

  function renderCards(cards) {
    els.cards.innerHTML = "";
    if (!cards?.length) {
      els.cards.innerHTML = `<div class="card"><em style="color:var(--muted)">No tool invocations in this run.</em></div>`;
      return;
    }
    cards.forEach((card) => {
      const div = document.createElement("div");
      div.className = "card" + (card.blocked ? " blocked" : "");
      const err =
        card.error_code || card.error_message
          ? `<p class="err">${escapeHtml(card.error_code || "")}${
              card.error_code && card.error_message ? ": " : ""
            }${escapeHtml(card.error_message || "")}</p>`
          : "";
      div.innerHTML = `
        <div class="card-head">
          <strong>${escapeHtml(card.tool_name)}</strong>
          <span class="status ${escapeHtml(card.status)}">${escapeHtml(card.status)}</span>
        </div>
        <div class="endpoint">${escapeHtml(card.endpoint)}</div>
        <div class="payloads">
          <div>
            <h4>LLM parameters (tokenized / safe)</h4>
            <pre>${escapeHtml(JSON.stringify(card.llm_parameters, null, 2))}</pre>
          </div>
          <div>
            <h4>Rehydrated at MCP boundary</h4>
            <pre>${escapeHtml(JSON.stringify(card.rehydrated_parameters, null, 2))}</pre>
          </div>
        </div>
        ${err}`;
      els.cards.appendChild(div);
    });
  }

  function renderTimeline(steps) {
    els.timeline.innerHTML = "";
    (steps || []).forEach((step) => {
      const li = document.createElement("li");
      li.className = step.kind || "info";
      const ms = String(step.t_ms).padStart(3, "0");
      li.innerHTML = `
        <span class="t">[${ms} ms]</span>
        <span class="l">${escapeHtml(step.label)}</span>
        <span class="d">${escapeHtml(step.detail || "")}</span>`;
      els.timeline.appendChild(li);
    });
  }

  function render(snap) {
    els.customer.textContent = snap.customer_id;
    els.correlation.textContent = snap.correlation_id;
    renderModes(snap.modes);
    els.raw.innerHTML = highlightRaw(snap.raw_message);
    els.tokenized.innerHTML = highlightTok(snap.tokenized_message);
    const pairs = Object.entries(snap.token_map || {})
      .map(([tok, kind]) => `${tok}→${kind}`)
      .join(" · ");
    els.tokenMap.textContent = pairs
      ? `Vault tokens: ${pairs}`
      : "No PII tokens detected in this message.";
    els.intent.textContent = snap.intent;
    renderList(els.allowed, snap.allowed_tools, "(none)");
    renderList(els.blocked, snap.blocked_tools, "(none)");
    renderCards(snap.tool_cards);
    els.reply.textContent = snap.reply ? `Assistant reply: ${snap.reply}` : "";
    renderTimeline(snap.timeline);
    els.status.textContent = `Loaded: ${snap.scenario}`;
  }

  async function runScenario(key) {
    els.buttons.forEach((b) => (b.disabled = true));
    els.status.textContent = `Running ${key}…`;
    try {
      const res = await fetch(`/api/scenarios/${key}/run`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Run failed");
      render(data);
    } catch (err) {
      els.status.textContent = err.message || "Run failed";
    } finally {
      els.buttons.forEach((b) => (b.disabled = false));
    }
  }

  els.buttons.forEach((btn) => {
    btn.addEventListener("click", () => runScenario(btn.dataset.scenario));
  });
})();
