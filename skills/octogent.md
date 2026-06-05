# Octogent Skill

Octogent is a multi-agent orchestration framework for Claude Code that treats terminal coding agents as building blocks within an orchestration layer. It provides **tentacles** as scoped context containers for work delegation.

## Core Concept: Tentacles

A **tentacle** is a folder under `.octogent/tentacles/<tentacle-id>/` containing agent-readable markdown files.

### Required Files

| File | Purpose |
|------|---------|
| `CONTEXT.md` | Explains the work area, important files, constraints |
| `todo.md` | Executable task list with checkbox items |

### Optional Files

- Any additional `.md` files become "vault files" surfaced in the UI
- Notes, handoffs, implementation details

## Tentacle Structure

```
.octogent/tentacles/<tentacle-id>/
├── CONTEXT.md      # Area explanation (required)
├── todo.md         # Task list (required)
└── notes.md        # Additional notes (optional)
```

## CONTEXT.md Format

```md
# Tentacle Name

Brief description of what this area owns.

## Overview
What this area does, important files, what already exists.

## Constraints
Edge cases, what not to break, security boundaries.

## Dependencies
What this area depends on, integration points.

## Suggested Skills
Any relevant Claude Code skills for this tentacle.
```

## todo.md Format

Only markdown checkbox lines are parsed:

```md
# Todo

- [ ] add request validation for monitor config
- [ ] cover the invalid payload case in tests
- [x] wire the route into the request handler
```

### Parsing Rules

- `- [ ] text` = incomplete task
- `- [x] text` or `- [X] text` = complete task
- Order matters (swarm uses index)
- Other markdown is allowed but ignored

### Good vs Bad Todo Items

**Good:** Specific, testable, narrow enough for one agent
```md
- [ ] add API route for terminal rename
```

**Bad:** Vague, requires rediscovering the assignment
```md
- [ ] work on the API
```

## Agent Workflow Patterns

### Single-Item Solve

1. Read tentacle's `CONTEXT.md` and `todo.md`
2. Pick one checkbox item
3. Create terminal with task context
4. Execute and mark done in `todo.md`

### Swarm Pattern

1. Parse incomplete items from `todo.md`
2. Create worker terminals for each item
3. Parent coordinator supervises completion
4. Update `todo.md` after review

### Delegation Flow

```
Developer/Parent Agent
    │
    ├──► Define job boundary
    │
    ├──► Create/update tentacle files
    │         │
    │         ├──► CONTEXT.md (area context)
    │         └──► todo.md (task list)
    │
    ├──► Spawn workers from todo items
    │
    ├──► Workers report via short messages + files
    │
    └──► Parent reviews, updates todo.md
```

## Key Principles

1. **Durable context in files** - Important info should be in markdown, not chat history
2. **One tentacle per work area** - Keep contexts isolated
3. **Todo order matters** - Swarm uses positional indices
4. **Small, specific tasks** - Each item should be one child-agent assignment
5. **Incremental progress** - Prefer small working steps over broad rewrites

## When to Use Tentacles

**Use for:**
- API runtime work
- Frontend components
- Database migrations
- Multi-module projects (like Odoo MCP Connector)
- Parallel work that needs a source of truth

**Don't overuse:**
- Simple one-off tasks
- Single-terminal work
- When chat context is sufficient

## Octogent Mental Model

```
Human Developer
    │
    ├──► Define boundaries
    │
    ├──► Create tentacles
    │         │
    │         └──► .octogent/tentacles/<id>/
    │                   ├── CONTEXT.md
    │                   └── todo.md
    │
    ├──► Spawn workers/coordinators
    │
    └──► Review and merge
              │
              └──► Update tentacle files
```

## Verification Commands

```bash
# Build the project
pnpm build

# Run tests
pnpm test

# Lint
pnpm lint

# Format
pnpm format
```

## For Odoo MCP Connector Implementation

Apply octogent principles:

1. **Create tentacles for each module:**
   - `odoo-mcp-connector/tentacles/foundation/` - Core server, config, connection
   - `odoo-mcp-connector/tentacles/crm/` - CRM module tools
   - `odoo-mcp-connector/tentacles/accounting/` - Accounting module tools
   - `odoo-mcp-connector/tentacles/sales/` - Sales module tools
   - `odoo-mcp-connector/tentacles/purchase/` - Purchase module tools
   - `odoo-mcp-connector/tentacles/inventory/` - Inventory module tools
   - `odoo-mcp-connector/tentacles/expenses/` - Expenses module tools
   - `odoo-mcp-connector/tentacles/lead-automation/` - Multi-channel lead capture

2. **Each tentacle contains:**
   - `CONTEXT.md` - Module overview, Odoo models, key operations
   - `todo.md` - Specific implementation tasks

3. **Spawn parallel workers for independent modules**

4. **Coordinator handles cross-module integration**

## Reference

- Project: https://github.com/hesamsheikh/octogent
- Docs: `docs/concepts/tentacles.md`, `docs/guides/working-with-todos.md`
