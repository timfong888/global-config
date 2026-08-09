---
name: google-sheets
description: Create, read, update, and format Google Sheets via the googleapis SDK (OAuth). Activate for "create a spreadsheet", "read this sheet", "update/edit cells or rows", "format this sheet", "research X and save to a sheet", or any spreadsheet automation task.
---

# Google Sheets

Primary mechanism: the **googleapis** Node SDK with OAuth (direct API, no MCP hop). Alternative path: Composio CLI `composio execute GOOGLESHEETS_*` — use when SDK/credential setup isn't available in the sandbox.

## OAuth setup

- Google Cloud project with Sheets API enabled → OAuth client ID (Desktop app) → downloaded as `credentials.json`.
- `npm install googleapis @google-cloud/local-auth`
- **Scope per operation, not one token for everything.** Reads use
  `spreadsheets.readonly`; only mutations request `spreadsheets`, and only after the user approves
  write access for this task. Where the work is confined to files the user picks or this code
  creates, `drive.file` is narrower than either and should be preferred. Keep a separate token file
  per scope set so a read never silently reuses a write-capable token:

  ```javascript
  const SCOPES = {
    read:  ['https://www.googleapis.com/auth/spreadsheets.readonly'],
    write: ['https://www.googleapis.com/auth/spreadsheets'],
    file:  ['https://www.googleapis.com/auth/drive.file'],
  };
  ```

- Default `CREDENTIALS_PATH`/`TOKEN_PATH` to `${XDG_CONFIG_HOME:-$HOME/.config}/gsheets/credentials.json` and `.../gsheets/token.json` — outside the project tree, so "never commit" isn't the only thing standing between these files and getting packaged or shared by accident. Create the dir with `mkdir -p -m 700` and write both files `chmod 600`. Use a project-local path only if the user explicitly confirms they want it there, and still gitignore it. First run opens a browser for consent and writes `token.json`; every run after that reuses it (googleapis auto-refreshes). Reuse one `auth.js` module per project:

```javascript
const { authenticate } = require('@google-cloud/local-auth');
const { google } = require('googleapis');

// mode: 'read' | 'write' | 'file'. Token path is per-mode, so a read cannot pick up
// a write-capable token that an earlier mutation happened to leave behind.
async function authorize(mode = 'read') {
  let client = await loadSavedCredentialsIfExist(mode); // reads TOKEN_PATH(mode), google.auth.fromJSON(...)
  if (client) return client;
  client = await authenticate({ scopes: SCOPES[mode], keyfilePath: CREDENTIALS_PATH });
  if (client.credentials) await saveCredentials(client, mode); // writes refresh_token to TOKEN_PATH(mode)
  return client;
}
```

## Operations

```javascript
// Read
const ro = google.sheets({ version: 'v4', auth: await authorize('read') });
const { data } = await ro.spreadsheets.values.get({ spreadsheetId, range: 'Sheet1!A1:E100' });
// data.values -> array of row arrays; trailing empty cells are omitted, not padded

// Everything below mutates, so it needs the write scope — confirm with the user first.
const sheets = google.sheets({ version: 'v4', auth: await authorize('write') });

// Overwrite a range
await sheets.spreadsheets.values.update({
  spreadsheetId, range, valueInputOption: 'RAW', // 'USER_ENTERED' to evaluate formulas/dates as typed
  requestBody: { values },
});

// Append rows after the last used row in range
await sheets.spreadsheets.values.append({
  spreadsheetId, range, valueInputOption: 'USER_ENTERED', requestBody: { values },
});

// Create
const sp = await sheets.spreadsheets.create({
  requestBody: { properties: { title }, sheets: [{ properties: { title: 'Sheet1' } }] },
});
// sp.data.spreadsheetId, sp.data.spreadsheetUrl

// Formatting / structural ops go through batchUpdate and need the numeric sheetId, NOT the sheet
// name — so resolve it first. A missing tab yields undefined, which the API rejects with an
// unhelpful error; fail loudly here instead.
const meta = await sheets.spreadsheets.get({ spreadsheetId });
const sheetId = meta.data.sheets.find(s => s.properties.title === sheetName)?.properties.sheetId;
if (sheetId === undefined) throw new Error(`No sheet named "${sheetName}" in ${spreadsheetId}`);

await sheets.spreadsheets.batchUpdate({
  spreadsheetId,
  requestBody: { requests: [
    { repeatCell: {
        range: { sheetId, startRowIndex: 0, endRowIndex: 1 },
        cell: { userEnteredFormat: { textFormat: { bold: true }, backgroundColor: { red: 0.9, green: 0.9, blue: 0.9 } } },
        fields: 'userEnteredFormat(textFormat,backgroundColor)',
    }},
    { updateDimensionProperties: {
        range: { sheetId, dimension: 'COLUMNS', startIndex: 0, endIndex: 1 },
        properties: { pixelSize: 200 }, fields: 'pixelSize',
    }},
  ]},
});
```

## Conventions

- A1 ranges: `Sheet1!A1:Z100`; whole sheet `Sheet1` or `Sheet1!A:Z`.
- Before calling `spreadsheets.create` for a new layout, show an ASCII table preview and get approval — don't build a layout nobody asked for.
- Group related writes/formats into one `batchUpdate` call rather than looping single-cell calls.
- Quota is per-project and per-user, not a single global number — check the actual limit in Cloud Console → APIs & Services → Sheets API → Quotas rather than assuming a fixed rate.

| Symptom | Fix |
|---|---|
| `credentials.json not found` | Re-download the OAuth client JSON from Cloud Console |
| `token.json not found` | Normal on first run — browser opens for consent |
| `invalid_grant` / invalid credentials | Delete `token.json`, re-authenticate |
| `429` / rate limit exceeded | Exponential backoff with jitter (e.g. 1s, then double each retry, cap ~60s) — don't just add a fixed delay |

## Research-then-store pattern

When asked to research a topic and save results: run the research with whatever web-research tool is available, and structure findings into a consistent row shape that includes a stable dedup key (e.g. URL, or topic+date). Read the target sheet first and check for that key, but treat the read as a best-effort check, not a guarantee — a retry or a concurrent run can still race past it. Prefer `values.update` against the range for that key (overwrite in place) over a blind `values.append`; if you must append, re-check for the key immediately before writing and skip if it's already present. Return the spreadsheet URL. Spot-check AI-sourced data before treating it as final.

## Finding a spreadsheet

Ask for the URL or ID rather than guessing. The ID is the path segment between `/d/` and `/edit`
in a Sheets URL.

A catalog of FilOz spreadsheet IDs lives in the vault at
`02-AI-Tools/skills/retired-skills/filoz-google-sheets/`. It is deliberately not reproduced here:
the IDs belong to a different org's Drive, have not been re-confirmed since capture, and a stale
ID in a globally-loaded skill sends the agent to the wrong document silently.
