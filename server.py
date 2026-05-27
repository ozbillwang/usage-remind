#!/usr/bin/env python3
import datetime as dt
import json
import pathlib
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
import zoneinfo


CODEX_AUTH = pathlib.Path.home() / ".codex" / "auth.json"
CODEX_USAGE_URL = "https://chatgpt.com/backend-api/wham/usage"
TIMEZONE = "Australia/Sydney"
HOST = "127.0.0.1"
PORT = 8765


INDEX_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Usage Remind</title>
    <link rel="stylesheet" href="/styles.css">
  </head>
  <body>
    <main class="shell">
      <header class="app-header">
        <div>
          <p class="eyebrow">Usage Remind</p>
          <h1>Codex usage</h1>
        </div>
        <span class="provider-pill">Codex</span>
      </header>

      <section class="dashboard" aria-label="Usage dashboard">
        <aside class="panel usage-panel">
          <div class="panel-heading">
            <h2>Usage Remaining</h2>
            <button id="copy-check" class="icon-button" title="Copy usage summary" aria-label="Copy usage summary">
              <span aria-hidden="true">⌘</span>
            </button>
          </div>
          <dl class="facts">
            <div class="usage-window">
              <dt>5h</dt>
              <dd><span id="usage-5h" class="usage-number">-</span> remaining</dd>
              <dd id="usage-5h-reset" class="reset-copy">Reset time unavailable</dd>
            </div>
            <div class="usage-window">
              <dt>Weekly</dt>
              <dd><span id="usage-weekly" class="usage-number">-</span> remaining</dd>
              <dd id="usage-weekly-reset" class="reset-copy">Reset time unavailable</dd>
            </div>
            <div class="plan-row">
              <dt>Plan</dt>
              <dd id="usage-plan">-</dd>
            </div>
          </dl>
          <div class="usage-actions">
            <button id="refresh-usage" class="ghost-button">Refresh</button>
            <span id="usage-updated" class="note">Not updated yet</span>
          </div>
        </aside>

        <div class="side-stack">
          <div class="status-card">
            <span class="pulse" aria-hidden="true"></span>
            <div>
              <strong id="usage-status-title">Usage loading</strong>
              <p id="usage-status-copy">Fetching usage from the local service.</p>
            </div>
          </div>
          <div class="metric-card">
            <span>Refresh</span>
            <strong>5s</strong>
          </div>
        </div>
      </section>
    </main>
    <script src="/app.js?v=20260527-standalone"></script>
  </body>
</html>
"""


STYLES_CSS = """:root {
  color-scheme: light;
  --ink: #182230;
  --muted: #667085;
  --line: #d7e0e5;
  --paper: #f6faf9;
  --panel: #ffffff;
  --teal: #006d77;
  --teal-ink: #034b52;
  --teal-soft: #e4f4f2;
  --rose: #b4234a;
  --green: #18794e;
  --shadow: 0 22px 60px rgba(24, 34, 48, 0.11);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-height: 100vh;
  background:
    linear-gradient(135deg, rgba(0, 109, 119, 0.12), transparent 34%),
    linear-gradient(315deg, rgba(180, 35, 74, 0.08), transparent 38%),
    var(--paper);
  color: var(--ink);
}

button {
  font: inherit;
}

.shell {
  width: min(860px, calc(100% - 40px));
  margin: 0 auto;
  padding: 42px 0;
}

.app-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
}

.eyebrow {
  margin: 0 0 8px;
  color: var(--teal);
  font-size: 0.78rem;
  font-weight: 850;
  letter-spacing: 0;
  text-transform: uppercase;
}

h1,
h2,
p {
  margin-top: 0;
}

h1 {
  margin-bottom: 0;
  font-size: clamp(2.2rem, 6vw, 4.1rem);
  line-height: 0.98;
  letter-spacing: 0;
}

h2 {
  margin-bottom: 0;
  font-size: 1rem;
}

.provider-pill {
  display: inline-flex;
  align-items: center;
  min-height: 36px;
  padding: 0 14px;
  border: 1px solid rgba(0, 109, 119, 0.22);
  border-radius: 999px;
  background: var(--teal-soft);
  color: var(--teal-ink);
  font-weight: 850;
}

.dashboard {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 18px;
  align-items: start;
}

