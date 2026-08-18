-- Read-only role for QueryPilot (Chinook target DB, local dev)
-- Password matches READONLY_PASSWORD in .env.example

DO $do$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'querypilot_readonly') THEN
    CREATE ROLE querypilot_readonly LOGIN PASSWORD 'querypilot_readonly_dev';
  END IF;
END
$do$;

GRANT CONNECT ON DATABASE chinook TO querypilot_readonly;
GRANT USAGE ON SCHEMA public TO querypilot_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO querypilot_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO querypilot_readonly;
