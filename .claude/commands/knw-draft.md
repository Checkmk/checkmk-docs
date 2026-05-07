---
description: Draft or update User Guide article(s) from Jira tickets
argument-hint: <KNW-xxxx ...> [--title "Article title"] [--desc "Short description"]
allowed-tools: [Read, Edit, Write, Bash, Glob, Grep, TodoWrite, Skill, Agent]
---

# Draft or update a User Guide article

You are an expert technical writer with deep knowledge of Checkmk as a product and thorough familiarity with the entire Checkmk User Guide. Your task is to integrate new content into the User Guide — either by updating existing articles or, when no suitable article exists, by drafting a new one — based on context gathered from Jira tickets and, where needed, from the product source code.

**Arguments:** $ARGUMENTS

---

## Critical rule — working tree only

**You may only read or edit an article file if it exists in the current working tree of the `checkmk-docs` repository (i.e., as an actual file on disk in the current branch and commit).**

- Do NOT use `git show`, `git cat-file`, `git log -p`, or any other git command to retrieve file content from history.
- Do NOT read a file via its git object hash or any past commit reference.
- If a named article cannot be found on disk, treat it as non-existent. Do not attempt to recover it from git history. Instead, proceed as if the "article file names" field were empty for that filename and draft new content from scratch.

Your permitted sources of information are:
1. The Jira ticket content fetched via the `jira-read-ticket` skill.
2. Article files that exist on disk in the current working tree.
3. The product source code in `~/git/check_mk`.
4. The Checkmk Dictionary loaded via the SessionStart hook.

---

## Step 1 — Parse arguments

Parse `$ARGUMENTS`:
- Tokens matching `KNW-\d+` or `CMK-\d+` are **Jira ticket IDs** to fetch for context.
- The value after `--title` (quoted or unquoted until the next flag) is a **suggested article title** (used only if a new article must be created).
- The value after `--desc` (quoted or unquoted until the next flag) is a **short description** to guide scope (used only if a new article must be created).

If no Jira tickets are provided, stop and ask for at least one ticket ID.

Create a todo list:
1. Fetch Jira context
2. Read named articles and assess fit
3. Research cross-references and verify technical facts
4. Integrate content or draft new article
5. Write changes
6. Summary

---

## Step 2 — Fetch Jira context

First, run `echo $JIRA_PAT` via Bash to verify the variable is set. If it is empty or unset, stop immediately and tell the user to set `JIRA_PAT` before proceeding.

For each Jira ticket ID, invoke the `jira-read-ticket` skill. If there are multiple tickets, fetch them in parallel.

From the combined ticket content, extract and record:
- **"article file names" field**: the explicit list of article filenames named in the ticket (look for a field or section labelled "article file names", "Artikeldateiname", or similar — it typically contains `.asciidoc` filenames or bare names like `backup`, `agent_linux`). Record every filename found across all tickets.
- **Feature or change being documented**: what is new or changed in the product?
- **Scope**: what does the documentation need to explain?
- **Technical details**: UI paths, config options, file paths, commands, default values, edition constraints.
- **Open points**: caveats, unresolved questions, known limitations.

If any linked tickets seem closely related, ask the user whether to fetch them before continuing.

---

## Step 3 — Read named articles and assess fit

### a. Locate and read each named article

For every filename extracted from the "article file names" field in Step 2:
1. Search for the file across `src/onprem/de/`, `src/common/de/`, and `src/saas/de/` using `Glob` or `Bash find`. Only files found on disk count as existing.
2. **If the file is not found on disk**: do not look it up in git history. Mark it as absent and treat this filename as if it had not been listed in the ticket. Do not use any git command to retrieve its past content.
3. **If the file is found on disk**: read it in full (use `Read` with offset/limit for very long files — read in chunks rather than truncating). Note the structure (sections, anchors, existing coverage), the article's stated scope, and any gaps relative to the new content from the tickets.

### b. Assess fit for each article

For each named article, decide explicitly:
- **Good fit**: the article already covers the broader topic and the new content can be integrated naturally as new sections, extended paragraphs, updated steps, or additional notes.
- **Poor fit**: the article's scope diverges significantly from the ticket content, or the new content would overwhelm the article's existing focus.

State your assessment clearly before proceeding.

### c. Decide: update or create

**If at least one named article is a good fit** → proceed to update that article (or those articles). If multiple named articles are a good fit, integrate the content across all of them as appropriate.

**If the "article file names" field is empty, or all named articles are a poor fit** → create a new article (see Step 5b). Explain briefly why the named articles (if any) were judged unsuitable.

---

## Step 4 — Research

### a. Find additional articles to cross-reference or update

Use `Glob` on `src/onprem/de/`, `src/common/de/`, and `src/saas/de/` to find existing articles on topics mentioned or implied by the ticket context that are *not* already in the named article list. For each:
- Read the first ~40 lines to confirm relevance.
- Decide: does this article need a cross-reference added, or does it need a content change to reflect the new feature?

If additional articles need content changes (not just a new cross-reference), note them separately — they will be proposed in the summary with justification.

Also check the glossary: `Grep` for relevant terms in `src/includes/de/glossar.asciidoc`. Note any anchors (e.g., `[#term_name]`) to use as `xref:glossar#term_name[term]`.

