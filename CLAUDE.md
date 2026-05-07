# Checkmk User Guide

This repository contains the Checkmk User Guide, written in AsciiDoc. Articles are organized under `src/onprem/`, `src/saas/`, and `src/common/`, each with `de/` (German) and `en/` (English) subdirectories.

## Language authority

German (`de/`) is the authoritative source language. English and other translations are derived from it. When reviewing or editing, always prefer the German article. Only work on the English article if the user explicitly requests it or if no German counterpart exists.

## Dictionary authority

The Checkmk Dictionary is loaded into context at session start. It is the definitive authority on all terminology — product names, GUI element names, compound word rules, and translation equivalents. Follow it without exception when editing or reviewing `.asciidoc` files.

Key terminology (as of March 2026):
- Checkmk Community (formerly Raw) — source: `community`
- Checkmk Pro (formerly Enterprise) — source: `pro`
- Checkmk Ultimate (formerly Enterprise Ultimate) — source: `ultimate`
- Checkmk Ultimate MSP (formerly MSP) — source: `ultimatemt`
- Checkmk Cloud (formerly Cloud Self-hosted) — source: `cloud`

## Target audience

Articles target Checkmk users with hands-on product experience but no prior expertise in the specific topic. They know general concepts (hosts, services, the Setup menu) but may never have used the feature. State prerequisites explicitly; do not assume internal knowledge.

## AI comments

Inline comments added in `.asciidoc` files must use the `// AI: ` prefix. Keep them to one or two sentences.

## Editing

Collect all corrections and comments for a file, then apply them in one pass using a single `Edit` call. Do not ask for confirmation per individual edit.

## Source code verification

The product source code is expected at `~/git/check_mk`. Use `Grep` and `Read` there to verify technical claims. Match the docs branch to the corresponding source branch (docs `master` → `check_mk` `master`; docs `2.4.0` → `check_mk` `2.4.0`).

## Session start

Begin your first response in every session with the session start timestamp from your system context.

## Clarification Before Action
For scripting and refactoring tasks, ask clarifying questions about requirements (e.g., line numbers vs. patterns, detection methods, scope) BEFORE proposing a plan or making edits. Do not enter plan mode for analysis-only or advice requests.