-- Simple seed graph: people and the technologies they use
--
-- Every cypher() call must declare return columns with agtype aliases:
--
--   SELECT * FROM cypher('dev', $$
--     MATCH (n:Person {name: 'Alice'}) RETURN n
--   $$) AS (n agtype);
--
-- MERGE is used throughout for idempotency.


-- Nodes: Person
SELECT * FROM cypher('dev', $$ MERGE (n:Person {name: 'Alice', age: 30}) RETURN n $$) AS (n agtype);
SELECT * FROM cypher('dev', $$ MERGE (n:Person {name: 'Bob', age: 25}) RETURN n $$) AS (n agtype);
SELECT * FROM cypher('dev', $$ MERGE (n:Person {name: 'Carol', age: 35}) RETURN n $$) AS (n agtype);
SELECT * FROM cypher('dev', $$ MERGE (n:Person {name: 'Dave', age: 28}) RETURN n $$) AS (n agtype);

-- Nodes: Technology
SELECT * FROM cypher('dev', $$ MERGE (n:Technology {name: 'Python'}) RETURN n $$) AS (n agtype);
SELECT * FROM cypher('dev', $$ MERGE (n:Technology {name: 'Rust'}) RETURN n $$) AS (n agtype);
SELECT * FROM cypher('dev', $$ MERGE (n:Technology {name: 'PostgreSQL'}) RETURN n $$) AS (n agtype);
SELECT * FROM cypher('dev', $$ MERGE (n:Technology {name: 'Kubernetes'}) RETURN n $$) AS (n agtype);

-- KNOWS relationships
SELECT * FROM cypher('dev', $$
  MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
  MERGE (a)-[r:KNOWS]->(b) RETURN a, b
$$) AS (a agtype, b agtype);

SELECT * FROM cypher('dev', $$
  MATCH (a:Person {name: 'Bob'}), (b:Person {name: 'Carol'})
  MERGE (a)-[r:KNOWS]->(b) RETURN a, b
$$) AS (a agtype, b agtype);

SELECT * FROM cypher('dev', $$
  MATCH (a:Person {name: 'Carol'}), (b:Person {name: 'Dave'})
  MERGE (a)-[r:KNOWS]->(b) RETURN a, b
$$) AS (a agtype, b agtype);

SELECT * FROM cypher('dev', $$
  MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Dave'})
  MERGE (a)-[r:KNOWS]->(b) RETURN a, b
$$) AS (a agtype, b agtype);

-- USES relationships
SELECT * FROM cypher('dev', $$
  MATCH (p:Person {name: 'Alice'}), (t:Technology {name: 'Python'})
  MERGE (p)-[r:USES]->(t) RETURN p, t
$$) AS (p agtype, t agtype);

SELECT * FROM cypher('dev', $$
  MATCH (p:Person {name: 'Alice'}), (t:Technology {name: 'PostgreSQL'})
  MERGE (p)-[r:USES]->(t) RETURN p, t
$$) AS (p agtype, t agtype);

SELECT * FROM cypher('dev', $$
  MATCH (p:Person {name: 'Bob'}), (t:Technology {name: 'Rust'})
  MERGE (p)-[r:USES]->(t) RETURN p, t
$$) AS (p agtype, t agtype);

SELECT * FROM cypher('dev', $$
  MATCH (p:Person {name: 'Bob'}), (t:Technology {name: 'PostgreSQL'})
  MERGE (p)-[r:USES]->(t) RETURN p, t
$$) AS (p agtype, t agtype);

SELECT * FROM cypher('dev', $$
  MATCH (p:Person {name: 'Carol'}), (t:Technology {name: 'Python'})
  MERGE (p)-[r:USES]->(t) RETURN p, t
$$) AS (p agtype, t agtype);

SELECT * FROM cypher('dev', $$
  MATCH (p:Person {name: 'Carol'}), (t:Technology {name: 'Kubernetes'})
  MERGE (p)-[r:USES]->(t) RETURN p, t
$$) AS (p agtype, t agtype);

SELECT * FROM cypher('dev', $$
  MATCH (p:Person {name: 'Dave'}), (t:Technology {name: 'Rust'})
  MERGE (p)-[r:USES]->(t) RETURN p, t
$$) AS (p agtype, t agtype);

SELECT * FROM cypher('dev', $$
  MATCH (p:Person {name: 'Dave'}), (t:Technology {name: 'Kubernetes'})
  MERGE (p)-[r:USES]->(t) RETURN p, t
$$) AS (p agtype, t agtype);
