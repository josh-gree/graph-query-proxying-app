#!/usr/bin/env bash
# Creates the read-only user and grants appropriate permissions.
# Uses a shell script (rather than .sql) so that PG_READONLY_USER and
# PG_READONLY_PASSWORD can be injected from environment variables at runtime.
#
# Security posture note:
# Apache AGE's cypher() function is SECURITY INVOKER, meaning it executes
# with the calling user's privileges. Granting only SELECT on the movies
# schema tables and EXECUTE on ag_catalog functions therefore prevents the
# readonly user from issuing write Cypher commands at the database level.
# Layer 1 keyword analysis (see SPEC.md) serves as an additional control.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER ${PG_READONLY_USER} WITH PASSWORD '${PG_READONLY_PASSWORD}';

    GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO ${PG_READONLY_USER};

    GRANT USAGE ON SCHEMA ag_catalog TO ${PG_READONLY_USER};
    GRANT USAGE ON SCHEMA movies TO ${PG_READONLY_USER};

    GRANT SELECT ON ALL TABLES IN SCHEMA movies TO ${PG_READONLY_USER};
    ALTER DEFAULT PRIVILEGES IN SCHEMA movies GRANT SELECT ON TABLES TO ${PG_READONLY_USER};

    GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA ag_catalog TO ${PG_READONLY_USER};

    ALTER ROLE ${PG_READONLY_USER} SET search_path = ag_catalog, public;
EOSQL
