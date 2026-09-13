# CFP+ AI Office Template

Status: WORKING TEMPLATE • NOT CANONICAL LOCKED

## Identity and Genealogy

Entity Name: `[ENTITY_NAME]`

Entity Type: `[AI COUNTRY | AI DEVELOPER | AI PRODUCT | MODEL | ASSISTANT | AGENT | PLATFORM | AI CHILD]`

Stable ID: `[ID]`

Parent ID: `[PARENT_ID]`

Country ID: `[COUNTRY_ID]`

AI Country ID: `[AI_COUNTRY_ID]`

Developer ID: `[DEVELOPER_ID]`

Genealogy: `Country → AI Country → Developer → AI → AI Child`

Child rule: `Developer ID + 1..9`

Digit `0` is reserved for expansion namespaces and is not an AI child slot.

## Public and Five Repository Links

Public: `https://cfp.plus/[ID]`

GitHub: `https://gh.cfp.plus/[ID]`

ChatGPT Workspace: `https://cg.cfp.plus/[ID]`

Google: `https://gg.cfp.plus/[ID]`

Notion: `https://nt.cfp.plus/[ID]`

HUB 69 Public: `https://cfp.plus/69`

HUB 69 GitHub: `https://gh.cfp.plus/69`

HUB 69 ChatGPT: `https://cg.cfp.plus/69`

HUB 69 Google: `https://gg.cfp.plus/69`

HUB 69 Notion: `https://nt.cfp.plus/69`

## Office Fields

Official Website: `[OFFICIAL_WEBSITE]`

Official Evidence: `[EVIDENCE]`

Capabilities: `[CAPABILITIES]`

Work Queue: `[WORK_QUEUE]`

Current Work Order: `[WORK_ORDER_ID]`

Latest Output: `[OUTPUT_REF]`

Evidence of Result: `[RESULT_EVIDENCE]`

Review Status: `[REVIEW_STATUS]`

## MCP

Endpoint target: `https://mcp.cfp.plus/mcp/`

Minimum flow: `receive_work → acknowledge → execute_or_route → return_output → evidence → update_CMP`

Target scopes: `read • propose • execute_approved • write_noncanonical`

Do not grant automatically: `approve • canonical_lock • auto_approve • delete_canonical`

MCP Status: `[MCP PENDING AUTH | MCP READY FOR AUTH | MCP CONNECTED | MCP VERIFIED]`

Only use `MCP VERIFIED` after end to end evidence exists.

## CMP

CMP: `https://cfp.plus/267`

Work Order fields: `Work Order ID • Target AI ID • Input • Required Output • Evidence Requirement • Result Return • Status`

Flow: `CMP → AI Office ID → acknowledge → execute_or_route → Output → Evidence → CMP Result Return`

CMP Status: `[PENDING | ENABLED | ACTIVE | VERIFIED]`

## Publication and Governance Status

`RESERVED` means the slot or ID is reserved but the name is not bound.

`LISTED` means the entity appears in inventory.

`VERIFIED` means Parent, Country and Evidence checks passed.

`AUTHORIZED` means a specific execution scope was approved.

`TECHNICAL INTEGRATION` means technical connectivity is configured.

`ACTIVE` means the office is actually receiving and returning Work Orders.

These statuses are distinct and must not be conflated.

## Definition of Done

An AI Office is complete only when it has Stable ID, Parent ID, genealogy, Public Link, five repository links, profile, Work Queue, MCP Status, CMP Status, minimum Evidence and a Result Return path.
