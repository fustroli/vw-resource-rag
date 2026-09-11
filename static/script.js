const form = document.getElementById("ask-form");
const input = document.getElementById("question");
const submitBtn = document.getElementById("submit-btn");
const answerSection = document.getElementById("answer-section");
const answerEl = document.getElementById("answer");
const sourcesEl = document.getElementById("sources");
const emptyState = document.getElementById("empty-state");
const content = document.getElementById("content");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = input.value.trim();
  if (!question) return;

  setLoading(true);
  emptyState.hidden = true;
  answerSection.hidden = false;
  answerEl.textContent = "";
  sourcesEl.innerHTML = "";
  answerEl.appendChild(cursorEl());

  try {
    const resp = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    if (!resp.ok || !resp.body) {
      throw new Error(`Request failed: ${resp.status}`);
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.trim()) continue;
        handleEvent(JSON.parse(line));
      }
    }
  } catch (err) {
    answerEl.textContent = `Error: ${err.message}`;
  } finally {
    removeCursor();
    setLoading(false);
  }
});

function handleEvent(event) {
  if (event.type === "sources") {
    renderSources(event.items);
  } else if (event.type === "token") {
    const cursor = answerEl.querySelector(".cursor");
    const textNode = document.createTextNode(event.content);
    answerEl.insertBefore(textNode, cursor);
    content.scrollTop = content.scrollHeight;
  }
}

function renderSources(items) {
  if (!items.length) return;
  const label = document.createElement("div");
  label.className = "sources-label";
  label.textContent = "Sources";
  sourcesEl.appendChild(label);

  for (const source of items) {
    const link = document.createElement("a");
    link.href = source.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = source.title;
    sourcesEl.appendChild(link);
  }
}

function cursorEl() {
  const span = document.createElement("span");
  span.className = "cursor";
  return span;
}

function removeCursor() {
  const cursor = answerEl.querySelector(".cursor");
  if (cursor) cursor.remove();
}

function setLoading(isLoading) {
  submitBtn.disabled = isLoading;
  submitBtn.textContent = isLoading ? "Thinking…" : "Ask";
}
