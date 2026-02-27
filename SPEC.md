# Graph Query Proxying App — Prototype Spec

## Overview

A web application that lets anonymous public users explore a graph database by writing raw Cypher queries in the browser. The backend acts as a security proxy between the browser and the database, enforcing read-only semantics and resource limits so that the underlying data can be explored freely without risk of mutation or abuse.

The database is **PostgreSQL with the Apache AGE extension**, which adds a Cypher-queryable property graph layer on top of Postgres. Queries are submitted as Cypher but executed via AGE's `cypher()` SQL wrapper under a read-only Postgres user.

---

## Goals

- Allow fluid, open exploration of a public graph dataset via raw Cypher
- Enforce read-only access via multiple independent layers
- Protect the database from resource abuse and denial-of-service
- Display results as both an interactive graph and a data table
- Local-first Docker Compose setup that is straightforward to promote to a deployed system

---

## Architecture

```
Browser (Next.js)
      |
      | HTTPS / REST
      v
Python Backend (FastAPI)
  - Query validation
  - Rate limiting
  - Result limiting
  - Query timeout enforcement
      |
      | PostgreSQL protocol (read-only user, psycopg2)
      v
PostgreSQL + Apache AGE
```

The database is never directly reachable from the browser. All queries pass through the backend proxy.

---

## Components

### 1. PostgreSQL + Apache AGE

- Runs in Docker (`apache/age` image, pinned by digest)
- `shared_preload_libraries=age` and `search_path=ag_catalog,public` set at server level
- Two database users:
  - `postgres` — superuser for init scripts and maintenance, never used by the app
  - `readonly` — used exclusively by the backend; has only `CONNECT`, `USAGE` on the graph schema, `SELECT` on graph tables, and `EXECUTE` on `ag_catalog` functions
- AGE's `cypher()` function is `SECURITY INVOKER`, so it executes with the calling user's privileges — the readonly user cannot issue write Cypher commands at the database level
- `statement_timeout` set at the session level by the backend to cap long-running queries
- Data persisted to a named Docker volume

### 2. Python Backend (FastAPI)

Responsible for all query safety and proxying.

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/query` | Execute a raw Cypher query (with all safety checks) |
| `GET`  | `/schema` | Return node labels, relationship types, and property keys |

**Dependencies:**
- `fastapi`, `uvicorn`
- `apache-age` Python driver (from `apache/age` repo, `drivers/python`) — wraps psycopg3 and parses `agtype` results into Vertex/Edge/Path objects
- `slowapi` (rate limiting)
- `pydantic` (request/response validation)

### 3. React / Next.js Frontend

- Cypher text editor with syntax highlighting (CodeMirror with Cypher language support)
- Submit button and keyboard shortcut to run queries
- Results displayed in two tabs:
  - **Graph view**: interactive node/edge visualisation (Cytoscape.js)
  - **Table view**: paginated property table (TanStack Table)
- Error messages surfaced clearly when queries are rejected or fail

---

## Security Model

Four independent layers — each one is a complete safeguard in its own right.

### Layer 1 — Static Keyword Analysis

Before executing any Cypher, the backend scans the query and rejects it if it contains write-intent keywords (case-insensitive, full-word match):

**Blocked:**
```
CREATE, MERGE, DELETE, DETACH, SET, REMOVE, DROP, ALTER, RENAME, LOAD CSV
```

This layer gives early rejection with a clear error message to the user. It is defence-in-depth, not the primary control.

### Layer 2 — Result Limit Enforcement

- Every query is checked for a `LIMIT` clause before execution
- If absent, `LIMIT 500` is appended automatically
- If present and greater than 500, it is overridden to 500
- Prevents both bulk data extraction and runaway result sets

### Layer 3 — Read-Only Database User

The backend connects using the `readonly` Postgres user. This user has only `SELECT` on the graph schema tables and no `INSERT`/`UPDATE`/`DELETE` privileges. Because AGE's `cypher()` is `SECURITY INVOKER`, even a `MERGE` or `CREATE` issued through `cypher()` will be rejected by Postgres — the user lacks the underlying write privileges. This is the definitive safety guarantee.

### Layer 4 — Query Timeout + Rate Limiting

- `statement_timeout` set on each connection before query execution (e.g. 10 seconds)
- Per-IP rate limiting via `slowapi` (e.g. 20 queries / minute)
- Queries exceeding the timeout are terminated; clients exceeding the rate limit receive HTTP 429

### What This Does Not Protect Against

- **Data exfiltration**: not a concern — data is fully public
- **Schema discovery**: not restricted — labels, types, and properties are intentionally exposable

---

## Data Display

### Graph View

- Library: **Cytoscape.js**
- Nodes rendered with their label and a configurable primary property (e.g. `name`)
- Edges rendered with relationship type
- Layout: force-directed by default, switchable (breadthfirst, concentric, grid)
- Click a node or edge to see all properties in a side panel

### Table View

- Library: **TanStack Table v8**
- Flattened rows from `RETURN` values — handles nodes, relationships, and primitives
- Sortable columns, client-side pagination
- Downloadable as CSV

### Result Format

The AGE Python driver deserialises `agtype` results into Vertex/Edge/Path objects. The backend normalises these into a common response envelope:

```json
{
  "nodes": [...],
  "edges": [...],
  "rows": [...],
  "columns": [...],
  "truncated": true,
  "row_count": 342
}
```

The frontend uses the presence of `nodes`/`edges` vs `rows` to decide which view to emphasise by default.

---

## Docker Compose Setup

```
services:
  postgres:  Apache AGE (PostgreSQL 18) — port 5432, named volume for data
  backend:   FastAPI app — port 8000
  frontend:  Next.js app — port 3000
```

- Environment variables control database connection details (see `.env.example`)
- `postgres/init/` holds SQL and shell scripts run by `docker-entrypoint-initdb.d` on first start
- `backend` and `frontend` mount source for hot-reload during development

---

## Project Structure (Proposed)

```
graph-query-proxying-app/
├── docker-compose.yml
├── .env.example
├── postgres/
│   └── init/
│       ├── 01_setup_age.sql   # enable AGE extension, create graph
│       ├── 02_users.sh        # create readonly user, grant privileges
│       └── 03_data.sql        # seed data
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── app/
│       ├── main.py
│       ├── query/
│       │   ├── validator.py   # keyword analysis + limit enforcement
│       │   └── executor.py    # AGE driver wrapper + timeout
│       ├── routes/
│       │   ├── query.py
│       │   └── schema.py
│       └── models.py
└── frontend/
    ├── Dockerfile
    ├── package.json
    └── src/
        ├── components/
        │   ├── GraphView.tsx
        │   ├── TableView.tsx
        │   └── CypherEditor.tsx
        └── pages/
            └── index.tsx
```

---

## Open Questions / Future Decisions

- **Query templates**: predefined parameterised queries could be added as a second mode once the raw Cypher prototype is proven
- **Authentication for advanced mode**: if abuse becomes an issue, gating raw Cypher behind a login or API key is a natural next step
- **Query history**: browser localStorage for UX convenience
- **Shareable links**: encode a query in the URL so results can be shared
- **Deployment**: Docker Compose maps naturally to Fly.io, Railway, or Render; Postgres can move to a managed provider (Supabase, Railway Postgres, etc.)
- **Query logging**: anonymised logging of queries to tune rate limits and understand usage patterns
