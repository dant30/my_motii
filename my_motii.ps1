#Requires -Version 5.1
<#
.SYNOPSIS
    Scaffolds the my_motii monorepo: multi-tenant AutoSpare SaaS.

.DESCRIPTION
    Creates the complete folder and file structure for my_motii.

    Key fixes vs. the initial version:
      * Uses single-quoted here-strings (@'...'@) for any content that
        contains a literal dollar sign (nginx $uri, JSON $schema, Makefile,
        shell scripts). This avoids "The variable '$uri' cannot be retrieved".
      * Writes files as UTF-8 WITHOUT BOM, so Linux shell scripts and
        config files stay valid (a BOM would break the shebang line).
      * Idempotent: re-running only creates missing items unless -Force.
      * Removed unused helpers.

.PARAMETER RootPath
    Destination folder. Defaults to .\my_motii in the current directory.

.PARAMETER Force
    Overwrite existing files. Directories are always safe to re-run.

.EXAMPLE
    PS C:\Users\dante> .\my_motii.ps1

.EXAMPLE
    PS C:\Users\dante> .\my_motii.ps1 -RootPath D:\projects\my_motii -Force
#>

[CmdletBinding()]
param(
    [string]$RootPath = (Join-Path (Get-Location).Path 'my_motii'),
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# =============================================================================
# Counters
# =============================================================================
$script:DirsCreated  = 0
$script:FilesCreated = 0
$script:FilesSkipped = 0

# =============================================================================
# Output helpers
# =============================================================================
function Write-Section {
    param([string]$T)
    Write-Host ""
    Write-Host ">> $T" -ForegroundColor Cyan
}

# =============================================================================
# Filesystem helpers
# =============================================================================
$script:Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function New-Dir {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        $script:DirsCreated++
    }
}

function New-FileContent {
    param(
        [Parameter(Mandatory)][string]$Path,
        [string]$Content = ""
    )
    if ((Test-Path -LiteralPath $Path) -and (-not $Force)) {
        $script:FilesSkipped++
        return
    }
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent)) { New-Dir -Path $parent }

    # UTF-8 without BOM: safe for .sh, .env, .json, .yml, .py
    [System.IO.File]::WriteAllText($Path, $Content, $script:Utf8NoBom)
    $script:FilesCreated++
}

function New-PyInit { param([string]$Dir) New-FileContent -Path (Join-Path $Dir '__init__.py') -Content '' }
function New-PyFile {
    param([string]$Path, [string]$Doc = 'Module.')
    New-FileContent -Path $Path -Content ('"""' + $Doc + '"""')
}
function New-MdFile {
    param([string]$Path, [string]$Title = 'Document')
    New-FileContent -Path $Path -Content ("# $Title`n`nTODO.`n")
}
function New-Gitkeep { param([string]$Dir) New-FileContent -Path (Join-Path $Dir '.gitkeep') -Content '' }
function New-JsonFile {
    param([string]$Path, [string]$Content = '{}')
    New-FileContent -Path $Path -Content $Content
}

# =============================================================================
# Django app factory — canonical template
# =============================================================================
function New-DjangoApp {
    param(
        [Parameter(Mandatory)][string]$AppsRoot,
        [Parameter(Mandatory)][string]$Name,
        [string[]]$Models        = @(),
        [string[]]$Services      = @(),
        [string[]]$Selectors     = @(),
        [string[]]$ExtraPackages = @(),
        [hashtable]$PackageFiles = @{},
        [string[]]$ExtraDirs     = @()
    )
    $root = Join-Path $AppsRoot $Name
    New-Dir -Path $root
    New-PyInit -Dir $root

    New-PyFile -Path (Join-Path $root 'apps.py')        -Doc "$Name app configuration."
    New-PyFile -Path (Join-Path $root 'admin.py')       -Doc "$Name Django admin registration."
    New-PyFile -Path (Join-Path $root 'urls.py')        -Doc "$Name URL configuration."
    New-PyFile -Path (Join-Path $root 'permissions.py') -Doc "$Name DRF/FastAPI permissions."
    New-PyFile -Path (Join-Path $root 'middleware.py')  -Doc "$Name middleware."
    New-PyFile -Path (Join-Path $root 'signals.py')     -Doc "$Name signal receivers."
    New-PyFile -Path (Join-Path $root 'tasks.py')       -Doc "$Name Celery tasks."
    New-MdFile -Path (Join-Path $root 'README.md')      -Title $Name

    foreach ($pkg in @('models','serializers','services','selectors','views','migrations','tests')) {
        $p = Join-Path $root $pkg
        New-Dir -Path $p
        New-PyInit -Dir $p
    }
    New-PyFile -Path (Join-Path $root 'views\api_views.py')   -Doc "$Name client-facing views."
    New-PyFile -Path (Join-Path $root 'views\admin_views.py') -Doc "$Name platform-admin views."

    foreach ($m   in $Models)    { New-PyFile -Path (Join-Path $root "models\$m.py")      -Doc "$Name model: $m." }
    foreach ($s   in $Services)  { New-PyFile -Path (Join-Path $root "services\$s.py")    -Doc "$Name service: $s." }
    foreach ($sel in $Selectors) { New-PyFile -Path (Join-Path $root "selectors\$sel.py") -Doc "$Name selector: $sel." }

    foreach ($ep in $ExtraPackages) {
        $epDir = Join-Path $root $ep
        New-Dir -Path $epDir
        New-PyInit -Dir $epDir
        if ($PackageFiles.ContainsKey($ep)) {
            foreach ($f in $PackageFiles[$ep]) {
                New-PyFile -Path (Join-Path $epDir "$f.py") -Doc "$Name/$ep :: $f."
            }
        }
    }

    foreach ($d in $ExtraDirs) { New-Dir -Path (Join-Path $root $d) }

    $testFiles = @(
        'conftest.py','factories.py','test_models.py','test_services.py',
        'test_selectors.py','test_api_views.py','test_admin_views.py',
        'test_permissions.py','test_tasks.py','test_signals.py'
    )
    foreach ($tf in $testFiles) {
        New-PyFile -Path (Join-Path $root "tests\$tf") -Doc "$Name tests: $tf."
    }
}

# =============================================================================
# PREFLIGHT
# =============================================================================
Write-Host ""
Write-Host "===========================================================" -ForegroundColor Magenta
Write-Host "  my_motii  |  AutoSpare SaaS scaffold" -ForegroundColor Magenta
Write-Host "  Target:   $RootPath"                  -ForegroundColor Magenta
Write-Host "  Force:    $Force"                     -ForegroundColor Magenta
Write-Host "===========================================================" -ForegroundColor Magenta

New-Dir -Path $RootPath
$backend   = Join-Path $RootPath 'backend'
$core      = Join-Path $backend  'core'
$appsRoot  = Join-Path $core     'apps'
$sharedPkg = Join-Path $backend  'shared'
$apiRoot   = Join-Path $backend  'api'
$frontend  = Join-Path $RootPath 'frontend'
$feApps    = Join-Path $frontend 'apps'
$fePkg     = Join-Path $frontend 'packages'

# =============================================================================
# 1 · ROOT FILES
# =============================================================================
Write-Section "Root files"

New-MdFile -Path (Join-Path $RootPath 'README.md') -Title 'my_motii'

New-FileContent -Path (Join-Path $RootPath '.gitignore') -Content @'
# Python
__pycache__/
*.py[cod]
.venv/
venv/
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Node
node_modules/
.pnpm-store/
dist/
build/
.next/
.turbo/

