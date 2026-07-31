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

```
# last known production — 404s as of 2026-07-31, verify before use
https://api.goldsky.com/api/public/project_cmb9tuo8r1xdw01ykb8uidk7h/subgraphs/filecoin-pay-mainnet/1.0.6/gn
```

- **v1.0.6** was the long-standing known-good production version and is still the version cited
  across Tim's notes; every other subgraph under the same project now 404s too, which points at
  a project-level rotation rather than one bad deploy.
- **v1.2.0** (`filecoin-pay-mainnet-tim`) was **permanently broken** even while live —
  deterministic mapping error at block 5,810,264; needs a code fix + redeploy.
- The **old project** `project_cmj7soo5uf4no01xw0tij21a1` was deleted.

Smoke-test any candidate endpoint before building on it:
```bash
curl -s -X POST "$ENDPOINT" -H "Content-Type: application/json" \
  -d '{"query":"{ _meta { block { number } } }"}'
```

Query with POST:
```bash
curl -s -X POST "$ENDPOINT" -H "Content-Type: application/json" \
  -d '{"query": "{ paymentsMetrics(first: 1) { totalRails totalActiveRails totalAccounts uniquePayers uniquePayees } }"}' | jq
```

## Known traps

- **Raw token amounts are wei-scale integers** — divide by `10^18` before displaying FIL/USDFC amounts.
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

Daily token metrics (sum these into weekly for WBR — no weekly per-token entity):
```graphql
{
  dailyTokenMetrics(first: 28, orderBy: timestamp, orderDirection: desc) {
    date volume deposit withdrawal settledAmount commissionPaid
    activeRailsCount uniqueHolders totalLocked
    token { symbol }
  }
}
```

Active rails:
```graphql
{
  rails(where: { state: Active }, first: 100, orderBy: createdAt, orderDirection: desc) {
    railId paymentRate state createdAt totalSettledAmount totalSettlements
    payer { address } payee { address } operator { address } token { symbol name }
  }
}
```

Recent settlements (use for correct per-payee amounts, not rail sums):
```graphql
{
  settlements(first: 20, orderBy: settledUpto, orderDirection: desc) {
    totalSettledAmount totalNetPayeeAmount filBurned operatorCommission settledUpto
    rail { railId payer { address } payee { address } }
  }
}
```

Operators / tokens:
```graphql
{ operators(first: 100, orderBy: totalRails, orderDirection: desc) { address totalRails totalTokens totalApprovals } }
{ tokens(first: 10) { name symbol decimals volume totalDeposits totalWithdrawals totalSettledAmount totalUsers userFunds operatorCommission } }
```

## Rail states

`Active` | `Terminated` | `Finalized` (fully settled).
