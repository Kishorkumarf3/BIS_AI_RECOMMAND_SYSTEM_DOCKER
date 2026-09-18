/**
 * BIS Standards AI Assistant — Content Script (Manifest V3)
 *
 * Attaches to textareas on Indian government procurement portals (GeM, eProcure, CPPP),
 * debounces user typing, fetches IS-code recommendations from the FastAPI backend,
 * and renders a floating widget with "One-Click Insert" for compliance clauses.
 */

const BACKEND_URL = "http://localhost:8000";
const DEBOUNCE_MS = 600;
const MIN_QUERY_LEN = 8;

let debounceTimer = null;
let currentWidget = null;
let currentTextarea = null;
let lastRecommendations = null;

// ─── Utilities ─────────────────────────────────────────────────────────────

function debounce(fn, delay) {
  let timer = null;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

// ─── Widget Creation & Rendering ───────────────────────────────────────────

function createWidget(rect) {
  // Remove any existing widget
  removeWidget();

  const widget = document.createElement("div");
  widget.className = "bis-ai-widget";
  widget.style.left = `${rect.left + rect.width + 8}px`;
  widget.style.top = `${rect.top}px`;

  widget.innerHTML = `
    <div class="bis-ai-widget__header">
      <span class="bis-ai-widget__title">BIS Standards AI</span>
      <button class="bis-ai-widget__close" title="Close">&times;</button>
    </div>
    <div class="bis-ai-widget__body">
      <div class="bis-ai-loading">
        <div class="bis-spinner"></div>
        <div>Searching BIS catalog…</div>
      </div>
    </div>
    <div class="bis-ai-widget__footer">
      <span class="bis-ai-status"></span>
      <button class="bis-ai-insert-btn" disabled>Insert Clause</button>
    </div>
  `;

  document.body.appendChild(widget);
  currentWidget = widget;

  // Animate in
  requestAnimationFrame(() => widget.classList.add("bis-visible"));

  // Close button
  widget.querySelector(".bis-ai-widget__close").addEventListener("click", removeWidget);

  // Insert button
  widget.querySelector(".bis-ai-insert-btn").addEventListener("click", insertClause);

  return widget;
}

function removeWidget() {
  if (currentWidget) {
    currentWidget.remove();
    currentWidget = null;
    lastRecommendations = null;
  }
}

function renderRecommendations(data) {
  if (!currentWidget) return;
  const body = currentWidget.querySelector(".bis-ai-widget__body");
  const insertBtn = currentWidget.querySelector(".bis-ai-insert-btn");
  const status = currentWidget.querySelector(".bis-ai-status");

  if (!data.recommendations || data.recommendations.length === 0) {
    body.innerHTML = '<div class="bis-ai-error">No matching standards found. Try refining your requirement.</div>';
    status.textContent = "0 results";
    return;
  }

  lastRecommendations = data;

  body.innerHTML = data.recommendations
    .map(
      (rec) => `
      <div class="bis-ai-rec" data-is-code="${rec.is_code}">
        <div class="bis-ai-rec__code">${rec.is_code} <span style="color:#64748b;font-weight:400;font-size:11px">(${(rec.score * 100).toFixed(0)}% match)</span></div>
        <div class="bis-ai-rec__title">${rec.title}</div>
        <div class="bis-ai-rec__flags">
          ${rec.qco_mandatory ? '<span class="bis-ai-flag bis-ai-flag--qco">QCO</span>' : ""}
          ${rec.crs_applicable ? '<span class="bis-ai-flag bis-ai-flag--crs">CRS</span>' : ""}
          ${rec.simplified_procedure ? '<span class="bis-ai-flag bis-ai-flag--fast">30-day Fast Track</span>' : ""}
        </div>
      </div>
    `
    )
    .join("");

  const legalCount = data.legal_framework ? data.legal_framework.length : 0;
  status.textContent = `${data.recommendations.length} standards · ${legalCount} BIS rules cited`;
  insertBtn.disabled = !data.compliance_clause;
}

function renderError(message) {
  if (!currentWidget) return;
  const body = currentWidget.querySelector(".bis-ai-widget__body");
  body.innerHTML = `<div class="bis-ai-error">${message}</div>`;
}

// ─── API Call ──────────────────────────────────────────────────────────────

async function fetchRecommendations(query) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: query,
        top_k: 5,
        generate_clause: true,
      }),
    });

    if (!res.ok) throw new Error(`Backend error: ${res.status}`);
    return await res.json();
  } catch (err) {
    renderError("Cannot connect to BIS AI backend. Is the FastAPI server running on localhost:8000?");
    return null;
  }
}