# Env
.env
.env.local
*.local

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Project
database/backups/*
!database/backups/.gitkeep
frontend/packages/api-client/generated/*
!frontend/packages/api-client/generated/.gitkeep
'@

New-FileContent -Path (Join-Path $RootPath '.editorconfig') -Content @'
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space

[*.py]
indent_size = 4

[*.{js,ts,tsx,jsx,json,yml,yaml,md}]
indent_size = 2
'@

New-FileContent -Path (Join-Path $RootPath '.dockerignore') -Content @'
.git
.github
node_modules
**/node_modules
.venv
**/__pycache__
**/*.pyc
docs
*.md
.env
.env.*
!.env.example
'@

New-FileContent -Path (Join-Path $RootPath '.env.example') -Content @'
# ---- Django ----
DJANGO_SETTINGS_MODULE=config.settings.development
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# ---- Postgres ----
POSTGRES_DB=my_motii
POSTGRES_USER=my_motii
POSTGRES_PASSWORD=change-me
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# ---- Redis ----
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# ---- FastAPI ----
API_HOST=0.0.0.0
API_PORT=8001
API_JWT_SECRET=change-me

# ---- Kenya integrations ----
MPESA_CONSUMER_KEY=
MPESA_CONSUMER_SECRET=
MPESA_SHORTCODE=
MPESA_PASSKEY=
MPESA_ENV=sandbox

ETIMS_BASE_URL=
ETIMS_TIN=
ETIMS_BHF_ID=
ETIMS_DEVICE_SERIAL=
ETIMS_CLIENT_ID=
ETIMS_CLIENT_SECRET=

WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_VERIFY_TOKEN=

SMS_PROVIDER=africastalking
SMS_API_KEY=
SMS_USERNAME=
'@

New-FileContent -Path (Join-Path $RootPath 'pyproject.toml') -Content @'
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E","F","W","I","N","UP","B","C4","SIM","RUF"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
strict = true
plugins = ["mypy_django_plugin.main"]

[tool.pytest.ini_options]
testpaths = ["backend/core/tests","backend/api/tests","tests"]
python_files = ["test_*.py"]
addopts = "-ra --strict-markers"
'@

New-FileContent -Path (Join-Path $RootPath 'package.json') -Content @'
{
  "name": "my-motii",
  "private": true,
  "packageManager": "pnpm@9.0.0",
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "lint": "turbo run lint",
    "test": "turbo run test"
  },
  "devDependencies": {
    "turbo": "^2.0.0",
    "typescript": "^5.5.0"
  }
}
'@

New-FileContent -Path (Join-Path $RootPath 'pnpm-workspace.yaml') -Content @'
packages:
  - "frontend/apps/*"
  - "frontend/packages/*"
  - "frontend/tooling/*"
'@

New-FileContent -Path (Join-Path $RootPath 'docker-compose.yml') -Content @'
services:
  postgres:
    image: postgres:16
    env_file: .env
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./infra/docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports: ["5432:5432"]

  redis:
    image: redis:7
    command: redis-server /usr/local/etc/redis/redis.conf
    volumes:
      - ./infra/docker/redis/redis.conf:/usr/local/etc/redis/redis.conf:ro
    ports: ["6379:6379"]

  api:
    build:
      context: .
      dockerfile: infra/docker/backend.Dockerfile
    command: ["/app/infra/scripts/entrypoint-api.sh"]
    env_file: .env
    depends_on: [postgres, redis]
    ports: ["8001:8001"]

  core:
    build:
      context: .
      dockerfile: infra/docker/backend.Dockerfile
    command: ["gunicorn","config.wsgi:application","-b","0.0.0.0:8000"]
    working_dir: /app/backend/core
    env_file: .env
    depends_on: [postgres, redis]
    ports: ["8000:8000"]

  worker:
    build:
      context: .
      dockerfile: infra/docker/worker.Dockerfile
    command: ["/app/infra/scripts/entrypoint-worker.sh"]
    env_file: .env
    depends_on: [postgres, redis]

  beat:
    build:
      context: .
      dockerfile: infra/docker/worker.Dockerfile
    command: ["/app/infra/scripts/entrypoint-beat.sh"]
    env_file: .env
    depends_on: [postgres, redis]

  nginx:
    image: nginx:1.27
    volumes:
      - ./infra/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./infra/nginx/conf.d:/etc/nginx/conf.d:ro
    ports: ["80:80"]
    depends_on: [api, core]

volumes:
  pgdata:
'@

New-FileContent -Path (Join-Path $RootPath 'docker-compose.override.yml') -Content @'
services: {}
'@

New-FileContent -Path (Join-Path $RootPath 'Makefile') -Content @'
.PHONY: up down logs test lint fmt migrate seed

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

migrate:
	docker compose exec core python manage.py migrate

seed:
	docker compose exec core python manage.py shell < backend/core/scripts/seed_demo_tenant.py

test:
	docker compose exec core pytest
	docker compose exec api pytest

lint:
	ruff check backend
	mypy backend
	pnpm -r lint

fmt:
	ruff format backend
	pnpm -r format
'@

# =============================================================================
# 2 · .github / workflows
# =============================================================================
Write-Section "GitHub workflows"
$gh = Join-Path $RootPath '.github\workflows'
New-Dir -Path $gh

New-FileContent -Path (Join-Path $gh 'ci.yml')            -Content "name: CI`non: [push, pull_request]`njobs:`n  placeholder:`n    runs-on: ubuntu-latest`n    steps:`n      - uses: actions/checkout@v4`n"
New-FileContent -Path (Join-Path $gh 'lint.yml')          -Content "name: Lint`non: [push, pull_request]`njobs:`n  placeholder:`n    runs-on: ubuntu-latest`n    steps:`n      - uses: actions/checkout@v4`n"
New-FileContent -Path (Join-Path $gh 'test-backend.yml')  -Content "name: Backend tests`non: [push, pull_request]`njobs:`n  placeholder:`n    runs-on: ubuntu-latest`n    steps:`n      - uses: actions/checkout@v4`n"
New-FileContent -Path (Join-Path $gh 'test-frontend.yml') -Content "name: Frontend tests`non: [push, pull_request]`njobs:`n  placeholder:`n    runs-on: ubuntu-latest`n    steps:`n      - uses: actions/checkout@v4`n"
New-FileContent -Path (Join-Path $gh 'build-images.yml')  -Content "name: Build images`non: [push]`njobs:`n  placeholder:`n    runs-on: ubuntu-latest`n    steps:`n      - uses: actions/checkout@v4`n"
New-FileContent -Path (Join-Path $gh 'deploy.yml')        -Content "name: Deploy`non: [push]`njobs:`n  placeholder:`n    runs-on: ubuntu-latest`n    steps:`n      - uses: actions/checkout@v4`n"

# =============================================================================
# 3 · docs
# =============================================================================
Write-Section "Docs"
$docs = Join-Path $RootPath 'docs'

New-MdFile -Path (Join-Path $docs 'README.md') -Title 'my_motii docs'
New-MdFile -Path (Join-Path $docs 'architecture\overview.md') -Title 'Architecture overview'
New-MdFile -Path (Join-Path $docs 'architecture\django-fastapi-boundary.md') -Title 'Django / FastAPI boundary'
New-MdFile -Path (Join-Path $docs 'architecture\platform-vs-tenant-data.md') -Title 'Platform vs tenant data'

$adr = Join-Path $docs 'architecture\adr'
New-Dir -Path $adr
$adrs = @(
    @{ N='0001-monorepo.md';                  T='ADR 0001 - Monorepo' },
    @{ N='0002-django-fastapi-boundary.md';   T='ADR 0002 - Django / FastAPI boundary' },
    @{ N='0003-multitenancy-strategy.md';     T='ADR 0003 - Multitenancy strategy' },
    @{ N='0004-stock-as-ledger.md';           T='ADR 0004 - Stock as an append-only ledger' },
    @{ N='0005-offline-sync-protocol.md';     T='ADR 0005 - Offline sync protocol' },
    @{ N='0006-numbering-scheme.md';          T='ADR 0006 - Document numbering scheme' },
    @{ N='0007-nginx-reverse-proxy.md';       T='ADR 0007 - nginx as reverse proxy' },
    @{ N='0008-frontend-packages-vs-apps.md'; T='ADR 0008 - Frontend packages vs apps' }
)
foreach ($a in $adrs) { New-MdFile -Path (Join-Path $adr $a.N) -Title $a.T }

$docPairs = @(
    @('domain\inventory.md','Domain - Inventory'),
    @('domain\pricing.md','Domain - Pricing'),
    @('domain\fitment.md','Domain - Fitment'),
    @('domain\accounting.md','Domain - Accounting'),
    @('domain\documents-numbering.md','Domain - Document numbering'),
    @('tenancy\model.md','Tenancy model'),
    @('tenancy\rls-policies.md','Tenancy RLS policies'),
    @('offline\protocol.md','Offline sync protocol'),
    @('offline\conflict-resolution.md','Offline conflict resolution'),
    @('offline\device-identity.md','Offline device identity'),
    @('integrations\mpesa-daraja.md','M-Pesa Daraja integration'),
    @('integrations\etims-kra.md','eTIMS / KRA integration'),
    @('integrations\whatsapp-cloud.md','WhatsApp Cloud integration'),
    @('integrations\sms-providers.md','SMS providers'),
    @('api\conventions.md','API conventions'),
    @('api\auth.md','API auth'),
    @('api\errors.md','API errors'),
    @('api\versioning.md','API versioning'),
    @('ops\deployment.md','Deployment'),
    @('ops\backups.md','Backups'),
    @('ops\observability.md','Observability'),
    @('product\roadmap.md','Product roadmap'),
    @('product\pricing.md','Product pricing'),
    @('product\personas.md','Product personas')
)
foreach ($pair in $docPairs) {
    New-MdFile -Path (Join-Path $docs $pair[0]) -Title $pair[1]
}
New-Dir -Path (Join-Path $docs 'ops\runbooks'); New-Gitkeep (Join-Path $docs 'ops\runbooks')

# =============================================================================
# 4 · infra
# =============================================================================
Write-Section "Infra"
$infra = Join-Path $RootPath 'infra'

New-FileContent -Path (Join-Path $infra 'docker\backend.Dockerfile') -Content @'
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*
COPY backend/requirements /app/backend/requirements
RUN pip install --no-cache-dir -r /app/backend/requirements/development.txt
COPY backend /app/backend
COPY infra /app/infra
RUN pip install -e /app/backend/shared
EXPOSE 8000 8001
'@

New-FileContent -Path (Join-Path $infra 'docker\worker.Dockerfile') -Content @'
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*
COPY backend/requirements /app/backend/requirements
RUN pip install --no-cache-dir -r /app/backend/requirements/development.txt
COPY backend /app/backend
COPY infra /app/infra
RUN pip install -e /app/backend/shared
'@

New-FileContent -Path (Join-Path $infra 'docker\frontend.Dockerfile') -Content @'
FROM node:20-alpine AS build
WORKDIR /app
RUN corepack enable
COPY frontend /app
RUN pnpm install --frozen-lockfile
RUN pnpm -r build

FROM nginx:1.27-alpine
COPY --from=build /app/apps/retailer-web/dist /usr/share/nginx/html
'@

New-FileContent -Path (Join-Path $infra 'docker\postgres\init.sql') -Content @'
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";
'@

New-FileContent -Path (Join-Path $infra 'docker\redis\redis.conf') -Content @'
appendonly yes
maxmemory-policy allkeys-lru
save 900 1
save 300 10
'@

$nginxConf = Join-Path $infra 'nginx\conf.d'
New-Dir -Path $nginxConf

New-FileContent -Path (Join-Path $infra 'nginx\nginx.conf') -Content @'
worker_processes auto;
events { worker_connections 4096; }
http {
    include       mime.types;
    default_type  application/octet-stream;
    sendfile      on;
    tcp_nopush    on;
    keepalive_timeout 65;
    client_max_body_size 25m;
    include /etc/nginx/conf.d/*.conf;
}
'@

New-FileContent -Path (Join-Path $nginxConf 'api.conf') -Content @'
upstream my_motii_api { server api:8001; }

server {
    listen 80;
    server_name api.my_motii.local;

    location /api/      { proxy_pass http://my_motii_api; include /etc/nginx/proxy_common.conf; }
    location /ws/       { proxy_pass http://my_motii_api; include /etc/nginx/proxy_ws.conf;     }
    location /webhooks/ { proxy_pass http://my_motii_api; include /etc/nginx/proxy_common.conf; }
    location /healthz   { proxy_pass http://my_motii_api; }
}
'@

New-FileContent -Path (Join-Path $nginxConf 'admin.conf') -Content @'
upstream my_motii_core { server core:8000; }

server {
    listen 80;
    server_name admin.my_motii.local;

    location /django-admin/ { proxy_pass http://my_motii_core; include /etc/nginx/proxy_common.conf; }
    location /internal/     { proxy_pass http://my_motii_core; include /etc/nginx/proxy_common.conf; }
    location /static/       { alias /var/www/static/; }
    location /media/        { alias /var/www/media/;  }
}
'@

# ── SINGLE-QUOTED here-string: $uri must stay literal ──────────────────────
New-FileContent -Path (Join-Path $nginxConf 'frontend.conf') -Content @'
server {
    listen 80 default_server;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    location / { try_files $uri $uri/ /index.html; }
}
'@

foreach ($p in @('k8s\base','k8s\overlays','terraform\modules','terraform\environments')) {
    $d = Join-Path $infra $p; New-Dir -Path $d; New-Gitkeep $d
}

New-FileContent -Path (Join-Path $infra 'scripts\entrypoint-api.sh') -Content @'
#!/usr/bin/env bash
set -e
cd /app/backend/api
exec uvicorn main:app --host 0.0.0.0 --port 8001 --reload
'@

New-FileContent -Path (Join-Path $infra 'scripts\entrypoint-worker.sh') -Content @'
#!/usr/bin/env bash
set -e
cd /app/backend/core
exec celery -A config.celery worker -l info
'@

New-FileContent -Path (Join-Path $infra 'scripts\entrypoint-beat.sh') -Content @'
#!/usr/bin/env bash
set -e
cd /app/backend/core
exec celery -A config.celery beat -l info
'@

# =============================================================================
# 5 · database
# =============================================================================
Write-Section "Database seeds & fixtures"
$db = Join-Path $RootPath 'database'
New-MdFile -Path (Join-Path $db 'README.md') -Title 'Database assets'

$seeds = Join-Path $db 'seeds'; New-Dir -Path $seeds
foreach ($f in @('vehicle_makes','vehicle_models','part_categories','brands','units_of_measure')) {
    New-JsonFile -Path (Join-Path $seeds "$f.json") -Content '[]'
}
$fixtures = Join-Path $db 'fixtures'; New-Dir -Path $fixtures
foreach ($f in @('demo_tenant','demo_products')) {
    New-JsonFile -Path (Join-Path $fixtures "$f.json") -Content '[]'
}
$backups = Join-Path $db 'backups'; New-Dir -Path $backups; New-Gitkeep $backups

# =============================================================================
# 6 · FRONTEND
# =============================================================================
Write-Section "Frontend workspace"

New-MdFile -Path (Join-Path $frontend 'README.md') -Title 'my_motii frontend'

New-FileContent -Path (Join-Path $frontend 'tsconfig.base.json') -Content @'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "jsx": "react-jsx",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noUncheckedIndexedAccess": true,
    "paths": {
      "@my-motii/ui":           ["packages/ui/src"],
      "@my-motii/api-client":   ["packages/api-client/src"],
      "@my-motii/auth":         ["packages/auth/src"],
      "@my-motii/offline-sync": ["packages/offline-sync/src"],
      "@my-motii/printing":     ["packages/printing/src"],
      "@my-motii/hooks":        ["packages/hooks/src"],
      "@my-motii/lib":          ["packages/lib/src"],
      "@my-motii/utils":        ["packages/utils/src"],
      "@my-motii/storage":      ["packages/storage/src"],
      "@my-motii/i18n":         ["packages/i18n/src"],
      "@my-motii/locale":       ["packages/locale"],
      "@my-motii/router":       ["packages/router/src"],
      "@my-motii/contexts":     ["packages/contexts/src"],
      "@my-motii/layout":       ["packages/layout/src"]
    }
  }
}
'@

# ── SINGLE-QUOTED here-string: $schema must stay literal ────────────────────
New-FileContent -Path (Join-Path $frontend 'turbo.json') -Content @'
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": { "dependsOn": ["^build"], "outputs": ["dist/**"] },
    "dev":   { "cache": false, "persistent": true },
    "lint":  { "dependsOn": ["^build"] },
    "test":  { "dependsOn": ["^build"] },
    "typecheck": { "dependsOn": ["^build"] }
  }
}
'@

New-FileContent -Path (Join-Path $frontend '.eslintrc.cjs') -Content @'
module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint', 'react', 'react-hooks'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended'
  ],
  ignorePatterns: ['dist', 'node_modules', 'generated'],
};
'@

New-FileContent -Path (Join-Path $frontend '.prettierrc') -Content @'
{ "semi": true, "singleQuote": true, "trailingComma": "all", "printWidth": 100 }
'@

New-FileContent -Path (Join-Path $frontend '.npmrc') -Content "strict-peer-dependencies=false`n"

New-FileContent -Path (Join-Path $frontend 'vitest.workspace.ts') -Content @'
import { defineWorkspace } from 'vitest/config';
export default defineWorkspace(['packages/*', 'apps/*']);
'@

# ---- frontend/packages ----
$packages = @(
    @{ Name='api-client';   Src=@('index.ts','axios.ts','fetch.ts','correlation.ts','tenant.ts','errors.ts') },
    @{ Name='auth';         Src=@('index.ts','AuthProvider.tsx','useAuth.ts','tokens.ts','permissions.ts','guards.tsx') },
    @{ Name='contexts';     Src=@('index.ts','ThemeContext.tsx','ToastContext.tsx','NotificationContext.tsx','TenantContext.tsx') },
    @{ Name='offline-sync'; Src=@('index.ts','db.ts','queue.ts','engine.ts','conflict.ts','types.ts') },
    @{ Name='printing';     Src=@('index.ts','escpos.ts','webusb.ts','bluetooth.ts','network.ts','pdf.ts','types.ts') },
    @{ Name='router';       Src=@('index.ts','routes.ts','guards.tsx','lazy.tsx','breadcrumbs.tsx') },
    @{ Name='i18n';         Src=@('index.ts','provider.tsx','useT.ts','formatters.ts') },
    @{ Name='storage';      Src=@('index.ts','local.ts','session.ts','memory.ts','secure.ts') },
    @{ Name='hooks';        Src=@('index.ts','useDebounce.ts','useMediaQuery.ts','useIsMobile.ts','usePagination.ts','useOnlineStatus.ts','useInterval.ts','useLocalStorage.ts') },
    @{ Name='lib';          Src=@('index.ts','logger.ts','date.ts','money.ts','phone.ts','password-strength.ts','notification-sound.ts','camera.ts','cn.ts') },
    @{ Name='utils';        Src=@('index.ts','array.ts','object.ts','string.ts','result.ts') },
    @{ Name='layout';       Src=@('index.ts','MainLayout.tsx','Sidebar.tsx','Header.tsx','Footer.tsx','MobileBottomNav.tsx','FloatingActionButton.tsx') }
)

foreach ($p in $packages) {
    $pkgRoot = Join-Path $fePkg $p.Name
    New-Dir -Path $pkgRoot
    # Interpolated: uses $($p.Name)
    New-FileContent -Path (Join-Path $pkgRoot 'package.json') -Content @"
{
  "name": "@my-motii/$($p.Name)",
  "version": "0.0.0",
  "private": true,
  "type": "module",
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "exports": { ".": "./src/index.ts" }
}
"@
    New-FileContent -Path (Join-Path $pkgRoot 'tsconfig.json') -Content '{ "extends": "../../tsconfig.base.json", "include": ["src"] }'
    $srcDir = Join-Path $pkgRoot 'src'; New-Dir -Path $srcDir
    foreach ($f in $p.Src) {
        New-FileContent -Path (Join-Path $srcDir $f) -Content 'export {};'
    }
}

# api-client endpoints + generated placeholder
$apiClientDir = Join-Path $fePkg 'api-client\src'
$epDir = Join-Path $apiClientDir 'endpoints'; New-Dir -Path $epDir
foreach ($f in @('auth','inventory','sales','documents','purchasing','payments','sync','tenants','analytics','notifications')) {
    New-FileContent -Path (Join-Path $epDir "$f.ts") -Content 'export {};'
}
New-Dir -Path (Join-Path $fePkg 'api-client\generated'); New-Gitkeep (Join-Path $fePkg 'api-client\generated')

# offline-sync entities
$osEnt = Join-Path $fePkg 'offline-sync\src\entities'; New-Dir -Path $osEnt
foreach ($f in @('sales','inventory','customers','payments')) {
    New-FileContent -Path (Join-Path $osEnt "$f.ts") -Content 'export {};'
}
New-Dir -Path (Join-Path $fePkg 'offline-sync\src\hooks')
New-FileContent -Path (Join-Path $fePkg 'offline-sync\src\hooks\useSyncStatus.ts') -Content 'export {};'

# printing templates
New-Dir -Path (Join-Path $fePkg 'printing\src\templates'); New-Gitkeep (Join-Path $fePkg 'printing\src\templates')

# locale
$locales = Join-Path $fePkg 'locale\locales'
foreach ($lang in @('en','sw')) {
    $langDir = Join-Path $locales $lang; New-Dir -Path $langDir
    foreach ($ns in @('common','inventory','sales','purchases','pos','errors')) {
        New-JsonFile -Path (Join-Path $langDir "$ns.json") -Content '{}'
    }
}

# ui design system
$ui = Join-Path $fePkg 'ui'
New-Dir -Path $ui
New-FileContent -Path (Join-Path $ui 'package.json') -Content @'
{
  "name": "@my-motii/ui",
  "version": "0.0.0",
  "private": true,
  "type": "module",
  "main": "./src/index.ts"
}
'@
New-FileContent -Path (Join-Path $ui 'tsconfig.json') -Content '{ "extends": "../../tsconfig.base.json", "include": ["src"] }'
New-FileContent -Path (Join-Path $ui 'tailwind.config.ts') -Content 'export default {};'
New-FileContent -Path (Join-Path $ui 'postcss.config.cjs')  -Content 'module.exports = { plugins: { tailwindcss: {}, autoprefixer: {} } };'
foreach ($sub in @('src','src\styles','src\primitives','src\feedback','src\tables','src\charts','src\forms','src\cards')) {
    New-Dir -Path (Join-Path $ui $sub)
}
New-FileContent -Path (Join-Path $ui 'src\index.ts')  -Content 'export {};'
New-FileContent -Path (Join-Path $ui 'src\tokens.ts') -Content 'export {};'
foreach ($css in @('variables','global','animations','components')) {
    New-FileContent -Path (Join-Path $ui "src\styles\$css.css") -Content "/* $css */"
}

