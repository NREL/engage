#!/usr/bin/env bash

echo "Waiting for PostgreSQL..."

while ! pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT; do
  sleep 0.1
done

echo "PostgreSQL started!"

exec "$@"
