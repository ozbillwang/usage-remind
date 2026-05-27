# Usage Remind

A tiny local web service for checking coding assistant usage windows.

Right now it supports Codex usage only. The service is intentionally small so it can later grow provider adapters for Claude Code, Gemini, Grok, and others.

This service is pretty useful for setting `/goal` in Codex when you want to keep your AI agent running while avoiding running out of usage.

<img width="765" height="479" alt="image" src="https://github.com/user-attachments/assets/84f9bbb1-5d1d-488e-aa8f-ab246ca00b1a" />

## What It Shows

The page shows:

- Codex 5-hour usage remaining
- Codex weekly usage remaining
- reset time for each window
- current plan type
- last refresh time

The page refreshes automatically every 5 seconds. The Refresh button does the same check immediately.

## Run

```bash
git clone https://github.com/ozbillwang/usage-remind.git
cd usage-remind
python3 server.py
```

Open http://127.0.0.1:8765

API:

```text
http://127.0.0.1:8765/api/usage
```

You can run the command from any working directory because `server.py` is self-contained and does not depend on nearby static files.

## Run From GitHub

The shortest command is:

```bash
curl -fsSL https://raw.githubusercontent.com/ozbillwang/usage-remind/main/server.sh | sh
```

That script downloads `server.py` into:

```text
~/.usage-remind/server.py
```

Then it starts the local service with `python3`.

The script runs the service in the background, writes the process id to:

```text
~/.usage-remind/server.pid
```

Note: Only run the `curl | sh` version from a repository you trust, because it executes downloaded code on your machine.



## API Shape

`GET /api/usage` returns JSON like:

```json
{
  "provider": "codex",
  "fetchedAt": "2026-05-27T11:54:09.241661+10:00",
  "planType": "plus",
  "rateLimitName": null,
  "allowed": true,
  "limitReached": false,
  "windows": [
    {
      "window": "5h",
      "remainingPercent": 58,
      "usedPercent": 42.0,
      "resetAt": {
        "epoch": 1779862668,
        "iso": "2026-05-27T16:17:48+10:00",
        "label": "2026-05-27 04:17 PM AEST"
      },
      "windowSeconds": 18000
    }
  ],
  "additionalRateLimits": []
}
```

The API intentionally does not return Codex credits because that value is not useful for this dashboard.

## How Codex Auth Works

The service reads the Codex/ChatGPT access token from:

```text
~/.codex/auth.json
```

That file is created by Codex after you sign in. The local service uses the token from that file to call:

```text
https://chatgpt.com/backend-api/wham/usage
```

Then it transforms the response into the simpler `/api/usage` JSON.

## Do I Need To Run The Codex UI First?

Usually, no.

You do not need the Codex UI open while this service runs, as long as `~/.codex/auth.json` already exists and contains a valid access token.

You do need to sign in to Codex at least once before using this service. If the token expires or the file is missing, open Codex and sign in again, then restart or refresh this service.

## Troubleshooting

If the page says usage is unavailable, check the API directly:

```bash
curl http://127.0.0.1:8765/api/usage
```

Common causes:

- Codex is not signed in yet
- `~/.codex/auth.json` is missing
- the saved access token expired
- port `8765` is already in use

If port `8765` is already in use, stop the older service first:

```bash
lsof -ti tcp:8765
kill <PID>
```

If you started it with `server.sh`, you can stop it with:

```bash
kill "$(cat ~/.usage-remind/server.pid)"
```
