---
name: google-sheets
description: Create, read, update, and format Google Sheets via the googleapis SDK (OAuth). Activate for "create a spreadsheet", "read this sheet", "update/edit cells or rows", "format this sheet", "research X and save to a sheet", or any spreadsheet automation task.
---

# Google Sheets

Primary mechanism: the **googleapis** Node SDK with OAuth (direct API, no MCP hop). Alternative path: Composio CLI `composio execute GOOGLESHEETS_*` — use when SDK/credential setup isn't available in the sandbox.

## OAuth setup

- Google Cloud project with Sheets API enabled → OAuth client ID (Desktop app) → downloaded as `credentials.json`.
- `npm install googleapis @google-cloud/local-auth`
- Conventions used by the auth module: `SCOPES = ['https://www.googleapis.com/auth/spreadsheets']`; `CREDENTIALS_PATH` = `credentials.json` in the project's cwd; `TOKEN_PATH` = `token.json` in the project's cwd. First run opens a browser for consent and writes `token.json`; every run after that reuses it (googleapis auto-refreshes). Never commit either file. Reuse one `auth.js` module per project:

```javascript
const { authenticate } = require('@google-cloud/local-auth');
const { google } = require('googleapis');

async function authorize() {
  let client = await loadSavedCredentialsIfExist(); // reads TOKEN_PATH, google.auth.fromJSON(...)
  if (client) return client;
  client = await authenticate({ scopes: SCOPES, keyfilePath: CREDENTIALS_PATH });
  if (client.credentials) await saveCredentials(client); // writes refresh_token to TOKEN_PATH
  return client;
}
```

## Operations

```javascript
const sheets = google.sheets({ version: 'v4', auth: await authorize() });

// Read
const { data } = await sheets.spreadsheets.values.get({ spreadsheetId, range: 'Sheet1!A1:E100' });
// data.values -> array of row arrays; trailing empty cells are omitted, not padded

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

// Formatting / structural ops go through batchUpdate and need the numeric sheetId, NOT the sheet name
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

// Look up sheetId (int) by tab name
const meta = await sheets.spreadsheets.get({ spreadsheetId });
const sheetId = meta.data.sheets.find(s => s.properties.title === sheetName)?.properties.sheetId;
```

## Conventions

- A1 ranges: `Sheet1!A1:Z100`; whole sheet `Sheet1` or `Sheet1!A:Z`.
- Before calling `spreadsheets.create` for a new layout, show an ASCII table preview and get approval — don't build a layout nobody asked for.
- Group related writes/formats into one `batchUpdate` call rather than looping single-cell calls.
- Rate limit: 300 requests/min.

| Symptom | Fix |
|---|---|
| `credentials.json not found` | Re-download the OAuth client JSON from Cloud Console |
| `token.json not found` | Normal on first run — browser opens for consent |
| `invalid_grant` / invalid credentials | Delete `token.json`, re-authenticate |
| Rate limit exceeded | Batch calls; add delay between loop iterations |

## Research-then-store pattern

When asked to research a topic and save results: run the research with whatever web-research tool is available, structure findings into a consistent row shape before writing, read the target sheet first to avoid duplicate entries, then `values.append` (new rows) or `values.update` (overwrite). Return the spreadsheet URL. Spot-check AI-sourced data before treating it as final.

## Finding a spreadsheet

Ask for the URL or ID rather than guessing. The ID is the path segment between `/d/` and `/edit`
in a Sheets URL.

A catalog of FilOz spreadsheet IDs lives in the vault at
`02-AI-Tools/skills/retired-skills/filoz-google-sheets/`. It is deliberately not reproduced here:
the IDs belong to a different org's Drive, have not been re-confirmed since capture, and a stale
ID in a globally-loaded skill sends the agent to the wrong document silently.
