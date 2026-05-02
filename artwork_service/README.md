# ArtworkService

FastAPI microservice for artwork data.

## Run with Docker Compose

This compose file does not use a `.env` file. Set environment variables in your shell or let Docker Compose use the defaults from `docker-compose.yml`.

PowerShell example:

```powershell
$env:DB_SERVER="your-sql-server.database.windows.net"
$env:DB_DATABASE="your-database"
$env:DB_USERNAME="your-username"
$env:DB_PASSWORD="your-password"
$env:ARTWORK_SERVICE_PORT="8001"
docker compose up --build
```

Open the API docs:

```text
http://localhost:8001/docs
```

## Run Tests in Docker

```powershell
docker compose build artwork-service
docker compose run --rm artwork-service pytest tests -v
```

## Azure Pipeline Variables

Before running `azure-pipelines.yml`, replace these variables with real Azure DevOps service connection and Azure resource names:

```yaml
dockerRegistryServiceConnection: 'CHANGE_ME_ACR_SERVICE_CONNECTION'
azureSubscription: 'CHANGE_ME_AZURE_RM_SERVICE_CONNECTION'
acrLoginServer: 'CHANGE_ME.azurecr.io'
resourceGroup: 'CHANGE_ME_RESOURCE_GROUP'
containerAppName: 'artwork-service'
```

The pipeline runs tests, builds the Docker image, pushes it to Azure Container Registry, and deploys it to Azure Container Apps.
