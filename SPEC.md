# Graph Query Proxying App — Prototype Spec

## Overview

A web application that lets anonymous public users explore a Neo4j graph database by writing raw Cypher queries in the browser. The backend acts as a security proxy between the browser and Neo4j, enforcing read-only semantics and resource limits so that the underlying data can be explored freely without risk of mutation or abuse.

---

## Goals

- Allow fluid, open exploration of a public Neo4j dataset via raw Cypher
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
      | Bolt protocol (read-only user)
      v
Neo4j Database
```

The Neo4j instance is never directly reachable from the browser. All queries pass through the backend proxy.

---

## Components

### 1. Neo4j Database

- Runs in Docker
- Two database users:
  - `admin` — for data loading and maintenance, never used by the app
  - `readonly` — used exclusively by the backend; has only `READ` privileges, no write roles
- Configuration:
  - Query timeout set at the database level (`dbms.transaction.timeout`)
  - APOC plugin installed but with procedure restrictions (see security section)

### 2. Python Backend (FastAPI)

Responsible for all query safety and proxying.

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/query` | Execute a raw Cypher query (with all safety checks) |
| `GET`  | `/schema` | Return node labels, relationship types, and property keys |

**Dependencies:**
- `fastapi`, `uvicorn`
- `neo4j` (official Python driver)
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
CREATE, MERGE, DELETE, DETACH, SET, REMOVE, DROP, ALTER, RENAME,
LOAD CSV, CALL { ... } IN TRANSACTIONS, apoc.create, apoc.merge,
apoc.refactor, apoc.periodic
```

**CALL handling:**
- All `CALL` expressions are blocked by default
- A curated allowlist of safe read procedures may be permitted over time:
  - `apoc.path.*`, `apoc.algo.*`, `apoc.meta.*`
  - `db.labels`, `db.relationshipTypes`, `db.propertyKeys`

This layer gives early rejection with a clear error message to the user. It is defence-in-depth, not the primary control.

### Layer 2 — Result Limit Enforcement

- Every query is checked for a `LIMIT` clause before execution
- If absent, `LIMIT 500` is appended automatically
- If present and greater than 500, it is overridden to 500
- Prevents both bulk data extraction and runaway result sets

### Layer 3 — Read-Only Database User

The backend connects using the `readonly` user, which has only `READ` privileges at the Neo4j role level. Even if layers 1 and 2 are bypassed, the database will reject any write operation outright. This is the definitive safety guarantee.

### Layer 4 — Query Timeout + Rate Limiting

- Neo4j transaction timeout set at the database level (e.g. 10 seconds)
- The Python driver also sets a timeout on the session
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

The backend normalises all Neo4j results into a common response envelope:

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
  neo4j:     Neo4j database — ports 7474 (HTTP) and 7687 (Bolt), APOC enabled
  backend:   FastAPI app — port 8000
  frontend:  Next.js app — port 3000
```

- Environment variables control Neo4j connection details (URL, credentials)
- A `seed/` directory holds Cypher scripts to populate the database on first run
- `backend` and `frontend` mount source for hot-reload during development

---

## Project Structure (Proposed)

```
graph-query-proxying-app/
├── docker-compose.yml
├── neo4j/
│   ├── conf/              # neo4j.conf overrides (timeout, APOC config)
│   └── seed/              # initial data Cypher scripts
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── app/
│       ├── main.py
│       ├── query/
│       │   ├── validator.py   # keyword analysis + limit enforcement
│       │   └── executor.py    # Neo4j driver wrapper + timeout
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
- **Deployment**: Docker Compose maps naturally to Fly.io, Railway, or Render; Neo4j can move to AuraDB (managed)
- **Query logging**: anonymised logging of queries to tune rate limits and understand usage patterns
