---
name: obsidian-process-journal
description: Processes raw Obsidian journal entries (daily notes or yearly files) into clean, readable prose. Use this skill whenever the user wants to process, convert, or enrich journal entries — including daily .md files, yearly journal files, or any raw bullet-point journal content. Trigger when the user mentions processing journal notes, converting bullet journals to prose, or cleaning up daily notes. If a user says anything like "process my journal", "convert my notes", "enrich my daily entries", or "clean up my diary", use this skill immediately.
---

# Journal Entry Processor

This skill converts raw Obsidian journal entries (typically bullet-point daily notes) into clean, readable prose. The transformation has two parts: bullets become flowing sentences, and abbreviations are expanded naturally on first mention so the text reads clearly without a glossary in hand.

## Before You Start: Load the Entity Glossary

Read `Processed_Entries/Entity_Glossary.md` before processing any entries. This file is the authoritative reference for who people are, what places and organisations mean, and how abbreviations expand. Use it to write entries correctly — but do not echo its contents inline as annotations. If the glossary doesn't exist yet, proceed using context from the entries themselves. If new entities are found in the journal entries (that don't exist in the Entity_Glossary.md), please add them to this file and mark them as TODOs for the user to verify before the next run.

## The Core Transformation

**Raw input:**
```markdown
2025-01-01
# What happened today?
- Bullet point describing an event
- Another bullet with acronyms like ETZ or GenAI
- Met with Ashok to discuss the IPA PoC
```

**Processed output:**
```markdown
2025-01-01

Prose paragraph expanding bullet 1 into a clear sentence.

Prose expanding bullet 2, expanding abbreviations naturally: Embasssy Tech Zone (ETZ) or Generative AI (GenAI).

I met with Ashok to discuss the Intelligent Process Automation (IPA) proof of concept.
```

### What changes and what doesn't

**Preserve everything** — no summarising, no dropping details, no merging bullets that belong apart. Every fact, number, personal note, and observation in the original must appear in the output.

**Expand abbreviations** on first mention per file, using the natural form: write out the full name first, then the abbreviation in parentheses — e.g., `Embasssy Tech Zone (ETZ)`, `Generative AI (GenAI)`, `Intelligent Process Automation (IPA)`, `Business Requirements Document (BRD)`. After first mention, use the short form freely.

**People are written by name only.** Do not annotate roles or relationships inline — that's what the glossary is for. Write "I met with Sneha" not "I met with Sneha [wife]". Write "Ashok raised a concern" not "Ashok [colleague] raised a concern". The prose should read like a journal, not a tagged database.

**Organisations** get their full name on first mention if they appear abbreviated — e.g., write "Vodafone" (not "Vodafone [Telecom company]"). If the raw entry already uses the full name, keep it as-is.

**Don't invent facts.** If a bullet is vague, keep it vague in the prose. Don't add context or colour that isn't in the original.

### Writing the prose

Group related bullets into paragraphs — if three bullets all describe one meeting, they can form one paragraph. Bullets about distinct events should become distinct paragraphs. Write in first person ("I went to...", "I met...", "I worked on...") to match journal voice.

Use clear, plain sentence structure. No literary flourishes, no editorial commentary. The goal is readability and completeness, not style.

## Output

- Save to `Processed_Entries/yyyy-mm-dd.md`
- The first line is the date (e.g., `2025-01-02`), then a blank line, then the prose paragraphs
- Do NOT include the "# What happened today?" header in output

## Example

**Input** (`2025-01-02` section of a daily note):
```
- Back to office after the holidays. Went to ETZ
- I had put in a couple of meetings myself to start catching up on things. Mainly the GenAI / IPA PoCs with Sachin, Ashok & Nitin. Also on the impending visits with Rajesh and IPA presentation to Vodafone with Sangeeta
- Thought it would be a lighter day, but already did the above. On top of that there was a sudden ask to prepare a deck for Corporate Audit. So an intruding task came up ! And I am sure there will be a lot of those as usual in this year. Have to control them and ensure I do spend time on those tasks that I do want to and are more strategically aligned
- I was in office almost till 8 pm as I was finishing off a couple of financial things in terms of paying Life Insurance premium etc
```

**Output** (`Processed_Entries/2025-01-02.md`):
```
2025-01-02

I returned to the office after the holidays, going to Embasssy Tech Zone (ETZ).

I had scheduled a couple of meetings to catch up on things, focusing on Generative AI (GenAI) and Intelligent Process Automation (IPA) proof of concepts with Sachin, Ashok, and Nitin. I also discussed the impending visits with Rajesh and the IPA presentation to Vodafone with Sangeeta.

I had expected a lighter day, but a sudden request to prepare a deck for Corporate Audit came up — an intruding task. I expect there will be many such tasks throughout the year and I need to keep them in check, ensuring I protect time for work that is more strategically aligned with what I want to focus on.

I stayed in the office until almost 8 pm, finishing some financial tasks including paying my Life Insurance premium.
```

## Processing Yearly Files

Yearly files (e.g., `2021.md`, `2022.md`) contain multiple daily entries in a nested structure. For each:

1. Identify daily entry boundaries — typically headers like `[2022-01-01, Saturday]` or `## 2022-01-01`
2. Extract the date from the header
3. Extract the bullet content beneath it
4. Process using the same workflow above
5. Save each as `Processed_Entries/yyyy-mm-dd.md` — one file per day

Process in chronological order. If you're processing a large yearly file, confirm with the user whether they want all entries processed or just a date range.