// ─── Insert Clause into Textarea ───────────────────────────────────────────

function insertClause() {
  if (!currentTextarea || !lastRecommendations?.compliance_clause) return;

  const textarea = currentTextarea;
  const clause = lastRecommendations.compliance_clause;
  const separator = textarea.value.length > 0 ? "\n\n" : "";

  // Insert at cursor position, or append
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const before = textarea.value.substring(0, start);
  const after = textarea.value.substring(end);

  const insertText = `${separator}--- BIS Compliance Clause (Auto-Generated) ---\n${clause}\n--- End of Clause ---`;

  textarea.value = before + insertText + after;

  // Trigger input event so the host page picks up the change
  textarea.dispatchEvent(new Event("input", { bubbles: true }));
  textarea.dispatchEvent(new Event("change", { bubbles: true }));

  // Visual feedback on button
  const btn = currentWidget?.querySelector(".bis-ai-insert-btn");
  if (btn) {
    const original = btn.textContent;
    btn.textContent = "Inserted ✓";
    btn.style.background = "#16a34a";
    setTimeout(() => {
      btn.textContent = original;
      btn.style.background = "";
    }, 2000);
  }
}

// ─── Textarea Detection & Debounce ─────────────────────────────────────────

const debouncedFetch = debounce(async (text, rect) => {
  if (text.trim().length < MIN_QUERY_LEN) {
    removeWidget();
    return;
  }

  createWidget(rect);
  const data = await fetchRecommendations(text);
  if (data) {
    renderRecommendations(data);
  }
}, DEBOUNCE_MS);

function attachToListeners() {
  // Target textareas and contenteditable elements on procurement portals
  const textareas = document.querySelectorAll("textarea, [contenteditable='true']");

  textareas.forEach((textarea) => {
    // Avoid double-attaching
    if (textarea.dataset.bisAttached) return;
    textarea.dataset.bisAttached = "true";

    textarea.addEventListener("input", function (e) {
      currentTextarea = e.target;
      const text = e.target.value || e.target.innerText || "";
      const rect = e.target.getBoundingClientRect();

      // Adjust position if widget would go off-screen
      const spaceRight = window.innerWidth - rect.right;
      if (spaceRight < 400) {
        // Will be repositioned in createWidget — place to the left
      }

      debouncedFetch(text, rect);
    });

    textarea.addEventListener("focus", function (e) {
      currentTextarea = e.target;
    });
  });
}

// ─── Init: observe DOM for dynamically added textareas ─────────────────────

const observer = new MutationObserver(() => {
  attachToListeners();
});

observer.observe(document.body, { childList: true, subtree: true });

// Initial attachment
attachToListeners();

// Reposition widget on scroll
window.addEventListener("scroll", () => {
  if (currentWidget && currentTextarea) {
    const rect = currentTextarea.getBoundingClientRect();
    currentWidget.style.left = `${rect.left + rect.width + 8}px`;
    currentWidget.style.top = `${rect.top}px`;
  }
});

// Close widget on outside click
document.addEventListener("click", (e) => {
  if (currentWidget && !currentWidget.contains(e.target) && e.target !== currentTextarea) {
    // Small delay to allow textarea click to re-trigger
    setTimeout(() => {
      if (currentWidget && !currentWidget.contains(e.target)) removeWidget();
    }, 200);
  }
});