# tooling
foreach ($t in @('eslint-config','tsconfig','tailwind-preset')) {
    $d = Join-Path $frontend "tooling\$t"; New-Dir -Path $d; New-Gitkeep $d
}

# ---- frontend/apps ----
function New-FrontendApp {
    param(
        [string]$AppRoot,
        [string]$AppName,
        [string[]]$Features
    )
    New-Dir -Path $AppRoot
    # Interpolated: uses $AppName
    New-FileContent -Path (Join-Path $AppRoot 'package.json') -Content @"
{
  "name": "$AppName",
  "version": "0.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "lint": "eslint src",
    "test": "vitest run",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.5.0",
    "vite": "^5.4.0",
    "vitest": "^2.0.0"
  }
}
"@
    New-FileContent -Path (Join-Path $AppRoot 'vite.config.ts') -Content @'
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': 'http://localhost:8001', '/ws': { target: 'ws://localhost:8001', ws: true } }
  }
});
'@
    New-FileContent -Path (Join-Path $AppRoot 'vitest.config.ts') -Content "import { defineConfig } from 'vitest/config'; export default defineConfig({ test: { environment: 'jsdom' } });"
    New-FileContent -Path (Join-Path $AppRoot 'tsconfig.json')     -Content '{ "extends": "../../tsconfig.base.json", "include": ["src"] }'
    New-FileContent -Path (Join-Path $AppRoot 'tailwind.config.ts') -Content 'export default {};'
    New-FileContent -Path (Join-Path $AppRoot 'postcss.config.cjs') -Content 'module.exports = { plugins: { tailwindcss: {}, autoprefixer: {} } };'

    # Interpolated: uses $AppName
    New-FileContent -Path (Join-Path $AppRoot 'index.html') -Content "<!doctype html><html><head><meta charset='utf-8'><title>$AppName</title></head><body><div id='root'></div><script type='module' src='/src/main.tsx'></script></body></html>"

    $pub = Join-Path $AppRoot 'public'; New-Dir -Path $pub
    New-Dir -Path (Join-Path $pub 'assets\icons')
    New-Dir -Path (Join-Path $pub 'assets\images')
    New-Dir -Path (Join-Path $pub 'assets\sounds')
    New-JsonFile -Path (Join-Path $pub 'manifest.json') -Content '{"name":"my_motii","short_name":"my_motii","start_url":"/","display":"standalone"}'
    New-FileContent -Path (Join-Path $pub 'service-worker.js') -Content "self.addEventListener('install', () => self.skipWaiting());`nself.addEventListener('activate', () => self.clients.claim());"

    $src = Join-Path $AppRoot 'src'; New-Dir -Path $src
    New-FileContent -Path (Join-Path $src 'main.tsx')  -Content @'
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
createRoot(document.getElementById('root')!).render(<App />);
'@

    # Interpolated: uses $AppName
    New-FileContent -Path (Join-Path $src 'App.tsx') -Content "export default function App() { return <div>$AppName</div>; }"

    New-FileContent -Path (Join-Path $src 'index.css') -Content '@tailwind base; @tailwind components; @tailwind utilities;'
    New-FileContent -Path (Join-Path $src 'env.ts')    -Content "export const env = { API_URL: import.meta.env.VITE_API_URL ?? '/api' };"

    New-Dir -Path (Join-Path $src 'routes')
    New-Dir -Path (Join-Path $src 'app-shell')
    New-Dir -Path (Join-Path $src 'lib')

    foreach ($feat in $Features) {
        $featRoot = Join-Path $src "features\$feat"
        New-Dir -Path $featRoot
        foreach ($sub in @('pages','components','hooks','types','stores','services')) {
            New-Dir -Path (Join-Path $featRoot $sub)
        }
        New-FileContent -Path (Join-Path $featRoot 'index.ts') -Content 'export {};'
    }
}

