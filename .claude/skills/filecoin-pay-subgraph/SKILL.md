---
name: filecoin-pay-subgraph
description: Query the Filecoin Pay Goldsky subgraph for rails, settlements, operators, accounts, and daily/token metrics. Activate when user asks about Filecoin Pay rails, settlements, operators, accounts, WBR/weekly metrics, or token volumes.
---

# Filecoin Pay Subgraph

## Endpoint

**Resolve the current endpoint from the Goldsky dashboard before querying — do not paste a URL
from memory.** As of 2026-07-31 every historical endpoint below returns
`{"statusCode":404,"message":"Subgraph not found..."}`, so this list is provenance, not a
working address:

```text
# last known production — 404s as of 2026-07-31, verify before use
https://api.goldsky.com/api/public/project_cmb9tuo8r1xdw01ykb8uidk7h/subgraphs/filecoin-pay-mainnet/1.0.6/gn
```

- **v1.0.6** was the long-standing known-good production version and is still the version cited
  across Tim's notes; every other subgraph under the same project now 404s too, which points at
  a project-level rotation rather than one bad deploy.
- **v1.2.0** (`filecoin-pay-mainnet-tim`) was **permanently broken** even while live —
  deterministic mapping error at block 5,810,264; needs a code fix + redeploy.
- The **old project** `project_cmj7soo5uf4no01xw0tij21a1` was deleted.

Smoke-test any candidate endpoint before building on it. Plain `curl -s` exits 0 on a 404/500 body too, so a bare response reads as success — check for a real `data` field and fail loudly otherwise:

```bash
set -euo pipefail
response=$(curl --fail-with-body --silent --show-error \
  -X POST "$ENDPOINT" -H "Content-Type: application/json" \
  -d '{"query":"{ _meta { block { number } } }"}')
jq -e '((.errors // []) | length) == 0 and has("data")' <<<"$response" >/dev/null \
  && echo "endpoint OK" \
  || { echo "endpoint smoke test FAILED: $response" >&2; exit 1; }
```

Query with POST:

```bash
curl -s -X POST "$ENDPOINT" -H "Content-Type: application/json" \
  -d '{"query": "{ paymentsMetrics(first: 1) { totalRails totalActiveRails totalAccounts uniquePayers uniquePayees } }"}' | jq
```

## Known traps

- **Raw token amounts are integers scaled by the token's own precision** — divide by `10^token.decimals`, not a hardcoded `10^18`. `tokens { decimals }` is queryable (see Operators / tokens below) — fetch it per token before scaling amounts. FIL and USDFC both happen to use 18 decimals today, but confirm that per token rather than assuming it.
- **Never sum `account.payerRails[].totalSettledAmount`** to get a per-account settled figure — it inflates ~6x. Rail IDs (e.g. `0x0e02`, `0x0e03`, `0x0e04`) are sub-components of one settlement slot (payee / network fee / operator commission); a single Settlement event credits multiple rail rows, so summing double/triple-counts. Verified example: naive sum gave $15.70 vs. the true $2.63 (~6x inflation).
  - Correct source for a single account: `https://filecoin-pay-console.vercel.app/payer-accounts/?address=0x...`.
  - Programmatic alternative: sum `Settlement.totalNetPayeeAmount` filtered by the rail's payer, not `Rail.totalSettledAmount`.
  - For protocol-wide totals, `Token.totalSettledAmount` + `Token.totalOneTimePayment` is correct — only the rail-level sum is broken.
- **No per-token weekly entity.** `weeklyMetrics` exists at the protocol level, but there is no `weeklyTokenMetrics`. For a per-token weekly/WBR number, query `dailyTokenMetrics` over the date range and sum daily into weekly yourself.
- BigInt fields come back as strings; addresses are hex `Bytes` strings.

## Entities

