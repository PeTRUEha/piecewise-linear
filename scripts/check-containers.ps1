<# Проверяет production-образы и health endpoints в изолированном Compose-проекте. #>

[CmdletBinding()]
param(
    [int]$Port = 18080,
    [string]$ProjectName = "piecewise-linear-check"
)

$ErrorActionPreference = "Stop"
$docker = if ($env:DOCKER_EXE) { $env:DOCKER_EXE } else { "docker" }
$compose = @("compose", "--project-name", $ProjectName, "-f", "compose.prod.yaml")
$env:POSTGRES_PASSWORD = "container-check-only"
$env:APP_PORT = [string]$Port
$baseUrl = "http://127.0.0.1:$Port"

function Assert-LastExitCode {
    <# Завершает проверку после неуспешной команды Docker. #>
    param([string]$Operation)
    if ($LASTEXITCODE -ne 0) {
        throw "$Operation завершилась с кодом $LASTEXITCODE"
    }
}

function Get-HttpStatus {
    <# Возвращает HTTP-статус, включая ответы 4xx и 5xx. #>
    param([string]$Uri)
    try {
        return [int](Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 15).StatusCode
    }
    catch {
        if ($null -ne $_.Exception.Response) {
            return [int]$_.Exception.Response.StatusCode
        }
        throw
    }
}

function Wait-HttpStatus {
    <# Ожидает заданный HTTP-статус с ограниченным числом попыток. #>
    param([string]$Uri, [int]$ExpectedStatus)
    foreach ($attempt in 1..30) {
        try {
            if ((Get-HttpStatus -Uri $Uri) -eq $ExpectedStatus) {
                return
            }
        }
        catch {
            if ($attempt -eq 30) {
                throw
            }
        }
        Start-Sleep -Seconds 1
    }
    throw "$Uri не вернул статус $ExpectedStatus"
}

try {
    & $docker @compose build
    Assert-LastExitCode -Operation "Сборка образов"
    & $docker @compose up --detach
    Assert-LastExitCode -Operation "Запуск Compose"

    Wait-HttpStatus -Uri "$baseUrl/api/v1/health/ready" -ExpectedStatus 200
    if ((Get-HttpStatus -Uri "$baseUrl/api/v1/health/live") -ne 200) {
        throw "Liveness не вернул 200 при доступной базе"
    }

    & $docker @compose exec -T backend python -c "import shutil, piecewise_linear; assert piecewise_linear.__file__; assert shutil.which('uv') is None"
    Assert-LastExitCode -Operation "Проверка backend-образа"
    & $docker @compose exec -T frontend nginx -t
    Assert-LastExitCode -Operation "Проверка frontend-образа"

    & $docker @compose stop db
    Assert-LastExitCode -Operation "Остановка PostgreSQL"
    Wait-HttpStatus -Uri "$baseUrl/api/v1/health/ready" -ExpectedStatus 503
    if ((Get-HttpStatus -Uri "$baseUrl/api/v1/health/live") -ne 200) {
        throw "Liveness зависит от доступности базы"
    }

    Write-Output "Проверка контейнеров и health endpoints пройдена"
}
finally {
    & $docker @compose down --volumes --remove-orphans
}