New-FrontendApp -AppRoot (Join-Path $feApps 'retailer-web') -AppName '@my-motii/retailer-web' -Features @(
    'auth','dashboard','inventory','sales','pos','purchases','suppliers',
    'customers','expenses','reports','settings'
)
New-FrontendApp -AppRoot (Join-Path $feApps 'supplier-web') -AppName '@my-motii/supplier-web' -Features @(
    'auth','dashboard','catalog','orders','retailers','pricing','analytics','reps','settings'
)
New-FrontendApp -AppRoot (Join-Path $feApps 'admin-web') -AppName '@my-motii/admin-web' -Features @(
    'auth','tenants','plans','feature-flags','ops','support'
)

# pos-desktop (Tauri)
$pos = Join-Path $feApps 'pos-desktop'
New-FrontendApp -AppRoot $pos -AppName '@my-motii/pos-desktop' -Features @(
    'checkout','register','cash-session','printing','sync'
)
$tauri = Join-Path $pos 'src-tauri'
New-Dir -Path $tauri
New-FileContent -Path (Join-Path $tauri 'Cargo.toml') -Content @'
[package]
name = "my_motii_pos"
version = "0.0.0"
edition = "2021"

[build-dependencies]
tauri-build = { version = "2", features = [] }

[dependencies]
tauri = { version = "2", features = [] }
serde = { version = "1", features = ["derive"] }
'@
New-FileContent -Path (Join-Path $tauri 'tauri.conf.json') -Content '{"build":{"frontendDist":"../dist"},"app":{"windows":[{"title":"my_motii POS","width":1280,"height":800}]}}'
New-Dir -Path (Join-Path $tauri 'src')
New-FileContent -Path (Join-Path $tauri 'src\main.rs') -Content 'fn main() { tauri::Builder::default().run(tauri::generate_context!()).expect("error"); }'

