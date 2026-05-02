#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick start script for Artwork Auction Microservices
.DESCRIPTION
    Runs all microservices with Docker
.EXAMPLE
    .\start.ps1
    .\start.ps1 -Build
    .\start.ps1 -Test
    .\start.ps1 -Stop
#>

param(
    [switch]$Build,
    [switch]$Test,
    [switch]$Stop,
    [switch]$Logs,
    [switch]$Clean
)

# Get the root directory (where this script is located)
$rootDir = (Get-Item -Path "." -Verbose).FullName
$dockerComposeFile = Join-Path $rootDir "docker-compose.yml"

function Write-Header {
    param([string]$Message)
    Write-Host "`n" -NoNewline
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[FAIL] $Message" -ForegroundColor Red
}

function Test-Docker {
    try {
        docker --version | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Test-DockerCompose {
    try {
        docker-compose --version | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# ═══════════════════════════════════════════════════════════════
# Check prerequisites
# ═══════════════════════════════════════════════════════════════

Write-Header "[*] Checking Prerequisites"

if (-not (Test-Docker)) {
    Write-Error-Custom "Docker is not installed or not in PATH"
    Write-Host "   Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
}

if (-not (Test-DockerCompose)) {
    Write-Error-Custom "Docker Compose is not installed or not in PATH"
    Write-Host "   Docker Compose should come with Docker Desktop"
    exit 1
}

Write-Success "Docker found: $(docker --version)"
Write-Success "Docker Compose found: $(docker-compose --version)"

# ═══════════════════════════════════════════════════════════════
# Check .env file
# ═══════════════════════════════════════════════════════════════

$envFile = Join-Path $rootDir ".env"
$envExampleFile = Join-Path $rootDir ".env.example"

if (-not (Test-Path $envFile)) {
    Write-Header "[*] Creating .env from template"
    if (Test-Path $envExampleFile) {
        Copy-Item $envExampleFile $envFile
        Write-Success "Created .env from .env.example"
    }
    else {
        Write-Error-Custom ".env.example not found"
        exit 1
    }
}

# ═══════════════════════════════════════════════════════════════
# Handle commands
# ═══════════════════════════════════════════════════════════════

if ($Stop) {
    Write-Header "[*] Stopping Docker Compose Services"
    docker-compose -f $dockerComposeFile down
    Write-Success "Services stopped"
    exit 0
}

if ($Clean) {
    Write-Header "[*] Cleaning Up Docker Compose (including volumes)"
    docker-compose -f $dockerComposeFile down -v
    Write-Success "Services and volumes removed"
    exit 0
}

if ($Logs) {
    Write-Header "[*] Docker Compose Logs (Follow Mode)"
    docker-compose -f $dockerComposeFile logs -f
    exit 0
}

if ($Test) {
    Write-Header "[*] Running Tests"
    
    Write-Host "`n[>>] Testing bid_service..." -ForegroundColor Yellow
    docker-compose -f $dockerComposeFile exec -T bid-service pytest /app/bid_service/tests/ -v
    
    Write-Host "`n[>>] Testing dispute_service..." -ForegroundColor Yellow
    docker-compose -f $dockerComposeFile exec -T dispute-service pytest /app/dispute_service/tests/ -v
    
    Write-Host "`n[>>] Testing artwork_service..." -ForegroundColor Yellow
    docker-compose -f $dockerComposeFile exec -T artwork-service pytest /app/artwork_service/tests/ -v
    
    Write-Success "All tests completed"
    exit 0
}

# ═══════════════════════════════════════════════════════════════
# Normal startup
# ═══════════════════════════════════════════════════════════════

Write-Header "[>>] Starting Artwork Auction Microservices"

if ($Build) {
    Write-Host "Building images..." -ForegroundColor Yellow
    docker-compose -f $dockerComposeFile up --build -d
}
else {
    docker-compose -f $dockerComposeFile up -d
}

# Wait for services to start
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Health checks
Write-Host "`nPerforming health checks..." -ForegroundColor Yellow

$services = @(
    @{ name = "artwork-service"; port = 8001; url = "http://localhost:8001/docs" },
    @{ name = "bid-service"; port = 8002; url = "http://localhost:8002/docs" },
    @{ name = "dispute-service"; port = 8003; url = "http://localhost:8003/docs" },
    @{ name = "mssql-db"; port = 1433; isDb = $true }
)

$allHealthy = $true

foreach ($service in $services) {
    try {
        if ($service.isDb) {
            $result = docker-compose -f $dockerComposeFile exec -T mssql-db /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P ChangeMe_12345 -Q "SELECT 1" 2>&1
            if ($result -match "1") {
                Write-Success "$($service.name) is healthy"
            }
            else {
                Write-Error-Custom "$($service.name) is not responding"
                $allHealthy = $false
            }
        }
        else {
            $response = Invoke-WebRequest -Uri $service.url -SkipCertificateCheck -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Success "$($service.name) is healthy"
            }
            else {
                Write-Error-Custom "$($service.name) returned status $($response.StatusCode)"
                $allHealthy = $false
            }
        }
    }
    catch {
        Write-Host "[..] Waiting for $($service.name)..." -ForegroundColor Yellow
    }
}

Write-Header "Service Overview"

Write-Host "Artwork Service:  http://localhost:8001/docs"
Write-Host "Bid Service:      http://localhost:8002/docs"
Write-Host "Dispute Service:  http://localhost:8003/docs"
Write-Host "MSSQL Database:   localhost:1433"
Write-Host ""
Write-Host "Credentials:"
Write-Host "  Username: sa"
Write-Host "  Password: ChangeMe_12345"
Write-Host ""
Write-Host "Docker Compose Status:" -ForegroundColor Cyan

docker-compose -f $dockerComposeFile ps

Write-Header "[*] Ready to Go!"

Write-Host @"
Next steps:
  1. Open Swagger UI: http://localhost:8001/docs
  2. Create some test data
  3. Run tests: .\start.ps1 -Test
  4. View logs: .\start.ps1 -Logs
  5. Stop services: .\start.ps1 -Stop

For more information, see:
  - README.md
  - SETUP.md
  - SECURITY.md
"@ -ForegroundColor Green

# ═══════════════════════════════════════════════════════════════
# Keep services running
# ═══════════════════════════════════════════════════════════════

Write-Host "`nPress Ctrl+C to stop services..." -ForegroundColor Yellow
while ($true) {
    Start-Sleep -Seconds 60
}
