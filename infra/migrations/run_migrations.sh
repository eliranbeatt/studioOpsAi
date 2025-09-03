#!/bin/bash
# Migration runner for StudioOps AI database

set -e

PSQL="psql -U studioops -d studioops -h localhost -p 5432"

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until $PSQL -c "SELECT 1" > /dev/null 2>&1; do
  sleep 1
done

echo "PostgreSQL is ready. Running migrations..."

# Run migrations in order
for migration_file in $(ls -1 *.sql | sort); do
    echo "Applying migration: $migration_file"
    $PSQL -f "$migration_file"
done

echo "All migrations completed successfully!"