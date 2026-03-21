---
name: obsidian-tasks
description: Manage Obsidian Tasks using natural language. Create, modify, complete, and search tasks with subtask linking, project integration, and urgent next action filtering. Use when the user wants to: create new tasks, modify or update existing tasks, mark tasks complete, search or view tasks using natural language, filter for urgent or next action items, link tasks to subtasks or Obsidian Projects, or manage task workflows.
---

# Obsidian Tasks

Manage Obsidian Tasks using natural language with task creation, modification, completion, searching, and filtering capabilities.

> **Dependency**: This skill requires the `obsidian-cli` skill for all `obsidian` command operations.
>
> **Scripts**: `task_utils.py`, `project_utils.py`, and `filter_tasks.py` live in the `scripts/` directory alongside this `SKILL.md`. Use their absolute paths when running them.

## Task Syntax Reference

Obsidian Tasks uses the **native emoji-based metadata format** with standard markdown checkboxes:

```markdown
- [ ] Task description 🔼 📅 2026-03-25 #Project/Frontend
- [x] Completed task ✅ 2026-03-20
- [ ] Task with subtask [[Link to subtask]] 🔼
```

### Task Components

**Status**: Use `[ ]` for incomplete, `[x]` for completed
**Description**: Clear, actionable task description
**Priority**: `⏫` highest · `🔼` high · _(none)_ normal · `🔽` low · `⏬` lowest
**Due date**: `📅 YYYY-MM-DD`
**Done date**: `✅ YYYY-MM-DD` — added automatically on completion
**Start date**: `🛫 YYYY-MM-DD` — when the task may begin
**Scheduled date**: `⏳ YYYY-MM-DD` — planned work date
**Recurrence**: `🔁 every day`, `🔁 every Monday`, etc.
**Projects**: `#Project/Name` hierarchical tags — e.g. `#Project/Frontend`, `#Project/Alpha`. Use tags, **not** wikilinks, for project association. This enables Task Genius plugin views.
**Tags**: `#tag-name` for other organisation

### Recommended Metadata Order

Place metadata after the description text in this order:

```
description [[links]] #tags ⏫/🔼/🔽/⏬  🔁 recurrence  🛫 start  ⏳ scheduled  📅 due  ✅ done
```

### Common Patterns

```markdown
- [ ] Important task 🔼 📅 2026-03-25
- [ ] Review document #Project/Alpha 📅 2026-03-26
- [ ] Subtask for [[Parent Task]] 🔽
- [ ] Recurring item 🔁 every Monday 🛫 2026-03-21 #Project/Frontend
```

## Workflow: Creating Tasks

1. **Parse user intent** to extract task description, dates, priorities, and links
2. **Build task syntax** using the native emoji metadata format
3. **Tag the project** using `#Project/Name` format (e.g. `#Project/Frontend`)
4. **Append to `Tasks.md`** — all new tasks go here by default:

```bash
# Always add new tasks to Tasks.md
obsidian append file="Tasks" content="- [ ] Review document #Project/Alpha 📅 2026-03-26"
```

> **Note**: The default task file is always `Tasks.md`. If `obsidian append` fails with "File not found", create the file first with `obsidian write file="Tasks" content=""`, then retry the append. Do **not** fall back to the daily note for task creation unless the user explicitly asks for it.

## Workflow: Searching & Filtering Tasks

### Real `obsidian tasks` flags

The CLI supports these flags — nothing more:

```bash
obsidian tasks todo                      # All incomplete tasks
obsidian tasks done                      # All completed tasks
obsidian tasks todo daily                # Incomplete tasks from today's daily note
obsidian tasks done daily                # Completed tasks from today's daily note
obsidian tasks todo file="Tasks"         # Incomplete tasks from a specific file
obsidian tasks todo active               # Tasks from the currently active file
obsidian tasks todo verbose              # Group results by file with line numbers
obsidian tasks todo format=json          # JSON output — use this for any advanced filtering
obsidian tasks todo total                # Return count of incomplete tasks
```

### Filtering by date, priority, or project

The `obsidian tasks` CLI has **no built-in filters** for due date, priority, or project. For those, fetch tasks as JSON and pipe to `filter_tasks.py`.

> **Note**: The `obsidian` CLI may emit warning/info lines (e.g. "Loading updated app package...") to stdout before the JSON payload. `filter_tasks.py` handles this automatically by scanning for the first `[` in stdin.

```bash
# Replace <scripts> with the absolute path to the scripts/ directory

# Tasks due today
obsidian tasks todo format=json | python3 <scripts>/filter_tasks.py --today

# Overdue tasks
obsidian tasks todo format=json | python3 <scripts>/filter_tasks.py --overdue

# Tasks with no due date
obsidian tasks todo format=json | python3 <scripts>/filter_tasks.py --no-due

# Due within 7 days (or specify N days)
obsidian tasks todo format=json | python3 <scripts>/filter_tasks.py --due-soon 7

# By priority level: highest | high | normal | low | lowest
obsidian tasks todo format=json | python3 <scripts>/filter_tasks.py --priority high

# Urgent: high/highest priority + anything overdue or due today, sorted by urgency
obsidian tasks todo format=json | python3 <scripts>/filter_tasks.py --urgent

# All incomplete tasks ranked by urgency score (default when no filter given)
obsidian tasks todo format=json | python3 <scripts>/filter_tasks.py --next-action

# Recurring tasks
obsidian tasks todo format=json | python3 <scripts>/filter_tasks.py --recurring
```

For project-specific queries (pass all tasks, not just `todo`, for summary):