| Entity | Description |
|---|---|
| `Account` | User accounts with rails and token balances |
| `Operator` | Service operators managing rails |
| `Rail` | Payment rails (streaming payments) |
| `Settlement` | Settlement events on rails |
| `Token` | Supported payment tokens |
| `UserToken` | User's token balances and lockups |
| `OperatorApproval` | Client approvals for operators |
| `OperatorToken` | Operator's token metrics |
| `PaymentsMetric` | Global aggregate metrics |
| `DailyMetric` / `WeeklyMetric` | Protocol-level daily/weekly aggregates |
| `DailyTokenMetric` | Daily metrics per token (no weekly equivalent — see traps) |
| `DailyOperatorMetric` | Daily metrics per operator |

## Example queries

Unless stated otherwise, the `first: N` queries below return a bounded top-N sample in the order shown — not an exhaustive list. To enumerate every matching entity, add cursor pagination (loop on `first`/`skip`, or `where: { id_gt: "<last id>" }`) until a page returns fewer rows than `first`.

Daily metrics, last 7 days:

```graphql
{
  dailyMetrics(first: 7, orderBy: timestamp, orderDirection: desc) {
    date timestamp filBurned railsCreated totalRailSettlements
    railsTerminated railsFinalized activeRailsCount
    uniquePayers uniquePayees uniqueOperators uniqueAccounts
  }
}
```

Daily token metrics (sum these into weekly for WBR — no weekly per-token entity). `first: N` caps *total* rows across all tokens, not rows per token — with more than 4 tokens, `first: 28` cannot return a full 7 days for every token. Bound by an explicit timestamp range and paginate with a stable cursor before summing:

```graphql
{
  dailyTokenMetrics(
    where: { timestamp_gte: "<week_start_unix>", timestamp_lt: "<week_end_unix>" }
    first: 1000
    orderBy: timestamp
    orderDirection: asc
  ) {
    id date timestamp volume deposit withdrawal settledAmount commissionPaid
    activeRailsCount uniqueHolders totalLocked
    token { symbol }
  }
}
```

If a page returns exactly `first` rows, it may be incomplete — page forward with a cursor that matches the sort key, not `id_gt`. This query sorts `orderBy: timestamp, orderDirection: asc`, and `id` is not guaranteed monotonic with `timestamp`; cursoring on `id_gt` under a timestamp-ordered query can skip or repeat rows relative to that order. Pair an ascending timestamp cursor with the ascending sort instead: `where: { timestamp_gte: "<week_start_unix>", timestamp_lt: "<week_end_unix>", timestamp_gt: "<last row's timestamp>" }`, using the previous page's last row `timestamp` as the cursor, and keep summing until a page returns fewer rows than `first`. If multiple rows can share the exact same timestamp, add `id_gt: "<last row's id>"` scoped to that timestamp only (`timestamp: "<last row's timestamp>", id_gt: "<last row's id>"`, OR'd with the `timestamp_gt` branch above) so same-timestamp ties aren't silently dropped.

Active rails (sample, not exhaustive — see pagination note above):

```graphql
{
  rails(where: { state: Active }, first: 100, orderBy: createdAt, orderDirection: desc) {
    railId paymentRate state createdAt totalSettledAmount totalSettlements
    payer { address } payee { address } operator { address } token { symbol name }
  }
}
```

Recent settlements (use for correct per-payee amounts, not rail sums; sample, not exhaustive):

```graphql
{
  settlements(first: 20, orderBy: settledUpto, orderDirection: desc) {
    totalSettledAmount totalNetPayeeAmount filBurned operatorCommission settledUpto
    rail { railId payer { address } payee { address } }
  }
}
```

Operators / tokens (top-N sample, not exhaustive):

```graphql
{ operators(first: 100, orderBy: totalRails, orderDirection: desc) { address totalRails totalTokens totalApprovals } }
{ tokens(first: 10) { name symbol decimals volume totalDeposits totalWithdrawals totalSettledAmount totalUsers userFunds operatorCommission } }
```

## Rail states

`Active` | `Terminated` | `Finalized` (fully settled).
