# Algo Solver - Colima Setup Guide

This guide covers running Algo Solver with **Colima** (Lima for Docker on macOS) instead of Docker Desktop.

## What is Colima?

Colima is a lightweight alternative to Docker Desktop for macOS. It runs a minimal Linux VM using Lima and provides the Docker CLI.

## Prerequisites

1. **Colima installed**
   ```bash
   brew install colima
   ```

2. **Docker CLI** (usually included with Colima)
   ```bash
   colima --version
   ```

## Quick Start

### 1. Start Colima and Database

```bash
./colima-setup.sh up
```

This will:
- Start Colima (if not running)
- Start PostgreSQL container
- Wait for database to be ready

### 2. Start Backend & Frontend

In a new terminal:

```bash
./run.sh dev
```

This starts:
- **Backend**: http://localhost:8080
- **Frontend**: http://localhost:3000

## Other Useful Commands

### Check Status
```bash
./colima-setup.sh status
```

### View Logs
```bash
./colima-setup.sh logs
```

### Stop Everything
```bash
./colima-setup.sh down
```

## Troubleshooting

### "Cannot connect to Docker daemon"
Colima might not be running:
```bash
colima start
```

### "PostgreSQL fails to start"
View detailed logs:
```bash
./colima-setup.sh logs
```

Or check container status:
```bash
docker-compose ps
```

### "Port 5432 already in use"
Another PostgreSQL might be running:
```bash
# Stop everything first
./colima-setup.sh down

# Wait a moment, then start again
sleep 3
./colima-setup.sh up
```

### "Permission denied" on colima-setup.sh
Make it executable:
```bash
chmod +x colima-setup.sh
./colima-setup.sh up
```

## Database Connection

When Colima + PostgreSQL are running:

- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `algosolver`
- **User**: `postgres`
- **Password**: (none - trust auth)

This is configured in `application.properties`:
```properties
spring.datasource.url=jdbc:postgresql://localhost:5432/algosolver
spring.datasource.username=postgres
spring.datasource.password=postgres
```

## Docker Compose Integration

Your existing `docker-compose.yml` works as-is with Colima. After running `colima start`, you can use Docker commands normally:

```bash
# Start services defined in docker-compose.yml
docker-compose up -d

# View logs
docker-compose logs -f postgres

# Stop services
docker-compose down
```

## Performance Tips

1. **Allocate Resources** to Colima if needed:
   ```bash
   colima start --cpu 4 --memory 8
   ```

2. **Monitor Resource Usage**:
   ```bash
   colima status
   ```

## Next Steps

After setup is complete:

1. Access frontend: http://localhost:3000/?main=true
2. Backend API: http://localhost:8080
3. Database viewer: http://localhost:3000/?main=true → DATABASE tab

For more info, see the main [README.md](./README.md)
