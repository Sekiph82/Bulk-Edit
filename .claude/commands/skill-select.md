# /skill-select — Select Skills for Current Task

## Instructions for Claude

Before starting any implementation task, complete this protocol:

1. Read SKILLS.md
2. Identify the task from TASKS.md or user message
3. Select skills using this format:

## Skill Selection Format

```
SKILL SELECTION
Task: [task description]

Primary skill: [id] [name]
  Use when: [brief reason this skill applies]

Supporting skills:
  [id] [name] — [role in this task]
  [id] [name] — [role in this task]

Files to inspect before starting:
  [path] — [why]
  [path] — [why]

Files expected to change:
  [path] — [what changes]
  [path] — [what changes]

Tests to run after:
  [test command or file]
  [test command or file]

Docs to update:
  [doc file] — [what to update]

If a required skill is missing from SKILLS.md: create it now before continuing.
```

Do not skip this protocol. Skills define boundaries and prevent scope creep.