# mobile (React Native placeholder)
$mobile = Join-Path $feApps 'mobile'
New-Dir -Path $mobile
New-Dir -Path (Join-Path $mobile 'src')
New-FileContent -Path (Join-Path $mobile 'package.json') -Content '{"name":"@my-motii/mobile","version":"0.0.0","private":true}'
New-FileContent -Path (Join-Path $mobile 'src\index.tsx') -Content 'export {};'

# =============================================================================
# 7 · BACKEND requirements
# =============================================================================
Write-Section "Backend requirements"
$req = Join-Path $backend 'requirements'
New-Dir -Path $req
New-FileContent -Path (Join-Path $req 'base.txt') -Content @'
Django>=5.0,<5.1
djangorestframework>=3.15
django-cors-headers>=4.4
django-filter>=24.3
psycopg[binary]>=3.2
celery>=5.4
redis>=5.0
fastapi>=0.115
uvicorn[standard]>=0.30
pydantic>=2.9
pydantic-settings>=2.5
httpx>=0.27
python-decouple>=3.8
structlog>=24.4
orjson>=3.10
boto3>=1.35
cryptography>=43.0
qrcode[pil]>=7.4
weasyprint>=62.3
'@
New-FileContent -Path (Join-Path $req 'development.txt') -Content @'
-r base.txt
pytest>=8.3
pytest-django>=4.9
pytest-asyncio>=0.24
pytest-cov>=5.0
factory-boy>=3.3
ruff>=0.6
mypy>=1.11
django-stubs>=5.0
ipython>=8.27
'@
New-FileContent -Path (Join-Path $req 'production.txt') -Content @'
-r base.txt
gunicorn>=23.0
sentry-sdk>=2.13
'@
New-FileContent -Path (Join-Path $req 'testing.txt') -Content @'
-r development.txt
'@

# =============================================================================
# 8 · BACKEND shared package
# =============================================================================
Write-Section "Backend shared package"

New-Dir -Path $sharedPkg
New-FileContent -Path (Join-Path $sharedPkg 'pyproject.toml') -Content @'
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-motii-shared"
version = "0.0.0"
description = "Shared domain primitives for my_motii."
requires-python = ">=3.11"
dependencies = []

[tool.setuptools.packages.find]
where = ["."]
include = ["my_motii_shared*"]
'@
New-MdFile -Path (Join-Path $sharedPkg 'README.md') -Title 'my_motii_shared'

