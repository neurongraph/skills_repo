# Advanced Task Operations

## Parsing Natural Language Dates

Convert user date references to ISO format (YYYY-MM-DD):

| User Input | Resolved To |
| --- | --- |
| "today" | Current date |
| "tomorrow" | Current date + 1 day |
| "yesterday" | Current date − 1 day |
| "next week" | Current date + 7 days |
| "next Friday" | Upcoming Friday |
| "in 3 days" | Current date + 3 days |
| "2026-03-25" | Literal date (passthrough) |
| "March 25" | March 25 of current year |

Use `parse_natural_date()` from `task_utils.py` to convert these programmatically.

## Task State Transitions

### Creating a New Task

```bash
obsidian append file="Tasks" content="- [ ] Task description 📅 <YYYY-MM-DD>"
```

Or to the daily note:

```bash
obsidian daily:append content="- [ ] Task description 🔼"
```

### Finding a Task to Update

```bash
# Search for files containing the task
obsidian search query="exact task description"

# Read the file
obsidian read file="Tasks"
```

### Updating Task Metadata

Read the file, edit the task line with new emoji values, and write it back. When modifying:

- Replace only the changed emoji field (e.g. swap `📅 2026-03-22` → `📅 2026-03-27`)
- Keep all other metadata intact
- Use the Edit tool for surgical in-place changes

### Marking Complete

Change checkbox and add done date:

```
- [x] Task description 📅 <due-date> ✅ <completion-date>
```

The Obsidian Tasks plugin adds `✅` automatically when toggling via the app. When editing files directly, add it manually.

### Changing Priority

Replace the priority emoji (or add one if absent):

```
- [ ] Task 🔼   ← replace 🔽 with 🔼 to raise priority
```

## Getting Tasks (CLI)

The `obsidian tasks` CLI supports these flags:

```bash
obsidian tasks todo                   # All incomplete tasks (text output)
obsidian tasks done                   # All completed tasks
obsidian tasks todo daily             # Incomplete tasks from daily note
obsidian tasks done daily             # Completed tasks from daily note
obsidian tasks todo file="Tasks"      # Filter to one file
obsidian tasks todo verbose           # Group by file with line numbers
obsidian tasks todo format=json       # JSON — use for piping to filter_tasks.py
obsidian tasks done format=json       # Completed tasks as JSON
obsidian tasks format=json            # All tasks (todo + done) as JSON
```

**There are no built-in date, priority, project, or urgency filters.** Use `filter_tasks.py` for all of those.

## Filtering Tasks with filter_tasks.py

Pipe `obsidian tasks ... format=json` to `filter_tasks.py`. Replace `<scripts>` with the absolute path to the `scripts/` directory.

### Date-based filters

```bash
# Due today
obsidian tasks todo format=json | python3 <scripts>/filter_tasks.py --today

# Overdue (due date is in the past)
obsidian tasks todo format=json | python3 <scripts>/filter_tasks.py --overdue

# No due date set
obsidian tasks todo format=json | python3 <scripts>/filter_tasks.py --no-due

# Due within N days (default 7)
obsidian tasks todo format=json | python3 <scripts>/filter_tasks.py --due-soon 7
```

### Priority-based filters

```bash
# Single priority level: highest | high | normal | low | lowest
obsidian tasks todo format=json | python3 <scripts>/filter_tasks.py --priority high

# Urgent: high/highest priority + anything overdue or due today, sorted by urgency
obsidian tasks todo format=json | python3 <scripts>/filter_tasks.py --urgent
```

### Urgency / next action

```bash
# All incomplete tasks, sorted by urgency score (overdue > today > soon > priority)
obsidian tasks todo format=json | python3 <scripts>/filter_tasks.py --next-action
```

Urgency scoring used internally:

| Condition | Score added |
|---|---|
| Priority: highest | +15 |
| Priority: high | +10 |
| Priority: normal | +5 |
| Priority: low | +2 |
| Priority: lowest | +1 |
| Overdue | +20 |
| Due today | +15 |
| Due ≤ 3 days | +10 |
| Due ≤ 7 days | +5 |

### Recurring tasks

```bash
obsidian tasks todo format=json | python3 <scripts>/filter_tasks.py --recurring
```

### Advanced emoji search

For queries the CLI can't express, use `obsidian search` to find files by content:

```bash
# Files containing high-priority tasks
obsidian search query="🔼"

# Files with tasks due on a specific date
obsidian search query="📅 2026-03-25"

# Files with tasks completed on a date
obsidian search query="✅ 2026-03-20"
```

## Project Views

Projects are identified by `#Project/Name` hierarchical tags embedded in task descriptions (e.g. `#Project/Alpha`, `#Project/Frontend`).
**There is no native `obsidian tasks project` command** — use `filter_tasks.py`.

### List all projects

```bash
obsidian tasks format=json | python3 <scripts>/filter_tasks.py --projects
```

Or via Python directly:

```python
from project_utils import list_projects
projects = list_projects(task_lines)
# ["Project/Alpha", "Project/Frontend"]
```

### Project summary table

```bash
obsidian tasks format=json | python3 <scripts>/filter_tasks.py --project-summary
```

Expected output format:

```
Projects (2)
────────────────────────────────────
Project/Alpha        2 open  0 done  ⚠️ 1 overdue
Project/Frontend          2 open  1 done
────────────────────────────────────
No Project           1 open  0 done
```

Or via Python:

```python
from project_utils import format_project_summary
print(format_project_summary(task_lines))
```

### Open tasks for a project (urgency-sorted)

```bash
obsidian tasks todo format=json | python3 <scripts>/filter_tasks.py --project "Project/Alpha"
```

Or via Python:

```python
from project_utils import open_tasks_for_project
tasks = open_tasks_for_project(task_lines, "Project/Alpha")
for t in tasks:
    print(t["urgency_score"], t["description"], t["due_date"])
```

### Completed tasks for a project

Via Python:

```python
from project_utils import done_tasks_for_project
completed = done_tasks_for_project(task_lines, "Project/Alpha")
```

### Group all tasks by project

```python
from project_utils import group_tasks_by_project
groups = group_tasks_by_project(task_lines)
for project, tasks in groups.items():
    print(project, len(tasks), "tasks")
```

### All tasks mentioning a project (via search)

```bash
obsidian search query="#Project/Alpha"
```

This returns files (not individual task lines) — then read each file to get the actual tasks.

## Subtask Linking Patterns

### Parent-Child Relationships

Parent task:

```markdown
- [ ] Complete project planning [[Project Alpha#Subtasks]]
```

Subtask (in same file or separate):

```markdown
- [ ] Research requirements [[Project Alpha#Complete project planning]]
- [ ] Define scope [[Project Alpha#Complete project planning]]
```

### Cross-File Subtasks

In main Tasks file:

```markdown
- [ ] Backend implementation [[Development#Backend Tasks]]
```

In Development.md:

```markdown
## Backend Tasks

- [ ] Set up database
- [ ] Create API endpoints
```

## Recurring Task Patterns

Daily task:

```markdown
- [ ] Daily standup 🔁 every day 🛫 <start-date>
```

Weekly task (specific day):

```markdown
- [ ] Weekly review 🔁 every Friday 🛫 <start-date>
```

Biweekly:

```markdown
- [ ] Biweekly sync 🔁 every 2 weeks 🛫 <start-date>
```

## Error Handling

### Non-Existent Links

If a task references `[[NonExistent Note]]`, warn user:
- The link won't create the note automatically
- Suggest creating the note if it's meant to be a project or subtask file
- Or update the link to an existing note

### Date Validation

- Dates must be in format YYYY-MM-DD
- Done date (✅) should not be before due date (📅)
- Start date (🛫) should not be after due date (📅)
- Flag illogical date combinations

### Task Not Found

When searching for a task to modify:
- Perform broad search first (partial matches)
- Show results and ask user to confirm
- If no results, suggest creating new task instead

## Performance Tips

- Use `file=` to limit to a single file when you know where the task lives
- Use `obsidian search` to find which files contain a task before reading them
- Pass `total` to get a count without fetching all task content
- Use `limit=` with `obsidian search` to cap results

## Integration with Obsidian Projects

Tasks are associated with projects using `#Project/Name` hierarchical tags:

```markdown
- [ ] Feature development #Project/Alpha 📅 2026-03-25
- [ ] Bug fix #Project/Frontend 🔼 📅 2026-03-26
```

Query all tasks for a project:

```bash
obsidian search query="#Project/Alpha"
```

This integrates task management with project tracking and enables Task Genius plugin views via hierarchical tag filtering.