.status-card,
.metric-card,
.panel {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: var(--shadow);
}

.panel {
  padding: 22px;
}

.usage-panel {
  min-height: 360px;
}

.side-stack {
  display: grid;
  gap: 14px;
}

.status-card {
  display: flex;
  gap: 14px;
  align-items: center;
  min-height: 104px;
  padding: 18px;
}

.metric-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 74px;
  padding: 18px;
}

.metric-card span,
.status-card p,
.note,
.facts dd {
  color: var(--muted);
}

.metric-card strong {
  color: var(--ink);
  font-size: 1.55rem;
  line-height: 1;
}

.status-card p {
  margin: 4px 0 0;
  font-size: 0.92rem;
  line-height: 1.35;
}

.pulse {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 0 8px rgba(24, 121, 78, 0.12);
  flex: 0 0 auto;
}

.panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 18px;
}

.facts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin: 0;
}

.facts div {
  min-height: 132px;
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fbfdfc;
}

.facts .plan-row {
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 70px;
}

.facts dt {
  margin-bottom: 10px;
  color: var(--ink);
  font-weight: 850;
}

.facts dd {
  margin: 0;
  font-size: 0.93rem;
}

.plan-row dt {
  margin-bottom: 0;
}

.plan-row dd {
  color: var(--ink);
  font-weight: 850;
}

.usage-number {
  color: var(--ink);
  font-size: 2.6rem;
  font-weight: 850;
  line-height: 0.9;
}

.reset-copy {
  margin-top: 8px !important;
  font-size: 0.82rem !important;
}

.usage-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-top: 18px;
}

.note {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.45;
}

.icon-button,
.ghost-button {
  min-height: 38px;
  border: 0;
  border-radius: 8px;
  background: #edf5f4;
  color: var(--ink);
  cursor: pointer;
  font-weight: 850;
}

.icon-button {
  width: 38px;
}

.ghost-button {
  padding: 0 16px;
}

.ghost-button:hover,
.icon-button:hover {
  background: #dff0ee;
}

button:focus-visible {
  outline: 3px solid rgba(0, 109, 119, 0.28);
  outline-offset: 2px;
}

button:disabled {
  cursor: wait;
  opacity: 0.7;
}

@media (max-width: 820px) {
  .app-header,
  .dashboard {
    grid-template-columns: 1fr;
  }

  .app-header {
    align-items: start;
    flex-direction: column;
  }

  .side-stack {
    grid-template-columns: 1fr 160px;
  }
}

@media (max-width: 620px) {
  .shell {
    width: min(100% - 20px, 860px);
    padding: 24px 0;
  }

  .facts,
  .side-stack {
    grid-template-columns: 1fr;
  }

  .usage-actions {
    align-items: flex-start;
    flex-direction: column;
  }
}
"""


APP_JS = """const els = {
  copyCheck: document.querySelector("#copy-check"),
  refreshUsage: document.querySelector("#refresh-usage"),
  usageStatusTitle: document.querySelector("#usage-status-title"),
  usageStatusCopy: document.querySelector("#usage-status-copy"),
  usage5h: document.querySelector("#usage-5h"),
  usage5hReset: document.querySelector("#usage-5h-reset"),
  usageWeekly: document.querySelector("#usage-weekly"),
  usageWeeklyReset: document.querySelector("#usage-weekly-reset"),
  usagePlan: document.querySelector("#usage-plan"),
  usageUpdated: document.querySelector("#usage-updated")
};

const usageRefreshMs = 5_000;
const usageEndpoints = [
  "/api/usage",
  "http://127.0.0.1:8765/api/usage"
];
let latestUsage = null;
let usageRefreshInFlight = false;

refreshUsage();
setInterval(refreshUsage, usageRefreshMs);
els.refreshUsage.addEventListener("click", refreshUsage);

els.copyCheck.addEventListener("click", () => {
  const status = latestUsage ? usageText(latestUsage) : "Codex usage has not loaded yet.";
  copy(status, els.copyCheck, "Copied");
});