$sharedRoot = Join-Path $sharedPkg 'my_motii_shared'
New-Dir -Path $sharedRoot
New-PyInit $sharedRoot

$sharedPkgs = @{
    'domain'      = @('money','quantity','tax','identifiers','numbering')
    'enums'       = @('tenant','roles','inventory','documents','payments','purchases','sync','compliance')
    'constants'   = @('currencies','taxes','system')
    'tenancy'     = @('context','resolver','isolation')
    'permissions' = @('permissions','roles')
    'events'      = @('base','bus','sales','inventory','purchasing','payments')
    'exceptions'  = @('base','tenancy','inventory','payments','compliance')
    'schemas'     = @('pagination','responses','common')
    'utils'       = @('dates','hashing','ids','retry')
    'db_models'   = @('base','mixins','managers')
    'logging'     = @('config','correlation','formatters','filters')
    'cache'       = @('decorators','keys','utils','backends')
    'security'    = @('crypto','tokens','secrets','headers','passwords')
    'storage'     = @('base','local','s3','factory','utils')
    'throttling'  = @('strategies','limits','decorators','backends')
}
foreach ($pkg in $sharedPkgs.Keys) {
    $pkgDir = Join-Path $sharedRoot $pkg
    New-Dir -Path $pkgDir
    New-PyInit $pkgDir
    foreach ($f in $sharedPkgs[$pkg]) {
        New-PyFile -Path (Join-Path $pkgDir "$f.py") -Doc "my_motii_shared.$pkg :: $f"
    }
}

$sharedTests = Join-Path $sharedPkg 'tests'
New-Dir -Path $sharedTests
New-PyInit $sharedTests
foreach ($tf in @('test_money','test_tenancy','test_logging','test_cache','test_throttling','test_db_models')) {
    New-PyFile -Path (Join-Path $sharedTests "$tf.py") -Doc "shared tests: $tf"
}

# =============================================================================
# 9 · BACKEND Django core
# =============================================================================
Write-Section "Backend Django core"

New-Dir -Path $core
New-FileContent -Path (Join-Path $core 'manage.py') -Content @'
#!/usr/bin/env python
import os, sys
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
'@
New-FileContent -Path (Join-Path $core 'pyproject.toml') -Content @'
[project]
name = "my-motii-core"
version = "0.0.0"
requires-python = ">=3.11"
dependencies = ["my-motii-shared"]

[tool.setuptools.packages.find]
where = ["."]
include = ["apps*", "config*"]
'@

$cfg = Join-Path $core 'config'
New-Dir -Path $cfg
New-PyInit $cfg
$settingsDir = Join-Path $cfg 'settings'
New-Dir -Path $settingsDir
New-PyInit $settingsDir
foreach ($sf in @('base','development','production','testing')) {
    New-PyFile -Path (Join-Path $settingsDir "$sf.py") -Doc "Django settings :: $sf"
}
foreach ($f in @('urls','asgi','wsgi','celery','logging')) {
    New-PyFile -Path (Join-Path $cfg "$f.py") -Doc "Django config :: $f"
}

# ---- Django apps ----
New-Dir -Path $appsRoot
New-PyInit $appsRoot

$appSpecs = @(
    @{ Name='tenancy';          Models=@('tenant','tenant_settings','tenant_domain','tenant_feature');                 Services=@('tenant_service','provisioning_service','onboarding_service'); Selectors=@('tenant_selectors') }
    @{ Name='accounts';         Models=@('user','user_profile','user_role','user_session','login_attempt');           Services=@('authentication','registration','password_service','otp_service'); Selectors=@('user_selectors') }
    @{ Name='organizations';    Models=@('organization','organization_profile','business_hours','business_settings','tax_profile'); Services=@('organization_service'); Selectors=@('organization_selectors') }
    @{ Name='branches';         Models=@('branch','branch_settings','branch_hours','branch_user');                    Services=@('branch_service'); Selectors=@('branch_selectors') }
    @{ Name='warehouses';       Models=@('warehouse','warehouse_zone','aisle','rack','shelf','bin_location');         Services=@('warehouse_service','location_service'); Selectors=@('warehouse_selectors') }
    @{ Name='catalog';          Models=@('product','product_variant','category','brand','unit_of_measure','barcode','product_image'); Services=@('product_service','pricing_service','catalog_service'); Selectors=@('product_selectors') }
    @{ Name='vehicles';         Models=@('make','model','generation','trim','engine','transmission','body_type','fuel_type'); Services=@('vehicle_service'); Selectors=@('vehicle_selectors'); ExtraPackages=@('imports') }
    @{ Name='fitment';          Models=@('compatibility','oem_part','equivalent_part','supersession','fitment_note');  Services=@('fitment_service','compatibility_service','cross_reference_service'); Selectors=@('fitment_selectors'); ExtraPackages=@('search','imports') }
    @{ Name='inventory';        Models=@('inventory_item','inventory_balance','stock_movement','stock_adjustment','stock_lot','serial_number','reservation','transfer','stocktake','reorder_rule','warranty'); Services=@('movement_service','balance_service','valuation_service','availability_service','reorder_service','reconciliation_service'); Selectors=@('inventory_selectors','movement_selectors'); ExtraPackages=@('events') }
    @{ Name='customers';        Models=@('customer','customer_profile','customer_credit','customer_group','customer_contact'); Services=@('customer_service'); Selectors=@('customer_selectors') }
    @{ Name='suppliers';        Models=@('supplier','supplier_profile','supplier_contact','supplier_terms');          Services=@('supplier_service'); Selectors=@('supplier_selectors') }
    @{ Name='supplier_network'; Models=@('supplier_connection','network_membership','visibility_rule','consent');    Services=@('connection_service','visibility_service','consent_service','supplier_matching'); Selectors=@('supplier_network_selectors'); ExtraPackages=@('catalog','pricing'); PackageFiles=@{ 'catalog'=@('catalog','catalog_product','catalog_import','catalog_version','catalog_mapping'); 'pricing'=@('price_list','price_list_item','retailer_price','volume_price','discount_rule','price_history') } }
    @{ Name='sales';            Models=@('sale','sale_item','sale_payment','sale_discount','sale_status');            Services=@('sale_service','pricing_service','discount_service','checkout_service'); Selectors=@('sale_selectors'); ExtraPackages=@('events') }
    @{ Name='pos';              Models=@('register','cash_session','register_transaction');                          Services=@('checkout','cash_session_service','register_service','reconciliation'); Selectors=@('pos_selectors') }
    @{ Name='documents';        Models=@('document','document_line','document_sequence','document_attachment');       Services=@('document_service','numbering_service','quote_service','invoice_service','receipt_service','credit_note_service'); Selectors=@('document_selectors'); ExtraPackages=@('generators'); PackageFiles=@{ 'generators'=@('pdf','escpos','html') } }
    @{ Name='purchasing';       Models=@('purchase_order','purchase_order_line','goods_received_note','supplier_invoice','rfq','rfq_line','quotation','quotation_line'); Services=@('purchase_service','purchase_calculator','receiving_service','rfq_service','quotation_service'); Selectors=@('purchase_selectors'); ExtraPackages=@('notifications') }
    @{ Name='payments';         Models=@('payment','payment_method','payment_allocation','payment_reference','refund'); Services=@('payment_service','allocation_service','refund_service'); Selectors=@('payment_selectors'); ExtraPackages=@('gateways','reconciliation'); PackageFiles=@{ 'gateways'=@('base','cash','mpesa','bank','card') } }
    @{ Name='mpesa';            Models=@('mpesa_transaction','stk_request','callback');                              Services=@('mpesa_service','reconciliation'); Selectors=@('mpesa_selectors'); ExtraPackages=@('daraja','webhooks','validators'); PackageFiles=@{ 'daraja'=@('auth','stk_push','c2b','b2c','transaction_status','reversal') } }
    @{ Name='accounting';       Models=@('account','journal_entry','journal_line','fiscal_period','cashbook','receivable','payable','tax_profile'); Services=@('ledger_service','posting_service','profit_service','reconciliation_service'); Selectors=@('accounting_selectors'); ExtraPackages=@('reports'); PackageFiles=@{ 'reports'=@('profit_loss','balance_sheet','cashflow','trial_balance') } }
    @{ Name='expenses';         Models=@('expense','expense_category','recurring_expense','expense_attachment','expense_approval'); Services=@('expense_service'); Selectors=@('expense_selectors'); ExtraPackages=@('approvals') }
    @{ Name='etims';            Models=@('etims_configuration','etims_document','etims_submission','etims_response','etims_error'); Services=@('invoice_service','credit_note_service','sync_service','reconciliation_service'); Selectors=@('etims_selectors'); ExtraPackages=@('clients','queues','validators','webhooks'); PackageFiles=@{ 'clients'=@('base','etims_client','authentication') } }
    @{ Name='notifications';    Models=@('notification','notification_preference','notification_template','notification_delivery'); Services=@('notification_service','template_service','preference_service'); Selectors=@('notification_selectors'); ExtraPackages=@('channels'); PackageFiles=@{ 'channels'=@('in_app','push','sms','email','whatsapp') } }
    @{ Name='analytics';        Models=@('daily_sales','product_performance','inventory_metrics','supplier_metrics','customer_metrics','branch_metrics'); Services=@('sales_analytics','inventory_analytics','supplier_analytics','customer_analytics'); Selectors=@('analytics_selectors'); ExtraPackages=@('aggregations','queries') }
    @{ Name='forecasting';      Models=@('demand_forecast','forecast_run','reorder_recommendation');                  Services=@('demand_service','forecast_service','reorder_recommendation'); Selectors=@('forecasting_selectors'); ExtraPackages=@('algorithms','jobs') }
    @{ Name='offline_sync';     Models=@('sync_device','sync_session','sync_operation','sync_batch','sync_conflict','sync_checkpoint'); Services=@('sync_service','conflict_service','idempotency_service','reconciliation_service'); Selectors=@('sync_selectors'); ExtraPackages=@('processors','validators'); PackageFiles=@{ 'processors'=@('sales_processor','inventory_processor','customer_processor','payment_processor') } }
    @{ Name='audit';            Models=@('audit_event','audit_change','security_event');                              Services=@('audit_service','security_log_service'); Selectors=@('audit_selectors'); ExtraPackages=@('middleware') }
    @{ Name='subscriptions';    Models=@('plan','plan_feature','subscription','subscription_item','subscription_usage','trial','subscription_event'); Services=@('subscription_service','feature_service','usage_service','entitlement_service'); Selectors=@('subscription_selectors'); ExtraPackages=@('limits') }
    @{ Name='billing';          Models=@('invoice','invoice_item','payment','transaction','billing_event');           Services=@('billing_service'); Selectors=@('billing_selectors'); ExtraPackages=@('gateways','webhooks') }
    @{ Name='marketplace';      Models=@('listing','listing_visibility','order','order_item','marketplace_cart','marketplace_transaction','marketplace_commission'); Services=@('listing_service','order_service','matching_service','commission_service'); Selectors=@('marketplace_selectors'); ExtraPackages=@('search','commissions','delivery') }
    @{ Name='garages';          Models=@('garage','garage_profile','garage_branch','mechanic','mechanic_profile','mechanic_specialization','job_card','job_item','labor','part_usage','job_status','job_payment'); Services=@('garage_service','mechanic_service','job_card_service','parts_service','billing_service'); Selectors=@('garage_selectors') }
    @{ Name='data_io';          Models=@('import_job','import_file','import_row','import_error','export_job','export_file'); Services=@('import_service','validation_service','mapping_service','export_service'); Selectors=@('data_io_selectors'); ExtraPackages=@('parsers','processors','generators'); PackageFiles=@{ 'parsers'=@('csv','excel','json'); 'processors'=@('products','customers','suppliers','inventory'); 'generators'=@('csv','excel','pdf','json') } }
    @{ Name='integrations';     Models=@('integration','integration_credential','webhook_endpoint','webhook_delivery'); Services=@('integration_service','webhook_service'); Selectors=@('integration_selectors'); ExtraPackages=@('webhooks') }
    @{ Name='common';           Models=@();                                                                         Services=@(); Selectors=@() }
)

