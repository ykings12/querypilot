#!/usr/bin/env bash
# Load Chinook sample database into target Postgres (localhost:5433 by default).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

HOST="${CHINOOK_HOST:-localhost}"
PORT="${CHINOOK_PORT:-5433}"
USER="${CHINOOK_USER:-querypilot}"
DB="${CHINOOK_DB:-chinook}"
PASSWORD="${CHINOOK_PASSWORD:-querypilot}"

CHINOOK_URL="https://raw.githubusercontent.com/lerocha/chinook-database/master/ChinookDatabase/DataSources/Chinook_PostgreSql.sql"
TMP_SQL="$(mktemp /tmp/chinook.XXXXXX.sql)"
FILTERED_SQL="$(mktemp /tmp/chinook_filtered.XXXXXX.sql)"
trap 'rm -f "$TMP_SQL" "$FILTERED_SQL"' EXIT

echo "Downloading Chinook Postgres schema + data..."
curl -fsSL "$CHINOOK_URL" -o "$TMP_SQL"

# Docker Postgres already creates database $DB; strip DROP/CREATE DATABASE and \\c meta commands.
grep -Ev '^(DROP DATABASE|CREATE DATABASE|\\c )' "$TMP_SQL" > "$FILTERED_SQL"

run_psql() {
  local database=$1
  local file=$2
  if command -v psql >/dev/null 2>&1; then
    PGPASSWORD="$PASSWORD" psql -h "$HOST" -p "$PORT" -U "$USER" -d "$database" -v ON_ERROR_STOP=1 -f "$file"
  else
    docker compose exec -T target-db psql -U "$USER" -d "$database" -v ON_ERROR_STOP=1 -f - < "$file"
  fi
}

run_psql_query() {
  local database=$1
  local query=$2
  if command -v psql >/dev/null 2>&1; then
    PGPASSWORD="$PASSWORD" psql -h "$HOST" -p "$PORT" -U "$USER" -d "$database" -tAc "$query"
  else
    docker compose exec -T target-db psql -U "$USER" -d "$database" -tAc "$query"
  fi
}

CHINOOK_FORCE="${CHINOOK_FORCE:-0}"
already_seeded="$(run_psql_query "$DB" "SELECT to_regclass('public.album') IS NOT NULL")"
already_seeded="${already_seeded//[[:space:]]/}"

if [[ "$already_seeded" == "t" && "$CHINOOK_FORCE" != "1" ]]; then
  echo "Chinook tables already exist in ${USER}@${HOST}:${PORT}/${DB}; skipping schema/data load."
  echo "Set CHINOOK_FORCE=1 to drop public schema and reload."
elif [[ "$already_seeded" == "t" && "$CHINOOK_FORCE" == "1" ]]; then
  echo "CHINOOK_FORCE=1 — dropping public schema before reload..."
  run_psql_query "$DB" "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO ${USER}; GRANT ALL ON SCHEMA public TO public;"
  echo "Loading tables + data into ${USER}@${HOST}:${PORT}/${DB}..."
  run_psql "$DB" "$FILTERED_SQL"
else
  echo "Loading tables + data into ${USER}@${HOST}:${PORT}/${DB}..."
  run_psql "$DB" "$FILTERED_SQL"
fi

echo "Creating read-only role..."
run_psql "$DB" "eval/seed/create_readonly_role.sql"

echo "Chinook seed complete."