async function refreshUsage() {
  if (usageRefreshInFlight) return;
  usageRefreshInFlight = true;
  els.refreshUsage.disabled = true;
  els.usageStatusTitle.textContent = "Usage refreshing";
  els.usageStatusCopy.textContent = "Checking the local usage API.";
  try {
    const data = await fetchUsage();
    latestUsage = data;
    renderUsage(data);
  } catch (error) {
    els.usageStatusTitle.textContent = "Usage unavailable";
    els.usageStatusCopy.textContent = error.message || "The local usage API did not return data.";
    els.usageUpdated.textContent = `Refresh failed: ${shortError(error)}`;
  } finally {
    usageRefreshInFlight = false;
    els.refreshUsage.disabled = false;
  }
}

async function fetchUsage() {
  const errors = [];
  for (const endpoint of usageEndpoints) {
    try {
      const response = await fetch(endpoint, {
        cache: "no-store",
        headers: { "Accept": "application/json" }
      });
      const text = await response.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        throw new Error(`Usage API returned non-JSON from ${endpoint}`);
      }
      if (!response.ok) {
        throw new Error(data.error || `Usage API returned ${response.status} from ${endpoint}`);
      }
      if (!Array.isArray(data.windows)) {
        throw new Error(`Usage API response is missing windows from ${endpoint}`);
      }
      return data;
    } catch (error) {
      errors.push(error.message || String(error));
    }
  }
  throw new Error(errors.join(" | "));
}

function renderUsage(data) {
  const windows = Array.isArray(data.windows) ? data.windows : [];
  const fiveHour = windows.find((item) => item.window === "5h");
  const weekly = windows.find((item) => item.window === "Weekly");
  renderWindow(fiveHour, els.usage5h, els.usage5hReset);
  renderWindow(weekly, els.usageWeekly, els.usageWeeklyReset);
  els.usagePlan.textContent = data.planType || "-";
  els.usageStatusTitle.textContent = data.allowed ? "Usage available" : "Usage blocked";
  els.usageStatusCopy.textContent = data.allowed
    ? "Codex can still run in the current account window."
    : "The current Codex usage window is exhausted.";
  els.usageUpdated.textContent = `Updated ${formatUpdated(data.fetchedAt)}`;
}

function renderWindow(window, valueEl, resetEl) {
  if (!window) {
    valueEl.textContent = "-";
    resetEl.textContent = "Reset time unavailable";
    return;
  }
  valueEl.textContent = `${window.remainingPercent}%`;
  resetEl.textContent = window.resetAt?.label ? `Resets ${window.resetAt.label}` : "Reset time unavailable";
}

function formatUpdated(iso) {
  if (!iso) return "just now";
  return new Date(iso).toLocaleTimeString([], { hour: "numeric", minute: "2-digit", second: "2-digit" });
}

function usageText(data) {
  const lines = [
    "Codex usage remaining",
    `Plan: ${data.planType || "-"}`,
    `Allowed: ${data.allowed}`
  ];
  for (const window of data.windows || []) {
    lines.push(`${window.window}: ${window.remainingPercent}% remaining, resets ${window.resetAt?.label || "-"}`);
  }
  return lines.join("\\n");
}

function shortError(error) {
  const message = error.message || String(error);
  return message.length > 80 ? `${message.slice(0, 77)}...` : message;
}

