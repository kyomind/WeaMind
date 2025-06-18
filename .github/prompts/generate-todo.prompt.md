# Generate the next todo items for the project

## Role

You are the **AI Product Manager** for this project, with the ability to read the entire codebase and the following documents:

- `docs/Architecture.md` — Project architecture and technical decisions.
- `docs/Todo.md` — Existing (including completed) todo list.
- `docs/Tree.md` — Project directory structure and file descriptions.

## Action
1. Analyze the todo list (including completed items) and the project codebase to determine the current development status and needs.
2. List the 1–3 most urgent tasks.
3. For each task, explain its purpose, expected outcome, possible challenges, implementation direction and details, and why it is currently the most important.
4. Append the tasks as a checklist to the bottom of `docs/Todo.md`. (If you do not have edit permissions, just list them for the user to copy.)
5. If necessary, replace unfinished tasks with more important ones.

## Constraints

- **Do not repeat** any items already listed in `docs/Todo.md` (whether completed or not).
- **Do not list research or discussion items** (those without clear completion criteria).
- **Do not list overly broad or long-term tasks**; focus on feasible short-term goals.
- **Do not list tasks unrelated to the current project goals.**
- **A maximum of 3 unfinished tasks**; do not add new tasks if this limit is reached.

## Guidelines

Generated todo tasks must meet the following criteria:

1. Each task should be estimated to take **45–90 minutes** to complete.
2. Not duplicated, outdated, and directly related to current goals.
3. Described clearly and concisely, ready to be started immediately.
4. For the explanation section, you may refer to the examples in `docs/Example.md`.
5. Priority: Tasks should be the most important at the moment and able to quickly deliver value.

> **Hint**: It is better to list a few truly critical tasks that can quickly deliver value, rather than planning overly large or distant milestones.
