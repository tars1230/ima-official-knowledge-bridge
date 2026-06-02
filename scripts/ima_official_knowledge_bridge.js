(function () {
  const BRIDGE_VERSION = "2026-06-02T14:30:00+08:00";
  const configuredPort = new URLSearchParams((globalThis.location && globalThis.location.search) || "").get("bridge") || "19795";
  const BASE = `http://127.0.0.1:${configuredPort}`;

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const stringify = (value) => {
    try {
      return JSON.stringify(value);
    } catch {
      return "";
    }
  };
  const parseMaybeJson = (value, fallback = null) => {
    if (value == null) return fallback;
    if (typeof value !== "string") return value;
    try {
      return JSON.parse(value);
    } catch {
      return fallback;
    }
  };
  const getSearchParam = (name) => {
    try {
      return new URLSearchParams(globalThis.location && globalThis.location.search || "").get(name) || "";
    } catch {
      return "";
    }
  };
  const normalizeSessionId = (value) => {
    if (value == null) return "";
    if (typeof value === "string" || typeof value === "number") return String(value);
    return "";
  };
  const safeSnapshot = (value, depth = 0, maxDepth = 8, seen = new WeakSet()) => {
    if (depth > maxDepth || value == null) return value == null ? value : `[${typeof value}]`;
    if (typeof value !== "object") return value;
    if (seen.has(value)) return "[circular]";
    seen.add(value);
    if (Array.isArray(value)) return value.slice(0, 12).map((item) => safeSnapshot(item, depth + 1, maxDepth, seen));
    if (value instanceof Map) {
      return {
        __ctor: "Map",
        entries: Array.from(value.entries()).slice(0, 20).map(([key, item]) => [String(key), safeSnapshot(item, depth + 1, maxDepth, seen)]),
      };
    }
    const out = { __ctor: value.constructor && value.constructor.name };
    for (const key of Reflect.ownKeys(value).slice(0, 120)) {
      const outKey = String(key);
      try {
        const item = value[key];
        out[outKey] = typeof item === "function" ? "[function]" : safeSnapshot(item, depth + 1, maxDepth, seen);
      } catch {
        out[outKey] = "[unreadable]";
      }
    }
    return out;
  };
  const isNoiseKey = (key) =>
    /^(id|eventId|sessionId|traceId|msgSeqId|parentId|from|icon|url|type|updateType|createTime|updateTime|timestamp)$/i.test(String(key));
  const stringScore = (path, text) => {
    const key = path[path.length - 1] || "";
    let score = 0;
    if (/^(content|text|message|markdown|answer|value|summary)$/i.test(String(key))) score += 20;
    if (/blockList\.\d+\.data/i.test(path.join("."))) score += 10;
    if (/[\u4e00-\u9fffA-Za-z]/.test(text)) score += 4;
    if (text.length >= 4) score += Math.min(12, Math.floor(text.length / 8));
    if (/^(id|eventId|sessionId|traceId|msgSeqId|parentId|url)$/i.test(String(key))) score -= 50;
    return score;
  };
  const collectStrings = (value, path = [], depth = 0, seen = new WeakSet()) => {
    if (depth > 12 || value == null) return [];
    if (typeof value === "string") {
      const text = value.trim();
      return text ? [{ path: path.join("."), text, score: stringScore(path, text) }] : [];
    }
    if (typeof value !== "object") return [];
    if (seen.has(value)) return [];
    seen.add(value);
    const out = [];
    if (typeof value.toJSON === "function") {
      try {
        const json = value.toJSON();
        if (json && json !== value) out.push(...collectStrings(json, path.concat("toJSON"), depth + 1, seen));
      } catch {}
    }
    if (value instanceof Map) {
      for (const [key, item] of value.entries()) {
        if (!isNoiseKey(key)) out.push(...collectStrings(item, path.concat(String(key)), depth + 1, seen));
      }
      return out;
    }
    if (Array.isArray(value)) {
      value.slice(0, 50).forEach((item, index) => out.push(...collectStrings(item, path.concat(String(index)), depth + 1, seen)));
      return out;
    }
    for (const key of Reflect.ownKeys(value).slice(0, 120)) {
      if (isNoiseKey(key)) continue;
      try {
        const item = value[key];
        if (typeof item !== "function") out.push(...collectStrings(item, path.concat(String(key)), depth + 1, seen));
      } catch {}
    }
    return out;
  };
  const blockSummaries = (answer) => {
    const blocks = (answer && Array.isArray(answer.blockList) && answer.blockList) || [];
    return blocks.slice(0, 20).map((block, index) => {
      const data = block && block.data;
      const candidates = collectStrings(data, ["blockList", String(index), "data"])
        .sort((a, b) => b.score - a.score)
        .slice(0, 12);
      return {
        index,
        type: block && block.type,
        idPresent: Boolean(block && block.id),
        dataCtor: data && data.constructor && data.constructor.name,
        dataKeys: data && typeof data === "object" ? Reflect.ownKeys(data).slice(0, 50).map(String) : [],
        textCandidates: candidates.map((item) => ({
          path: item.path,
          score: item.score,
          text: item.text.slice(0, 500),
        })),
      };
    });
  };
  const pickAnswerText = (answer) => {
    const blocks = (answer && Array.isArray(answer.blockList) && answer.blockList) || [];
    const scored = [];
    for (const [index, block] of blocks.entries()) {
      const blockType = String((block && block.type) || "");
      const typeScore = /blockMessage/i.test(blockType) ? 80 : /message/i.test(blockType) ? 60 : /blockThinking/i.test(blockType) ? 5 : 20;
      for (const item of collectStrings(block && block.data, ["blockList", String(index), "data"])) {
        scored.push({ ...item, score: item.score + typeScore });
      }
    }
    if (!scored.length) scored.push(...collectStrings(answer, ["answer"]));
    scored.sort((a, b) => b.score - a.score);
    return scored.length ? scored[0].text : "";
  };
  const findText = (value, depth = 0) => {
    if (depth > 10 || value == null) return "";
    if (typeof value === "string") return value;
    if (typeof value !== "object") return "";
    for (const key of ["content", "Text", "text", "message", "markdown", "answer", "value", "closeMsg"]) {
      if (typeof value[key] === "string" && value[key]) return value[key];
    }
    if (Array.isArray(value.blockList)) {
      for (const block of value.blockList) {
        const found = findText(block && block.data, depth + 1);
        if (found) return found;
      }
    }
    if (Array.isArray(value)) {
      for (const item of value) {
        const found = findText(item, depth + 1);
        if (found) return found;
      }
    } else {
      for (const [key, item] of Object.entries(value)) {
        if (isNoiseKey(key)) continue;
        const found = findText(item, depth + 1);
        if (found) return found;
      }
    }
    return "";
  };
  const waitForDI = async () => {
    for (let i = 0; i < 200; i += 1) {
      const di = globalThis.__IMA_KB_CODEX_DI__;
      if (di && di.container && di.tokens) return di;
      await sleep(100);
    }
    return null;
  };
  const waitForSelectedSessionId = async (sessionPresenter, expected = "") => {
    for (let i = 0; i < 200; i += 1) {
      try {
        const state = sessionPresenter.useStore.getState();
        const sessionId = normalizeSessionId(state && state.selectedSessionId);
        if (sessionId && (!expected || sessionId === expected)) return sessionId;
      } catch {}
      await sleep(100);
    }
    return "";
  };
  const getLatestAiSection = (sections, baselineIds) => {
    const fresh = sections.filter((section) => section && !baselineIds.has(section.id));
    return [...fresh].reverse().find((section) => section && section.aiAnswer) || [...sections].reverse().find((section) => section && section.aiAnswer) || null;
  };
  const summarizeSection = (section) => {
    if (!section || !section.aiAnswer) return null;
    const answer = section.aiAnswer;
    return {
      sectionId: section.id,
      from: section.from,
      isFinish: Boolean(answer.isFinish),
      closeMsg: typeof answer.closeMsg === "string" ? answer.closeMsg : "",
      errorCode: Object.prototype.hasOwnProperty.call(answer, "errorCode") ? answer.errorCode : undefined,
      blockSummaries: blockSummaries(answer),
      answerSnapshot: safeSnapshot(answer, 0, 8),
    };
  };
  const getJob = async () => {
    const response = await fetch(`${BASE}/job`, { cache: "no-store" });
    if (response.status === 204) return null;
    if (!response.ok) throw new Error(`job fetch failed: ${response.status}`);
    return response.json();
  };
  const postResult = async (payload) => {
    await fetch(`${BASE}/result`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
  };
  const askViaKnowledgePage = async (job) => {
    const di = await waitForDI();
    if (!di) throw new Error("official knowledge DI bridge unavailable");
    const { container, tokens } = di;
    const sessionPresenter = container.get(tokens.SessionKnowledgePresenter);
    const chatFactory = container.get(tokens.ChatListPresenterFactory);
    if (!sessionPresenter || !chatFactory) throw new Error("knowledge presenters unavailable");

    const requestedSessionId = normalizeSessionId(job.sessionId);
    let sessionId = "";
    const existingSessionId = normalizeSessionId(sessionPresenter.useStore.getState().selectedSessionId);
    if (requestedSessionId) {
      if (existingSessionId !== requestedSessionId) {
        await sessionPresenter.loadSessionById(requestedSessionId);
      }
      sessionId = await waitForSelectedSessionId(sessionPresenter, requestedSessionId);
    } else {
      if (!existingSessionId) {
        await sessionPresenter.load();
      }
      sessionId = await waitForSelectedSessionId(sessionPresenter);
    }
    if (!sessionId) throw new Error("knowledge session unavailable");

    const chat = chatFactory(sessionId);
    const store = chat && chat.useStore;
    if (!store || typeof store.getState !== "function") throw new Error("knowledge chat store unavailable");

    let latestState = store.getState();
    const baselineIds = new Set(((latestState && latestState.sections) || []).map((section) => section && section.id).filter(Boolean));
    const events = [];
    let done = false;
    let unsubscribe = () => {};
    const finishPromise = new Promise((resolve) => {
      const finish = () => {
        if (done) return;
        done = true;
        clearTimeout(timer);
        try {
          unsubscribe();
        } catch {}
        resolve();
      };
      const handleState = (state) => {
        latestState = state || latestState;
        const sections = (latestState && latestState.sections) || [];
        const latestAi = getLatestAiSection(sections, baselineIds);
        if (!latestAi || !latestAi.aiAnswer) return;
        const answer = latestAi.aiAnswer;
        const content = pickAnswerText(answer) || findText(answer || latestAi) || "";
        events.push({
          event: "KB_UPDATE",
          data: {
            sectionId: latestAi.id,
            contentPreview: content.slice(0, 1200),
            isFinish: Boolean(answer.isFinish),
            closeMsg: typeof answer.closeMsg === "string" ? answer.closeMsg : "",
            errorCode: Object.prototype.hasOwnProperty.call(answer, "errorCode") ? answer.errorCode : undefined,
            blockSummaries: blockSummaries(answer).slice(0, 4),
          },
        });
        if (answer.isFinish) {
          setTimeout(finish, 1200);
        }
      };
      unsubscribe = typeof store.subscribe === "function" ? store.subscribe(handleState) : () => {};
      const timer = setTimeout(finish, Math.max(1000, Number(job.maxEvents || 80) * 1000));
      handleState(latestState);
      chat.askKnowledgeTagsQuestion(job.question || "ping", [], []);
    });

    await finishPromise;

    const finalState = store.getState();
    const finalSections = (finalState && finalState.sections) || [];
    const finalAi = getLatestAiSection(finalSections, baselineIds);
    const finalText = finalAi && finalAi.aiAnswer ? pickAnswerText(finalAi.aiAnswer) || findText(finalAi.aiAnswer) || "" : "";
    return {
      bridgeVersion: BRIDGE_VERSION,
      mode: "official-knowledge",
      currentUrl: globalThis.location && globalThis.location.href || "",
      context: {
        knowledgeBaseId: getSearchParam("knowledgeBaseId"),
        shareId: getSearchParam("shareId"),
        folderId: getSearchParam("folderId"),
      },
      sessionId,
      sessionIdPresent: Boolean(sessionId),
      sessionReused: Boolean(requestedSessionId && requestedSessionId === sessionId),
      authShape: { officialKnowledge: true },
      finalText,
      finalSectionSummary: summarizeSection(finalAi),
      events,
    };
  };
  const main = async () => {
    const job = await getJob();
    if (!job) return;
    try {
      const result = await askViaKnowledgePage(job);
      await postResult({ ok: true, result });
    } catch (error) {
      await postResult({
        ok: false,
        error: String((error && error.stack) || (error && error.message) || error),
      });
    }
  };
  main().catch(async (error) => {
    try {
      await postResult({
        ok: false,
        error: String((error && error.stack) || (error && error.message) || error),
      });
    } catch {}
  });
})();
