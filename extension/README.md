# BIS Standards AI — Chrome Extension

Manifest V3 extension that intercepts textareas on Indian government procurement
portals (GeM, eProcure, CPPP) and provides AI-powered BIS standard recommendations
with one-click compliance clause insertion.

## Files

| File            | Purpose                                              |
|-----------------|------------------------------------------------------|
| `manifest.json` | MV3 config with host permissions for procurement sites |
| `content.js`    | DOM listener, debounced API fetch, widget rendering  |
| `widget.css`    | Floating overlay styles                              |

## How It Works

1. **DOM Listener** — Observes the page for textareas, attaches input listeners
   with 600ms debounce to avoid excessive API calls.
2. **API Fetch** — Sends the textarea content to the FastAPI backend
   (`/api/v1/recommend`) for semantic search + clause synthesis.
3. **Floating Widget** — Renders a dark-themed overlay near the textarea showing
   matching IS codes with QCO/CRS/Fast-Track flags.
4. **One-Click Insert** — Appends the auto-generated compliance clause directly
   into the textarea at the cursor position.

## Installation (Dev)

1. Start the FastAPI backend on `localhost:8000`
2. Open `chrome://extensions`
3. Enable Developer Mode
4. Click "Load unpacked" and select this `extension/` folder
5. Navigate to a procurement portal (e.g., gem.gov.in)
