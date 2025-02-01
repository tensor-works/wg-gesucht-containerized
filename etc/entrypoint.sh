#!/bin/bash
exec 1> >(tee -a "/workspaces/wg-gesucht-containerized/entrypoint.log") 2>&1

# Load environment variables
source .env
export $(grep -v '^#' .env | xargs)

# Frontend setup
if [ ! -d frontend/node_modules ] || [ ! -d frontend/dist ]; then
    echo "Building frontend..."
    cd frontend && npm install && npm run build -y && \
    npx shadcn init --defaults -f && \
    npx shadcn add card tabs button alert input badge textarea select checkbox label separator calendar --yes --overwrite && \
    cd ..
fi

# Development server
if [ "$NODE_ENV" = "development" ]; then
    cd frontend && npm run dev & cd ..
fi

# PostgreSQL setup
if [ ! -d /workspaces/wg-gesucht-containerized/pgdata ]; then
    echo "Initializing PostgreSQL database..."
    mkdir -p /workspaces/wg-gesucht-containerized/pgdata
    chown postgres:postgres /workspaces/wg-gesucht-containerized/pgdata
    chmod 700 /workspaces/wg-gesucht-containerized/pgdata
    su - postgres -c "/usr/lib/postgresql/15/bin/initdb -D /workspaces/wg-gesucht-containerized/pgdata"
fi

# Start PostgreSQL
su - postgres -c "/usr/lib/postgresql/15/bin/pg_ctl start -D /workspaces/wg-gesucht-containerized/pgdata"

# Wait for PostgreSQL to start
echo "Waiting for PostgreSQL to start..."
sleep 5

# Initialize database schema
echo "Initializing database schema..."
envsubst < "$WORKDIR/assets/sql/init.sql" | su - postgres -c "psql -d postgres"

if [ "$REMOTE_CONTAINERS" = "true" ]; then
    exec "$@"
else
    exec /bin/bash
fi