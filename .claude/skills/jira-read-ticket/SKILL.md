---
name: jira-read-ticket
description: Fetch and display a Jira ticket's description, comments, attachments, and linked tickets
---

# Read a Jira Ticket

Fetches a Jira ticket and displays its full context: description, comments, attachments, and linked tickets. User names are anonymized.

Supports tickets from both the **CMK** project (`CMK-` prefix) and the **KNW** project (`KNW-` prefix).

## Arguments

The user provides one or more Jira ticket keys as the argument (e.g., `/jira-read-ticket KNW-1234` or `/jira-read-ticket CMK-12345 KNW-1234`).

## Setup

The skill requires the `jira` Python package. On first use, set up a virtual environment:

```bash
python3 -m venv .claude/skills/jira-read-ticket/.venv && .claude/skills/jira-read-ticket/.venv/bin/pip install jira -q
```

Skip this step if `.claude/skills/jira-read-ticket/.venv` already exists.

## Workflow

### 1. Fetch ticket context

For each ticket key provided, run the helper script:

```bash
.claude/skills/jira-read-ticket/.venv/bin/python .claude/skills/jira-read-ticket/read_ticket.py <TICKET_KEY>
```

If the script fails, report the error to the user and continue with the remaining tickets.

If multiple tickets are requested, fetch them in parallel using separate Bash calls.

### 2. Review attachments

Skip this step entirely if the script output contains no attachment sections.

If there are attachments, launch **at most 2 Task agents** (subagent_type: `general-purpose`) in parallel:

- **Images agent** (only if there are image attachments): One agent receives ALL image file paths. It should read each image with the Read tool and describe what it shows (UI state, error messages, annotations, etc.). Return a concise summary per image.
- **Other files agent** (only if there are non-image attachments): One agent receives ALL other file paths. For text-based files (logs, configs, CSVs), read and summarize key findings. For archives (tar, zip, gz), extract via Bash and summarize structure. Return a concise summary per file.

### 3. Present the ticket

Present the ticket context to the user. Summarize the key information:

- What the ticket is about (type, status, priority)
- The core ask from the description
- Key takeaways from comments (decisions made, blockers, etc.)
- Notable linked tickets and their relevance
- Attachment summaries (if any)

Keep it concise — the user can ask follow-up questions if they need more detail.

### 4. Offer to fetch linked tickets (optional, requires user permission)

After presenting the ticket, check whether any linked tickets were listed in the output. If there are linked tickets, **ask the user** whether they would like the full details of those tickets fetched and added to the context.

> Example prompt: "This ticket links to KNW-456, CMK-789, and CMK-1011. Would you like me to fetch the full details for any of these?"

Only proceed with fetching linked tickets if the user explicitly confirms. Do not recurse automatically. This also applies to any tickets discovered during a recursive fetch — always ask before going deeper.