async function copy(text, button, label) {
  await navigator.clipboard.writeText(text);
  const original = button.textContent;
  button.textContent = label;
  setTimeout(() => {
    button.textContent = original;
  }, 1300);
}
"""


def codex_access_token():
    if not CODEX_AUTH.exists():
        raise RuntimeError("No ~/.codex/auth.json file found. Sign in to Codex first.")
    data = json.loads(CODEX_AUTH.read_text())
    return data.get("access_token") or data.get("tokens", {}).get("access_token")


def fetch_codex_usage():
    token = codex_access_token()
    if not token:
        raise RuntimeError("No Codex ChatGPT access token found in ~/.codex/auth.json")
    request = urllib.request.Request(
        CODEX_USAGE_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "usage-remind-local",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def close(value, target):
    return abs(value - target) <= target * 0.05


def window_label(seconds):
    minutes = (seconds or 0) / 60
    if close(minutes, 300):
        return "5h"
    if close(minutes, 10080):
        return "Weekly"
    if close(minutes, 1440):
        return "Daily"
    if close(minutes, 43200):
        return "Monthly"
    return f"{round(minutes)}m"


def format_reset(epoch_seconds):
    if not epoch_seconds:
        return None
    timezone = zoneinfo.ZoneInfo(TIMEZONE)
    reset = dt.datetime.fromtimestamp(epoch_seconds, timezone)
    return {
        "epoch": epoch_seconds,
        "iso": reset.isoformat(),
        "label": reset.strftime("%Y-%m-%d %I:%M %p %Z"),
    }


def usage_window(window):
    used = float(window.get("used_percent") or 0)
    remaining = max(0, min(100, 100 - used))
    return {
        "window": window_label(window.get("limit_window_seconds")),
        "remainingPercent": round(remaining),
        "usedPercent": used,
        "resetAt": format_reset(window.get("reset_at")),
        "windowSeconds": window.get("limit_window_seconds"),
    }


def transform_codex_usage(payload):
    rate_limit = payload.get("rate_limit") or {}
    windows = []
    for key in ("primary_window", "secondary_window"):
        window = rate_limit.get(key)
        if window:
            windows.append(usage_window(window))

    additional = []
    for item in payload.get("additional_rate_limits") or []:
        item_windows = []
        item_rate_limit = item.get("rate_limit") or {}
        for key in ("primary_window", "secondary_window"):
            window = item_rate_limit.get(key)
            if window:
                item_windows.append(usage_window(window))
        additional.append({
            "limitName": item.get("limit_name"),
            "windows": item_windows,
            "allowed": item_rate_limit.get("allowed"),
            "limitReached": item_rate_limit.get("limit_reached"),
        })

    return {
        "provider": "codex",
        "fetchedAt": dt.datetime.now(zoneinfo.ZoneInfo(TIMEZONE)).isoformat(),
        "planType": payload.get("plan_type"),
        "rateLimitName": payload.get("rate_limit_name"),
        "allowed": rate_limit.get("allowed"),
        "limitReached": rate_limit.get("limit_reached"),
        "windows": windows,
        "additionalRateLimits": additional,
    }


def current_usage():
    return transform_codex_usage(fetch_codex_usage())


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/usage":
            self.send_usage()
            return
        if parsed.path in ("", "/"):
            self.send_text(INDEX_HTML, "text/html; charset=utf-8")
            return
        if parsed.path == "/styles.css":
            self.send_text(STYLES_CSS, "text/css; charset=utf-8")
            return
        if parsed.path == "/app.js":
            self.send_text(APP_JS, "application/javascript; charset=utf-8")
            return
        self.send_error(404)

    def do_HEAD(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/usage":
            self.send_headers(200, "application/json; charset=utf-8", 0)
            return
        if parsed.path in ("", "/"):
            self.send_headers(200, "text/html; charset=utf-8", len(INDEX_HTML.encode("utf-8")))
            return
        if parsed.path == "/styles.css":
            self.send_headers(200, "text/css; charset=utf-8", len(STYLES_CSS.encode("utf-8")))
            return
        if parsed.path == "/app.js":
            self.send_headers(200, "application/javascript; charset=utf-8", len(APP_JS.encode("utf-8")))
            return
        self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def send_usage(self):
        try:
            body = json.dumps(current_usage(), indent=2).encode("utf-8")
            status = 200
        except urllib.error.HTTPError as error:
            body = json.dumps({"error": f"HTTP {error.code} from Codex usage endpoint"}).encode("utf-8")
            status = 502
        except Exception as error:
            body = json.dumps({"error": str(error)}).encode("utf-8")
            status = 500
        self.send_headers(status, "application/json; charset=utf-8", len(body), no_store=True)
        self.wfile.write(body)

    def send_text(self, text, content_type):
        body = text.encode("utf-8")
        self.send_headers(200, content_type, len(body))
        self.wfile.write(body)

    def send_headers(self, status, content_type, content_length, no_store=False):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(content_length))
        if no_store:
            self.send_header("Cache-Control", "no-store")
        self.send_cors_headers()
        self.end_headers()

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Accept, Content-Type")

    def log_message(self, format, *args):
        pass


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Usage Remind running at http://{HOST}:{PORT}")
    print(f"Usage API: http://{HOST}:{PORT}/api/usage")
    server.serve_forever()


if __name__ == "__main__":
    main()