foreach ($spec in $appSpecs) {
    $params = @{
        AppsRoot  = $appsRoot
        Name      = $spec.Name
        Models    = $spec.Models
        Services  = $spec.Services
        Selectors = $spec.Selectors
    }
    if ($spec.ContainsKey('ExtraPackages')) { $params.ExtraPackages = $spec.ExtraPackages }
    if ($spec.ContainsKey('PackageFiles'))  { $params.PackageFiles  = $spec.PackageFiles  }
    if ($spec.ContainsKey('ExtraDirs'))     { $params.ExtraDirs     = $spec.ExtraDirs     }
    New-DjangoApp @params
}

New-PyFile -Path (Join-Path $appsRoot 'common\models.py')     -Doc 'Shared base models.'
New-PyFile -Path (Join-Path $appsRoot 'common\managers.py')   -Doc 'Shared managers.'
New-PyFile -Path (Join-Path $appsRoot 'common\mixins.py')     -Doc 'Shared mixins.'
New-PyFile -Path (Join-Path $appsRoot 'common\validators.py') -Doc 'Shared validators.'

# core/scripts
$coreScripts = Join-Path $core 'scripts'
New-Dir -Path $coreScripts
New-PyFile -Path (Join-Path $coreScripts 'bootstrap_platform_data.py') -Doc 'Seed platform-owned data.'
New-PyFile -Path (Join-Path $coreScripts 'seed_demo_tenant.py')        -Doc 'Seed a demo tenant.'
New-PyFile -Path (Join-Path $coreScripts 'rotate_encryption_keys.py')  -Doc 'Rotate encryption keys.'

# core/tests
$coreTests = Join-Path $core 'tests'
New-Dir -Path $coreTests
New-PyInit $coreTests
New-PyFile -Path (Join-Path $coreTests 'conftest.py') -Doc 'Core test fixtures.'
New-Dir -Path (Join-Path $coreTests 'factories')
New-PyInit (Join-Path $coreTests 'factories')
New-Dir -Path (Join-Path $coreTests 'unit');        New-Gitkeep (Join-Path $coreTests 'unit')
New-Dir -Path (Join-Path $coreTests 'integration'); New-Gitkeep (Join-Path $coreTests 'integration')

# =============================================================================
# 10 · BACKEND FastAPI edge
# =============================================================================
Write-Section "Backend FastAPI edge"

New-Dir -Path $apiRoot
New-PyFile -Path (Join-Path $apiRoot 'main.py')      -Doc 'FastAPI entry point.'
New-PyFile -Path (Join-Path $apiRoot 'asgi.py')      -Doc 'ASGI application.'
New-PyFile -Path (Join-Path $apiRoot 'bootstrap.py') -Doc 'Bootstrap Django ORM inside FastAPI.'

New-FileContent -Path (Join-Path $apiRoot 'pyproject.toml') -Content @'
[project]
name = "my-motii-api"
version = "0.0.0"
requires-python = ">=3.11"
dependencies = ["my-motii-shared", "my-motii-core"]
'@

$apiApp = Join-Path $apiRoot 'app'
New-Dir -Path $apiApp
New-PyInit $apiApp

