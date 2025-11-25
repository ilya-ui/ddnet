# LMArena Gemini Proxy

This project exposes an OpenAI-compatible HTTP API that forwards requests to the
[`canary.lmarena.ai`](https://lmarena.ai/) backend so you can access the
**Gemini 2.5 Pro** model from your own infrastructure.
The service replicates the `/v1/chat/completions` and `/v1/models` endpoints and
supports both standard and streaming responses.

## Features

- ✅ OpenAI-compatible `/v1/chat/completions` endpoint (non-stream + SSE stream)
- ✅ `/v1/models` endpoint returning the available Gemini aliases
- ✅ Cookie rotation with automatic banning of exhausted/invalid cookies
- ✅ Optional bearer-token protection for your private deployment
- ✅ Cloudflare-compatible HTTP stack built on top of `curl_cffi`

## Prerequisites

You need:

- A Cloudflare `cf_clearance` token for `canary.lmarena.ai`
- One or more valid `arena-auth-prod-v1` cookies gathered from the site
- Python 3.11+ (the tooling here uses `curl_cffi` which mirrors curl 8.x)

Install dependencies (Windows PowerShell/CMD):

```bash
py -m pip install fastapi==0.115.2 uvicorn[standard]==0.32.0 curl_cffi==0.7.4 python-dotenv==1.0.1
```

Or equivalently on Unix-like systems:

```bash
python3 -m pip install -r requirements.txt
```

### Windows quick start

You can also double-click `run_proxy.bat`. The batch script will:

1. Install/upgrade the required packages via `py -m pip install -r requirements.txt`
2. Expose the `src` directory on `PYTHONPATH` automatically
3. Launch the proxy using `py -m lmarena_proxy.main`
4. Keep the console window open so you can review any errors

The script runs from the repository root and shows the exit code when the proxy stops.

## Configuration

Create a `.env` file (or export variables) with at least the following keys:

```env
CF_CLEARANCE=cf_clearance_token_here
ARENA_AUTH_COOKIES=cookie1,cookie2,cookie3
# Optional parameters
API_AUTH_SECRET=your-private-bearer-token
PROXY_URL=socks5://127.0.0.1:1080
ARENA_BASE_URL=https://canary.lmarena.ai
ARENA_TIMEOUT_SECONDS=120
CURL_IMPERSONATE=chrome137
```

- **CF_CLEARANCE** – Cloudflare challenge token for `lmarena.ai`
- **ARENA_AUTH_COOKIES** – Comma-separated list of `arena-auth-prod-v1` cookies
- **API_AUTH_SECRET** – If set, every request must send `Authorization: Bearer <secret>`
- **PROXY_URL** – Optional HTTP/SOCKS proxy used for outbound requests

## Running the proxy

```bash
python -m lmarena_proxy.main
```

The service listens on `0.0.0.0:8000` by default. Override via `HOST`/`PORT`/`UVICORN_WORKERS` env vars.

## Example usage

```bash
curl -N \
  -H "Authorization: Bearer your-private-bearer-token" \
  -H "Content-Type: application/json" \
  -d '{
        "model": "gemini-2.5-pro",
        "stream": true,
        "messages": [
          {"role": "user", "content": "Привет! Расскажи о Gemini"}
        ]
      }' \
  http://localhost:8000/v1/chat/completions
```

The response stream mirrors the OpenAI Chat Completions SSE format.

## Notes

- Each cookie is automatically rotated and banned once the remote service flags
  it as exhausted, rate-limited or invalid.
- The project intentionally supports only Gemini 2.5 Pro. Extend the
  `MODEL_REGISTRY` map in `lmarena_proxy/arena_client.py` to add more models.
- Respect LMArena's terms of service when using this bridge.
