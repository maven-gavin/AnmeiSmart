# Deployment Guide

This project includes Docker configuration for both the API (backend) and Web (frontend) services.

## Prerequisites

- Docker and Docker Compose installed
- Bash shell (for deployment script)

## Project Structure

- `api/`: Python FastAPI backend
- `web/`: Next.js frontend
- `scripts/`: Deployment scripts
- `docker-compose.yml`: Local development orchestration

## Configuration

1. Copy `env.example` to create environment-specific configuration files:
   ```bash
   cp env.example .env.dev
   cp env.example .env.prod
   ```
2. Edit the `.env.{env}` files with your specific configuration.

   **Important:**
   - `DATABASE_URL` in `.env.{env}` must be configured with your production database connection string.
     - Format: `postgresql://user:password@host:port/database`
     - **⚠️ Docker 环境注意事项:**
       - 如果数据库在**宿主机**上运行，不能使用 `localhost`（容器内的 localhost 指向容器自身）
       - 使用 `host.docker.internal` (macOS/Windows) 或宿主机 IP 地址
       - 示例: `postgresql://user:password@host.docker.internal:5432/database`
       - 如果数据库在**另一个容器**中，使用 Docker 网络中的服务名
       - 示例: `postgresql://user:password@postgres:5432/database`
   - `NEXT_PUBLIC_API_URL` in `.env.{env}` determines where the frontend makes API calls. 
     - For local dev: `http://localhost:8766`
     - For production: `https://api.yourdomain.com`

## Local Development

To run the stack locally:

```bash
docker compose up --build
```

## Automated Deployment (Jenkins)

The `scripts/deploy.sh` script automates the build and deployment process.

Usage:
```bash
./scripts/deploy.sh <environment>
```

Example:
```bash
./scripts/deploy.sh dev
```

This script will:
1. Load variables from `.env.<environment>`
2. Build the API Docker image
3. Build the Web Docker image (baking in `NEXT_PUBLIC_` variables)
4. Stop and remove old containers for this environment
5. Start new containers

**Database Migrations:**
- Database migrations are automatically executed when the API container starts
- The entrypoint script (`api/entrypoint.sh`) runs `alembic upgrade head` before starting the application
- The script includes automatic retry mechanism (default: 30 retries, 2 seconds interval)
- If migrations fail, the container will not start, preventing application errors
- Ensure `DATABASE_URL` is correctly configured in your `.env.{env}` file before deployment

**Migration Configuration (Optional):**
- `DB_MIGRATION_MAX_RETRIES`: Maximum retry attempts (default: 30)
- `DB_MIGRATION_RETRY_INTERVAL`: Retry interval in seconds (default: 2)
- `SKIP_DB_MIGRATION`: Set to `true` to skip migrations (default: false)

### Jenkins Pipeline Example

In your Jenkinsfile, you can use a shell step:

```groovy
stage('Deploy') {
    steps {
        sh 'chmod +x scripts/deploy.sh'
        sh './scripts/deploy.sh dev'
    }
}
```