$v1 = Join-Path $apiApp 'api\v1'
New-Dir -Path $v1
New-PyInit $v1
foreach ($f in @(
    'router','auth','tenants','users','dashboard','catalog','inventory','sales','pos',
    'documents','customers','suppliers','purchasing','rfqs','payments','expenses',
    'analytics','notifications','fitment','marketplace','sync','realtime','health'
)) {
    New-PyFile -Path (Join-Path $v1 "$f.py") -Doc "FastAPI v1 :: $f"
}
$wh = Join-Path $v1 'webhooks'; New-Dir -Path $wh; New-PyInit $wh
foreach ($f in @('mpesa','etims','whatsapp')) { New-PyFile -Path (Join-Path $wh "$f.py") -Doc "Webhook :: $f" }

$v2 = Join-Path $apiApp 'api\v2'; New-Dir -Path $v2; New-PyInit $v2
New-PyInit (Join-Path $apiApp 'api')

foreach ($sub in @('dependencies','schemas','orchestrators','security','middleware','exceptions','utils')) {
    $d = Join-Path $apiApp $sub; New-Dir -Path $d; New-PyInit $d
}
foreach ($f in @('auth','tenant','permissions','pagination','database','idempotency'))        { New-PyFile -Path (Join-Path $apiApp "dependencies\$f.py") -Doc "Dep :: $f" }
foreach ($f in @('auth','tenant','catalog','inventory','sales','documents','purchasing','supplier','customer','payment','analytics','sync','common')) { New-PyFile -Path (Join-Path $apiApp "schemas\$f.py") -Doc "Schema :: $f" }
foreach ($f in @('checkout','sync_ingest','dashboard'))                                        { New-PyFile -Path (Join-Path $apiApp "orchestrators\$f.py") -Doc "Orchestrator :: $f" }
foreach ($f in @('jwt','password','otp','permissions'))                                        { New-PyFile -Path (Join-Path $apiApp "security\$f.py") -Doc "Security :: $f" }
foreach ($f in @('tenant','request_id','logging','rate_limit'))                                { New-PyFile -Path (Join-Path $apiApp "middleware\$f.py") -Doc "Middleware :: $f" }
foreach ($f in @('handlers','auth','tenant','business'))                                       { New-PyFile -Path (Join-Path $apiApp "exceptions\$f.py") -Doc "Exception :: $f" }

foreach ($t in @('api','security','integration')) {
    $d = Join-Path $apiRoot "tests\$t"; New-Dir -Path $d; New-Gitkeep $d
}
New-PyInit (Join-Path $apiRoot 'tests')

# =============================================================================
# 11 · BACKEND Celery workers
# =============================================================================
Write-Section "Backend Celery workers"

$workers = Join-Path $backend 'workers'
New-Dir -Path $workers
New-PyInit $workers
New-PyFile -Path (Join-Path $workers 'celery_app.py') -Doc 'Celery application.'

$wTasks = Join-Path $workers 'tasks'; New-Dir -Path $wTasks; New-PyInit $wTasks
foreach ($f in @('notifications','analytics','reports','etims','mpesa','data_io','offline_sync','forecasting','cleanup')) {
    New-PyFile -Path (Join-Path $wTasks "$f.py") -Doc "Task group :: $f"
}
$wSched = Join-Path $workers 'schedules'; New-Dir -Path $wSched; New-PyInit $wSched
foreach ($f in @('hourly','daily','periodic')) { New-PyFile -Path (Join-Path $wSched "$f.py") -Doc "Schedule :: $f" }

$wTests = Join-Path $workers 'tests'; New-Dir -Path $wTests; New-PyInit $wTests

# =============================================================================
# 12 · BACKEND Infrastructure adapters
# =============================================================================
Write-Section "Backend Infrastructure adapters"

$infraB = Join-Path $backend 'infrastructure'
New-PyInit $infraB
foreach ($pkg in @('database','redis','storage','email','sms','whatsapp','observability','feature_flags')) {
    $d = Join-Path $infraB $pkg; New-Dir -Path $d; New-PyInit $d
}
foreach ($f in @('session','migrations_hooks')) { New-PyFile -Path (Join-Path $infraB "database\$f.py")      -Doc "DB :: $f" }
foreach ($f in @('client','locks'))              { New-PyFile -Path (Join-Path $infraB "redis\$f.py")         -Doc "Redis :: $f" }
foreach ($f in @('s3','local'))                  { New-PyFile -Path (Join-Path $infraB "storage\$f.py")       -Doc "Storage :: $f" }
foreach ($f in @('logging','tracing','metrics')) { New-PyFile -Path (Join-Path $infraB "observability\$f.py") -Doc "Obs :: $f" }

New-MdFile -Path (Join-Path $backend 'README.md') -Title 'my_motii backend'
New-FileContent -Path (Join-Path $backend '.env.example') -Content '# see root .env.example'

# =============================================================================
# 13 · repo-level scripts
# =============================================================================
Write-Section "Repo scripts"

$scriptsRoot = Join-Path $RootPath 'scripts'
New-Dir -Path $scriptsRoot

New-FileContent -Path (Join-Path $scriptsRoot 'dev_up.sh')         -Content @'
#!/usr/bin/env bash
set -e
docker compose up -d --build
'@
New-FileContent -Path (Join-Path $scriptsRoot 'dev_down.sh')       -Content @'
#!/usr/bin/env bash
set -e
docker compose down
'@
New-FileContent -Path (Join-Path $scriptsRoot 'reset_db.sh')       -Content @'
#!/usr/bin/env bash
set -e
docker compose down -v
docker compose up -d postgres
'@
New-FileContent -Path (Join-Path $scriptsRoot 'seed_all.sh')       -Content @'
#!/usr/bin/env bash
set -e
docker compose exec core python manage.py loaddata database/seeds/*.json
'@
New-FileContent -Path (Join-Path $scriptsRoot 'gen_openapi.sh')    -Content @'
#!/usr/bin/env bash
set -e
cd backend/api
python -c "import main; main.app.openapi()" > ../../frontend/openapi.json
'@
New-FileContent -Path (Join-Path $scriptsRoot 'gen_api_client.sh') -Content @'
#!/usr/bin/env bash
set -e
pnpm --filter @my-motii/api-client run generate
'@
New-FileContent -Path (Join-Path $scriptsRoot 'run_all_tests.sh')  -Content @'
#!/usr/bin/env bash
set -e
pytest backend
pnpm -r test
'@

# =============================================================================
# 14 · cross-service E2E tests
# =============================================================================
Write-Section "Cross-service E2E tests"

$testsRoot = Join-Path $RootPath 'tests'
New-Dir -Path $testsRoot
foreach ($t in @('e2e\retailer','e2e\supplier','e2e\marketplace','e2e\onboarding','fixtures')) {
    $d = Join-Path $testsRoot $t; New-Dir -Path $d; New-Gitkeep $d
}

# =============================================================================
# 15 · Summary
# =============================================================================
Write-Host ""
Write-Host "===========================================================" -ForegroundColor Magenta
Write-Host "  Scaffold complete" -ForegroundColor Magenta
Write-Host "===========================================================" -ForegroundColor Magenta
Write-Host ("  Directories created : {0}" -f $script:DirsCreated)  -ForegroundColor Green
Write-Host ("  Files created       : {0}" -f $script:FilesCreated) -ForegroundColor Green
Write-Host ("  Files skipped       : {0}" -f $script:FilesSkipped) -ForegroundColor Yellow
Write-Host ""
Write-Host "  Root: $RootPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor White
Write-Host "    1) cd `"$RootPath`"" -ForegroundColor White
Write-Host "    2) Copy .env.example to .env and fill in secrets" -ForegroundColor White
Write-Host "    3) docker compose up -d --build" -ForegroundColor White
Write-Host "    4) docker compose exec core python manage.py migrate" -ForegroundColor White
Write-Host "    5) docker compose exec core python manage.py createsuperuser" -ForegroundColor White
Write-Host "    6) pnpm install  (in frontend)" -ForegroundColor White
Write-Host "    7) pnpm -r dev" -ForegroundColor White
Write-Host ""