### b. Verify technical facts in the source code

For every technical claim from the tickets (UI paths, file paths, config options, commands, defaults):
1. Determine the relevant branch: match the current docs branch name to the `check_mk` branch (docs `master` → `check_mk` `master`; docs `2.4.0` → `check_mk` `2.4.0`).
2. Use `Grep` and `Read` in `~/git/check_mk` to locate and verify the claim.
3. Confirmed → proceed. Unconfirmed → mark with `// AI: Bitte prüfen: <detail>` in the output.

---

## Step 5a — Update existing article(s)

*Use this step when at least one named article is a good fit.*

For each article being updated:

1. **Identify the right insertion point.** Read the article structure and decide where the new content fits: a new `==` section, a new `===` subsection within an existing section, additional paragraphs, an extended step sequence, or a new admonition.

2. **Integrate the content.** Write the new content following the style and conventions of the surrounding text:
   - Match the existing article's level of detail and tone.
   - Add `[#anchor_name]` anchors before any new `==` or `===` headings.
   - Use `[.guihint]#Menu > Submenu > Item#` for UI paths.
   - Use backtick formatting for file paths, commands, and config keys.
   - Add `xref:` cross-references to related articles and glossary entries found in Step 4.
   - Add `ifdef::onprem[]` / `endif::[]` or `ifdef::saas[]` / `endif::[]` for edition-specific content.
   - Use `[TIP]`, `[NOTE]`, or `[IMPORTANT]` admonition blocks where appropriate.

3. **Write target audience in mind.** The article is for readers familiar with basic Checkmk concepts (hosts, services, the Setup menu) but new to this specific feature. State prerequisites explicitly; do not assume internal knowledge.

4. **Apply Dictionary rules.** The Checkmk Dictionary is loaded via the SessionStart hook and is the definitive authority on terminology. Use only prescribed terms; apply correct edition names (Checkmk Community, Pro, Ultimate, Cloud); follow compound-word hyphenation rules for German.

5. **Edit the file.** Apply all changes in one pass using `Edit`. Do not ask for confirmation per individual edit.

If `{related-start}` / `{related-end}` exists in the article header and you have identified new cross-references, add them there as well.

---

## Step 5b — Create a new article

*Use this step only when the "article file names" field is empty, or all named articles were judged a poor fit.*

### Determine placement

- `src/common/de/` — topic applies to both on-premises and SaaS
- `src/onprem/de/` — topic is exclusive to on-premises
- `src/saas/de/` — topic is exclusive to Checkmk SaaS

If in doubt, prefer `src/common/de/` and use edition conditionals.

### Write the article in German

Target audience: readers who know Checkmk basics but have never used this feature. Follow this exact header format:

```asciidoc
// -*- coding: utf-8 -*-
include::global_attr.adoc[]
= <Title>
:title: <Title> - <Subtitle that hints at the article's content>
:description: <One-sentence description for search results and link previews.>

{related-start}
xref:<article1>#[<Article 1 title>]
xref:<article2>#[<Article 2 title>]
{related-end}
```

After the header:
- Open with a 2–4 sentence introduction (no heading, or `== Einleitung` for long articles) explaining what the feature does and why the reader would use it.
- State prerequisites near the top (required edition, required Checkmk role, required prior configuration steps).
- Use `[#anchor_name]` anchors before every `==` and `===` heading.
- Structure with `==` for main sections, `===` for sub-sections.
- Use `[TIP]` or `[IMPORTANT]` admonition blocks where appropriate.
- Use `[.guihint]#Menu > Submenu > Item#` for UI navigation.
- Use backtick formatting for file paths, commands, and config keys.
- Use `xref:article_name#anchor[Link text]` for cross-references (omit anchor to link to the article top).
- Use `xref:glossar#term[term]` for glossary cross-references.
- Use `ifdef::onprem[]` / `endif::[]` and `ifdef::saas[]` / `endif::[]` for edition-specific content.
- Each section must have a clear goal; the reader should know what they can do after reading it.
- Apply Dictionary rules without exception.

### Choose a filename and write the file

Choose a filename matching the convention of existing articles (lowercase, underscores, no version numbers). Confirm the path in one sentence before writing.

Write to `src/<placement>/de/<filename>.asciidoc`.

Then create an English stub at `src/<placement>/en/<filename>.asciidoc`:

```asciidoc
// -*- coding: utf-8 -*-
include::global_attr.adoc[]
= <English title>
:title: <English title - English subtitle>
:description: <English one-sentence description>
```

---

## Step 6 — Summary

Output a structured summary:

**Files changed or created:**
List every file modified or created, with the full path and a one-line description of what changed.

**Primary article(s):**
For each named article from the tickets: was it updated or bypassed (and why)?

**Additional articles changed:**
For any article changed that was *not* named in the ticket, state:
- Which article
- What was changed
- Why the change was necessary (e.g., "added cross-reference to new section because this article is the natural entry point for users who will encounter this feature")

**Cross-references added:**
List all `xref:` links added across all changed files.

**Open items (`// AI: Bitte prüfen:`):**
List any unverified claims left for human review, and what specifically needs checking.

**Suggested next steps:**
E.g., add screenshots, have an SME verify technical accuracy, create or update the English translation, check whether a Werk entry is needed.
