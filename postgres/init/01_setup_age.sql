CREATE EXTENSION IF NOT EXISTS age;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM ag_catalog.ag_graph WHERE name = 'dev') THEN
        PERFORM create_graph('dev');
    END IF;
END;
$$;
