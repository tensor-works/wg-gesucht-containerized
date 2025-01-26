# Build the frontend if necessary\n\
if [ ! -d frontend/node_modules ] || [ ! -d frontend/dist ]; then
    echo "Building frontend..."
    cd frontend && npm install && npm run build && 
    npx shadcn@latest init --defaults -f && 
    npx shadcn@latest add card tabs button alert input badge textarea select checkbox label separator calendar
    cd ..
fi
# Start the frontend development server in the background (development mode only)\n\
if [ "$NODE_ENV" = "development" ]; then
    cd frontend && npm run dev & cd ..
fi

if [ $# -eq 0 ]; then
    exec /bin/bash
else
    exec "$@"
fi