```bash
# Open tasks for one project, urgency-sorted
obsidian tasks todo format=json | python3 <scripts>/filter_tasks.py --project "Project Alpha"

# List all project names found in tasks
obsidian tasks format=json | python3 <scripts>/filter_tasks.py --projects

# Project summary table: open · done · overdue per project
obsidian tasks format=json | python3 <scripts>/filter_tasks.py --project-summary
```

You can also search for tasks containing specific text or emoji using `obsidian search`:

```bash
obsidian search query="#Project/Alpha"       # Files with tasks for a project
obsidian search query="🔼"                   # Files with high-priority tasks
obsidian search query="✅ 2026-03-21"        # Files with tasks completed on a date
```

### Natural language → correct command

| User asks | What to run |
|---|---|
| "What's urgent / what's next?" | `obsidian tasks todo format=json \| filter_tasks.py --urgent` |
| "What do I need to do today?" | `obsidian tasks todo format=json \| filter_tasks.py --today` |
| "Any overdue tasks?" | `obsidian tasks todo format=json \| filter_tasks.py --overdue` |
| "Tasks without a due date" | `obsidian tasks todo format=json \| filter_tasks.py --no-due` |
| "High priority tasks" | `obsidian tasks todo format=json \| filter_tasks.py --priority high` |
| "Recurring tasks" | `obsidian tasks todo format=json \| filter_tasks.py --recurring` |
| "Daily note tasks" | `obsidian tasks todo daily` |
| "Tasks in file X" | `obsidian tasks todo file="X"` |
| "Completed tasks" | `obsidian tasks done` |
| "What projects do I have?" | `obsidian tasks format=json \| filter_tasks.py --projects` |
| "Give me a project overview" | `obsidian tasks format=json \| filter_tasks.py --project-summary` |
| "Open tasks for Project Alpha" | `obsidian tasks todo format=json \| filter_tasks.py --project "Project Alpha"` |

## Workflow: Modifying Tasks

1. **Find task** — search for the file containing it:
   ```bash
   obsidian search query="exact task description"
   ```
2. **Read the file**:
   ```bash
   obsidian read file="Tasks"
   ```
3. **Update emoji metadata** with new values in the task line
4. **Write changes** — edit the file directly, replacing only the changed task line

## Workflow: Completing Tasks

1. **Find task** using `obsidian tasks todo` or search
2. **Read `Tasks.md`** to get the full task line:
   ```bash
   obsidian read file="Tasks"
   ```
3. **Toggle completion**: change `[ ]` to `[x]`
4. **Add done date**: append `✅ YYYY-MM-DD` (today's date)
5. **Remove the task from `Tasks.md`**: edit the file, deleting the completed task line
6. **Append to `Completed_Tasks.md`**: add the completed task line there
   ```bash
   obsidian append file="Completed_Tasks" content="- [x] Review document #Project/Alpha 📅 2026-03-27 ✅ 2026-03-21"
   ```

> **Important**: Completed tasks must always be moved — removed from `Tasks.md` and appended to `Completed_Tasks.md`. Never leave a `[x]` task in `Tasks.md`.

## Workflow: Project Views

Projects are identified by `#Project/Name` tags in task descriptions. There is no native `obsidian tasks project` command — use `filter_tasks.py` for all project operations.

```bash
# List all project names
obsidian tasks format=json | python3 <scripts>/filter_tasks.py --projects

# Summary table (open / done / overdue per project)
obsidian tasks format=json | python3 <scripts>/filter_tasks.py --project-summary

# Open tasks for one project, sorted by urgency
obsidian tasks todo format=json | python3 <scripts>/filter_tasks.py --project "Project/Alpha"

# All tasks for a project (includes completed)
obsidian search query="#Project/Alpha"
```

## Example: Complete Task Workflow

1. **Create**: User asks "Add a task to review the document for Project Alpha due tomorrow"
   - Parse: description="review document", project="Project Alpha", due="tomorrow"
   - Build: `- [ ] Review document #Project/Alpha 📅 2026-03-22`
   - Run: `obsidian append file="Tasks" content="- [ ] Review document #Project/Alpha 📅 2026-03-22"`

2. **Search**: User asks "Show me my urgent next actions"
   - Run: `obsidian tasks todo format=json | python3 <scripts>/filter_tasks.py --urgent`
   - Display results

3. **Modify**: User asks "That task should be due on Friday instead"
   - Find: `obsidian search query="Review document"`
   - Read: `obsidian read file="Tasks"`
   - Edit the task line, updating `📅 2026-03-22` → `📅 2026-03-27`

4. **Complete**: User says "Mark it done"
   - Read `Tasks.md`, find the task line
   - Build completed line: `- [x] Review document #Project/Alpha 📅 2026-03-27 ✅ 2026-03-21`
   - Remove the line from `Tasks.md`
   - Append to `Completed_Tasks.md`: `obsidian append file="Completed_Tasks" content="- [x] Review document #Project/Alpha 📅 2026-03-27 ✅ 2026-03-21"`

## Key Considerations

- **Projects use tags, not wikilinks**: Always use `#Project/Name` format for project association — e.g. `#Project/Frontend`, `#Project/Alpha`. This enables Task Genius plugin views.
- **Preserve existing metadata**: When updating tasks, maintain all existing emoji properties unless specifically changed
- **Natural language dates**: Use `parse_natural_date()` from `task_utils.py` to convert "tomorrow", "next Friday", etc. to ISO dates
- **Subtask linking**: Use section wikilinks to show task hierarchy: `[[Parent Task#Subtask]]`
- **Project filtering requires Python**: The `obsidian tasks` CLI has no project/date/priority filters — always use `filter_tasks.py` for these

## References

- Full task operations guide: `references/TASK_OPERATIONS.md`
- For full native Obsidian Tasks syntax documentation: https://publish.obsidian.md/tasks
