# Deployment Guide

This guide covers deploying the People Management System in production environments, including configuration, optimization, monitoring, and maintenance procedures.

## Table of Contents

- [Deployment Overview](#deployment-overview)
- [Production Environment Setup](#production-environment-setup)
- [Server Deployment](#server-deployment)
- [Client Deployment](#client-deployment)
- [Database Configuration](#database-configuration)
- [Environment Configuration](#environment-configuration)
- [Security Configuration](#security-configuration)
- [Performance Optimization](#performance-optimization)
- [Monitoring and Logging](#monitoring-and-logging)
- [Backup and Recovery](#backup-and-recovery)
- [Maintenance Procedures](#maintenance-procedures)
- [Troubleshooting](#troubleshooting)

## Deployment Overview

The People Management System can be deployed in various configurations:

1. **Single Server Deployment**: All components on one server (suitable for small organizations)
2. **Distributed Deployment**: Separate servers for API, database, and client distribution
3. **Container Deployment**: Docker-based deployment for scalability
4. **Cloud Deployment**: Cloud-native deployment on AWS, Azure, or GCP

### Recommended Architecture

```
┌─────────────────┐    HTTPS/443     ┌─────────────────┐
│   Load Balancer │◄────────────────►│   Reverse Proxy │
│   (Optional)    │                  │    (Nginx)      │
└─────────────────┘                  └─────────────────┘
                                              │
                                              ▼
                                     ┌─────────────────┐
                                     │   FastAPI App   │
                                     │   (Gunicorn +   │
                                     │    Uvicorn)     │
                                     └─────────────────┘
                                              │
                                              ▼
                                     ┌─────────────────┐
                                     │   PostgreSQL    │
                                     │    Database     │
                                     └─────────────────┘
```

## Production Environment Setup

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 20 GB SSD
- **OS**: Ubuntu 20.04 LTS or higher, CentOS 8+, or similar

#### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Storage**: 50+ GB SSD
- **OS**: Ubuntu 22.04 LTS
- **Network**: 1 Gbps connection

### Server Preparation

#### 1. Update System

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

#### 2. Install Required Packages

```bash
# Ubuntu/Debian
sudo apt install -y python3.9 python3.9-venv python3.9-dev \
    postgresql postgresql-contrib nginx supervisor \
    build-essential curl git

# CentOS/RHEL
sudo yum install -y python39 python39-devel postgresql-server \
    postgresql-contrib nginx supervisor gcc curl git
```

#### 3. Install UV (Python Package Manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

#### 4. Create Application User

```bash
sudo adduser --system --group --home /opt/people-management peoplemgmt
sudo usermod -a -G www-data peoplemgmt
```

## Server Deployment

### 1. Application Setup

```bash
# Switch to application user
sudo su - peoplemgmt

# Clone repository
git clone <repository-url> /opt/people-management/app
cd /opt/people-management/app

# Install dependencies
uv sync --no-dev

# Set up environment
cp server/.env.example server/.env.production
```

### 2. Environment Configuration

Edit `/opt/people-management/app/server/.env.production`:

```bash
# Application settings
APP_NAME="People Management System API"
APP_VERSION="1.0.0"
APP_DESCRIPTION="Production People Management API"

# Server configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
RELOAD=false

# Database configuration
DATABASE_URL=postgresql://peoplemgmt_user:secure_password@localhost:5432/peoplemgmt_db

# Security settings
SECRET_KEY=your-super-secret-key-here-change-this-in-production
CORS_ORIGINS=["https://your-domain.com"]

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/people-management/api.log

# Rate limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_BURST=20
```

### 3. Database Migration

```bash
# Run migrations
cd /opt/people-management/app
uv run alembic upgrade head
```

### 4. Gunicorn Configuration

Create `/opt/people-management/app/gunicorn.conf.py`:

```python
"""
Gunicorn configuration for People Management System API.
"""

import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 2

# Restart workers after this many requests, to prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
log_level = "info"
accesslog = "/var/log/people-management/access.log"
errorlog = "/var/log/people-management/error.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "people-management-api"

# Server mechanics
daemon = False
pidfile = "/var/run/people-management/api.pid"
user = "peoplemgmt"
group = "peoplemgmt"
tmp_upload_dir = None

# SSL (if terminating SSL at Gunicorn level)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Environment
raw_env = [
    "ENVIRONMENT=production",
    "PATH=/opt/people-management/app/.venv/bin:/usr/local/bin:/usr/bin:/bin"
]

# Preload application for better performance
preload_app = True

# Worker lifecycle hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting People Management System API server")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading People Management System API")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGTERM."""
    worker.log.info("Worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker process is forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    """Called just after a worker process is forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info("Worker received SIGABRT signal")
```

### 5. Systemd Service

Create `/etc/systemd/system/people-management-api.service`:

```ini
[Unit]
Description=People Management System API
Requires=postgresql.service
After=network.target postgresql.service

[Service]
Type=notify
User=peoplemgmt
Group=peoplemgmt
RuntimeDirectory=people-management
WorkingDirectory=/opt/people-management/app
Environment=PATH=/opt/people-management/app/.venv/bin
Environment=ENVIRONMENT=production
ExecStart=/opt/people-management/app/.venv/bin/gunicorn server.main:app -c gunicorn.conf.py
ExecReload=/bin/kill -s HUP $MAINPID
TimeoutStopSec=30
Restart=always
RestartSec=3

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=/var/log/people-management /var/run/people-management
ProtectHome=yes

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable people-management-api
sudo systemctl start people-management-api
sudo systemctl status people-management-api
```

### 6. Nginx Configuration

Create `/etc/nginx/sites-available/people-management`:

```nginx
# People Management System API Nginx Configuration

upstream people_management_api {
    server 127.0.0.1:8000;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;

# API Server Configuration
server {
    listen 80;
    listen [::]:80;
    server_name api.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:MozTLS:10m;
    ssl_session_tickets off;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # Logging
    access_log /var/log/nginx/people-management-access.log;
    error_log /var/log/nginx/people-management-error.log;
    
    # Client settings
    client_max_body_size 10M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        application/json
        application/javascript
        text/css
        text/javascript
        text/xml
        application/xml
        application/xml+rss;
    
    # API endpoints
    location / {
        # Rate limiting
        limit_req zone=api_limit burst=20 nodelay;
        
        # Proxy settings
        proxy_pass http://people_management_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
    }
    
    # Stricter rate limiting for authentication endpoints
    location /api/v1/auth/ {
        limit_req zone=login_limit burst=5 nodelay;
        
        proxy_pass http://people_management_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check endpoint (no rate limiting)
    location /health {
        proxy_pass http://people_management_api;
        proxy_set_header Host $host;
        access_log off;
    }
    
    # Static files (if any)
    location /static/ {
        alias /opt/people-management/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/people-management /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Client Deployment

### Desktop Application Distribution

#### 1. Build Executable

```bash
# Install PyInstaller
uv add --dev pyinstaller

# Build executable
cd client/
uv run pyinstaller --onefile --windowed \
    --name "People Management System" \
    --icon resources/icons/app_icon.ico \
    main.py
```

#### 2. Create Installer (Windows)

Using NSIS (Nullsoft Scriptable Install System):

```nsis
; People Management System Installer Script

!define APPNAME "People Management System"
!define COMPANYNAME "Your Company"
!define DESCRIPTION "Desktop client for People Management System"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0

!include "MUI2.nsh"

Name "${APPNAME}"
OutFile "PeopleManagementSystem-Setup.exe"
InstallDir "$PROGRAMFILES\${COMPANYNAME}\${APPNAME}"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "Install"
    SetOutPath $INSTDIR
    File "dist\People Management System.exe"
    File "LICENSE.txt"
    File "README.txt"
    
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortcut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\People Management System.exe"
    CreateShortcut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\People Management System.exe"
    
    ; Register uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\People Management System.exe"
    Delete "$INSTDIR\LICENSE.txt"
    Delete "$INSTDIR\README.txt"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir "$INSTDIR"
    
    Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
    RMDir "$SMPROGRAMS\${APPNAME}"
    Delete "$DESKTOP\${APPNAME}.lnk"
    
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
SectionEnd
```

#### 3. macOS App Bundle

Create `build_macos.py`:

```python
"""
Build script for macOS app bundle.
"""

import os
import subprocess
import shutil
from pathlib import Path

def build_macos_app():
    """Build macOS application bundle."""
    
    # Build with PyInstaller
    subprocess.run([
        "uv", "run", "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", "People Management System",
        "--icon", "resources/icons/app_icon.icns",
        "--osx-bundle-identifier", "com.yourcompany.peoplemanagement",
        "main.py"
    ], check=True)
    
    # Codesign the app (requires Apple Developer certificate)
    app_path = "dist/People Management System.app"
    if os.path.exists(app_path):
        try:
            subprocess.run([
                "codesign",
                "--force",
                "--sign", "Developer ID Application: Your Name",
                "--deep",
                app_path
            ], check=True)
            print("App signed successfully")
        except subprocess.CalledProcessError:
            print("Warning: Could not sign app (certificate not found)")
    
    # Create DMG
    subprocess.run([
        "hdiutil", "create",
        "-srcfolder", app_path,
        "-volname", "People Management System",
        "dist/PeopleManagementSystem.dmg"
    ], check=True)
    
    print("macOS app bundle created successfully")

if __name__ == "__main__":
    build_macos_app()
```

#### 4. Linux AppImage

Create `build_appimage.py`:

```python
"""
Build script for Linux AppImage.
"""

import os
import subprocess
import shutil
from pathlib import Path

def build_appimage():
    """Build Linux AppImage."""
    
    # Build with PyInstaller
    subprocess.run([
        "uv", "run", "pyinstaller",
        "--onefile",
        "--name", "people-management-system",
        "main.py"
    ], check=True)
    
    # Create AppDir structure
    appdir = Path("dist/PeopleManagementSystem.AppDir")
    appdir.mkdir(exist_ok=True)
    
    # Copy executable
    shutil.copy("dist/people-management-system", appdir / "AppRun")
    os.chmod(appdir / "AppRun", 0o755)
    
    # Create desktop file
    desktop_content = """[Desktop Entry]
Type=Application
Name=People Management System
Comment=Desktop client for People Management System
Exec=AppRun
Icon=app_icon
Terminal=false
Categories=Office;
"""
    
    with open(appdir / "people-management-system.desktop", "w") as f:
        f.write(desktop_content)
    
    # Copy icon
    shutil.copy("resources/icons/app_icon.png", appdir / "app_icon.png")
    
    # Download and run appimagetool
    subprocess.run([
        "wget", "-O", "appimagetool",
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    ], check=True)
    
    os.chmod("appimagetool", 0o755)
    
    subprocess.run([
        "./appimagetool",
        str(appdir),
        "dist/PeopleManagementSystem-x86_64.AppImage"
    ], check=True)
    
    print("Linux AppImage created successfully")

if __name__ == "__main__":
    build_appimage()
```

## Database Configuration

### PostgreSQL Setup

#### 1. Install and Configure PostgreSQL

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### 2. Create Database and User

```bash
sudo -u postgres psql

-- Create database user
CREATE USER peoplemgmt_user WITH PASSWORD 'secure_password_here';

-- Create database
CREATE DATABASE peoplemgmt_db OWNER peoplemgmt_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE peoplemgmt_db TO peoplemgmt_user;

-- Exit psql
\q
```

#### 3. Configure PostgreSQL

Edit `/etc/postgresql/14/main/postgresql.conf`:

```conf
# Connection settings
listen_addresses = 'localhost'
port = 5432
max_connections = 100

# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_statement = 'mod'
log_duration = on
log_line_prefix = '%t [%p-%l] %q%u@%d '

# Backup settings
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/14/archive/%f'
```

Edit `/etc/postgresql/14/main/pg_hba.conf`:

```conf
# Local connections
local   all             postgres                                peer
local   all             all                                     peer

# IPv4 local connections
host    all             all             127.0.0.1/32            md5
host    peoplemgmt_db   peoplemgmt_user 127.0.0.1/32            md5

# IPv6 local connections
host    all             all             ::1/128                 md5
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

#### 4. Database Optimization

Create database optimization script:

```sql
-- /opt/people-management/scripts/optimize_db.sql

-- Optimize for read-heavy workloads
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activity_query_size = 2048;
ALTER SYSTEM SET pg_stat_statements.max = 10000;
ALTER SYSTEM SET pg_stat_statements.track = all;

-- Analyze tables regularly
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Create indexes for common queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_people_search 
ON people USING gin(to_tsvector('english', first_name || ' ' || last_name || ' ' || email));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_employment_active_dates 
ON employments (is_active, start_date, end_date) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_positions_department_title 
ON positions (department_id, title);

-- Update statistics
ANALYZE;
```

## Environment Configuration

### Production Environment Variables

Create `/opt/people-management/app/.env.production`:

```bash
# Application Configuration
ENVIRONMENT=production
APP_NAME="People Management System API"
APP_VERSION="1.0.0"
DEBUG=false

# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=false

# Database Configuration
DATABASE_URL=postgresql://peoplemgmt_user:secure_password@localhost:5432/peoplemgmt_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600

# Security Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
CORS_ORIGINS=["https://your-domain.com", "https://api.your-domain.com"]
ALLOWED_HOSTS=["your-domain.com", "api.your-domain.com"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_BURST=20

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/people-management/api.log
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=7

# Cache Configuration (if using Redis)
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=300

# Email Configuration (for notifications)
SMTP_HOST=smtp.your-domain.com
SMTP_PORT=587
SMTP_USER=api@your-domain.com
SMTP_PASSWORD=email_password
SMTP_TLS=true

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENABLE_METRICS=true
METRICS_PORT=9090
```

### Configuration Management

Create `/opt/people-management/scripts/manage_config.py`:

```python
"""
Configuration management script for production deployment.
"""

import os
import secrets
import argparse
from pathlib import Path
from cryptography.fernet import Fernet

def generate_secret_key():
    """Generate a secure secret key."""
    return secrets.token_urlsafe(32)

def encrypt_config(config_file, key_file):
    """Encrypt configuration file."""
    key = Fernet.generate_key()
    
    with open(key_file, 'wb') as f:
        f.write(key)
    
    cipher = Fernet(key)
    
    with open(config_file, 'rb') as f:
        data = f.read()
    
    encrypted_data = cipher.encrypt(data)
    
    with open(f"{config_file}.encrypted", 'wb') as f:
        f.write(encrypted_data)
    
    print(f"Configuration encrypted: {config_file}.encrypted")
    print(f"Key saved to: {key_file}")

def decrypt_config(encrypted_file, key_file, output_file):
    """Decrypt configuration file."""
    with open(key_file, 'rb') as f:
        key = f.read()
    
    cipher = Fernet(key)
    
    with open(encrypted_file, 'rb') as f:
        encrypted_data = f.read()
    
    decrypted_data = cipher.decrypt(encrypted_data)
    
    with open(output_file, 'wb') as f:
        f.write(decrypted_data)
    
    print(f"Configuration decrypted: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Manage production configuration")
    parser.add_argument("--generate-key", action="store_true", help="Generate secret key")
    parser.add_argument("--encrypt", nargs=2, metavar=("CONFIG", "KEY"), 
                       help="Encrypt config file")
    parser.add_argument("--decrypt", nargs=3, metavar=("ENCRYPTED", "KEY", "OUTPUT"),
                       help="Decrypt config file")
    
    args = parser.parse_args()
    
    if args.generate_key:
        key = generate_secret_key()
        print(f"Generated secret key: {key}")
    
    elif args.encrypt:
        encrypt_config(args.encrypt[0], args.encrypt[1])
    
    elif args.decrypt:
        decrypt_config(args.decrypt[0], args.decrypt[1], args.decrypt[2])
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
```

## Security Configuration

### SSL/TLS Setup

#### 1. Let's Encrypt Certificate

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d api.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add line: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### 2. Security Headers

Add to Nginx configuration:

```nginx
# Security headers
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';";
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()";
```

### Application Security

#### 1. Firewall Configuration

```bash
# Configure UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

#### 2. Fail2ban Configuration

Create `/etc/fail2ban/jail.local`:

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/people-management-error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/people-management-error.log
maxretry = 10
```

## Performance Optimization

### Application Optimization

#### 1. Database Connection Pooling

Configure in production settings:

```python
# server/core/config.py

class ProductionSettings(Settings):
    # Database connection pooling
    database_pool_size: int = 20
    database_max_overflow: int = 30
    database_pool_timeout: int = 30
    database_pool_recycle: int = 3600
    
    # Query optimization
    database_echo: bool = False
    database_pool_pre_ping: bool = True
```

#### 2. Caching Strategy

Implement Redis caching:

```python
# server/core/cache.py

import redis
from functools import wraps
import json
import pickle
from typing import Any, Optional

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(ttl: int = 300):
    """Cache function result with TTL."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return pickle.loads(cached)
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, pickle.dumps(result))
            
            return result
        return wrapper
    return decorator

# Usage example
@cache_result(ttl=600)  # Cache for 10 minutes
def get_department_statistics(department_id: str):
    # Expensive database query
    pass
```

#### 3. Background Tasks

Implement with Celery:

```python
# server/tasks.py

from celery import Celery
from .core.config import get_settings

settings = get_settings()
celery_app = Celery(
    "people_management",
    broker=settings.redis_url,
    backend=settings.redis_url
)

@celery_app.task
def send_welcome_email(person_id: str):
    """Send welcome email to new person."""
    # Implementation here
    pass

@celery_app.task
def generate_monthly_report():
    """Generate monthly employment report."""
    # Implementation here
    pass
```

### System Optimization

#### 1. Nginx Tuning

```nginx
# /etc/nginx/nginx.conf

worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # Buffer settings
    client_body_buffer_size 16K;
    client_header_buffer_size 1k;
    large_client_header_buffers 2 1k;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
}
```

#### 2. PostgreSQL Tuning

```conf
# /etc/postgresql/14/main/postgresql.conf

# Memory settings (for 8GB RAM server)
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
checkpoint_completion_target = 0.9
wal_buffers = 64MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200

# Connection settings
max_connections = 200
shared_preload_libraries = 'pg_stat_statements'

# WAL settings
wal_level = replica
max_wal_size = 2GB
min_wal_size = 80MB
checkpoint_timeout = 10min
```

## Monitoring and Logging

### Application Monitoring

#### 1. Prometheus Metrics

```python
# server/monitoring/metrics.py

from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
from functools import wraps

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('active_database_connections', 'Active database connections')
MEMORY_USAGE = Gauge('memory_usage_bytes', 'Memory usage in bytes')

def monitor_requests(func):
    """Monitor HTTP requests."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            REQUEST_COUNT.labels(method='GET', endpoint='/api/v1/people', status=200).inc()
            return result
        except Exception as e:
            REQUEST_COUNT.labels(method='GET', endpoint='/api/v1/people', status=500).inc()
            raise
        finally:
            REQUEST_DURATION.observe(time.time() - start_time)
    return wrapper

# Start metrics server
def start_metrics_server(port: int = 9090):
    start_http_server(port)
```

#### 2. Health Checks

```python
# server/monitoring/health.py

from typing import Dict, Any
from sqlalchemy import text
from ..database.db import get_db

async def check_database_health() -> Dict[str, Any]:
    """Check database health."""
    try:
        db = next(get_db())
        result = db.execute(text("SELECT 1")).fetchone()
        return {
            "status": "healthy",
            "response_time_ms": 10,
            "details": "Database connection successful"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "details": "Database connection failed"
        }

async def check_redis_health() -> Dict[str, Any]:
    """Check Redis health."""
    try:
        # Import and test Redis connection
        import redis
        client = redis.Redis(host='localhost', port=6379, db=0)
        client.ping()
        return {
            "status": "healthy",
            "details": "Redis connection successful"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "details": "Redis connection failed"
        }

async def comprehensive_health_check() -> Dict[str, Any]:
    """Perform comprehensive health check."""
    checks = {
        "database": await check_database_health(),
        "redis": await check_redis_health(),
        "disk_space": check_disk_space(),
        "memory": check_memory_usage(),
    }
    
    overall_status = "healthy" if all(
        check["status"] == "healthy" for check in checks.values()
    ) else "unhealthy"
    
    return {
        "status": overall_status,
        "timestamp": time.time(),
        "checks": checks
    }
```

### Logging Configuration

#### 1. Structured Logging

```python
# server/core/logging.py

import logging
import json
import sys
from typing import Any, Dict
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """JSON log formatter."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

def setup_logging(level: str = "INFO", log_file: str = None):
    """Set up application logging."""
    
    formatter = JSONFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    handlers = [console_handler]
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=handlers,
        force=True
    )
```

#### 2. Log Rotation

Create `/etc/logrotate.d/people-management`:

```
/var/log/people-management/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 peoplemgmt peoplemgmt
    postrotate
        systemctl reload people-management-api
    endscript
}

/var/log/nginx/people-management-*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data adm
    postrotate
        systemctl reload nginx
    endscript
}
```

## Backup and Recovery

### Database Backup

#### 1. Automated Backup Script

Create `/opt/people-management/scripts/backup_db.sh`:

```bash
#!/bin/bash

# Database backup script for People Management System
# Run as: ./backup_db.sh [full|incremental]

set -e

# Configuration
DB_NAME="peoplemgmt_db"
DB_USER="peoplemgmt_user"
BACKUP_DIR="/var/backups/people-management"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_TYPE=${1:-full}

# Create backup directory
mkdir -p "$BACKUP_DIR"
cd "$BACKUP_DIR"

# Full backup
if [ "$BACKUP_TYPE" = "full" ]; then
    echo "Starting full database backup..."
    
    # Create SQL dump
    pg_dump -U "$DB_USER" -h localhost -d "$DB_NAME" \
        --verbose --clean --no-owner --no-privileges \
        --file="$BACKUP_DIR/full_backup_$DATE.sql"
    
    # Compress backup
    gzip "$BACKUP_DIR/full_backup_$DATE.sql"
    
    echo "Full backup completed: full_backup_$DATE.sql.gz"

# Incremental backup using WAL files
elif [ "$BACKUP_TYPE" = "incremental" ]; then
    echo "Starting incremental backup..."
    
    # Archive WAL files
    rsync -av /var/lib/postgresql/14/archive/ \
        "$BACKUP_DIR/wal_archive_$DATE/"
    
    echo "Incremental backup completed: wal_archive_$DATE/"
fi

# Cleanup old backups
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "wal_archive_*" -type d -mtime +$RETENTION_DAYS -exec rm -rf {} +

# Upload to cloud storage (optional)
if [ -n "$AWS_S3_BUCKET" ]; then
    echo "Uploading backup to S3..."
    aws s3 cp "$BACKUP_DIR/full_backup_$DATE.sql.gz" \
        "s3://$AWS_S3_BUCKET/backups/database/"
fi

echo "Backup process completed successfully"
```

#### 2. Backup Cron Job

```bash
# Add to crontab (sudo crontab -e)

# Full backup daily at 2 AM
0 2 * * * /opt/people-management/scripts/backup_db.sh full >> /var/log/people-management/backup.log 2>&1

# Incremental backup every 6 hours
0 */6 * * * /opt/people-management/scripts/backup_db.sh incremental >> /var/log/people-management/backup.log 2>&1
```

### Application Backup

Create `/opt/people-management/scripts/backup_app.sh`:

```bash
#!/bin/bash

# Application backup script

set -e

BACKUP_DIR="/var/backups/people-management"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/opt/people-management/app"

echo "Starting application backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR/app"

# Backup application files
tar -czf "$BACKUP_DIR/app/app_backup_$DATE.tar.gz" \
    --exclude="*.pyc" \
    --exclude="__pycache__" \
    --exclude=".venv" \
    --exclude="*.log" \
    "$APP_DIR"

# Backup configuration
cp "$APP_DIR/.env.production" "$BACKUP_DIR/app/env_backup_$DATE"

# Backup logs
tar -czf "$BACKUP_DIR/app/logs_backup_$DATE.tar.gz" \
    /var/log/people-management/

echo "Application backup completed"
```

### Recovery Procedures

#### 1. Database Recovery

Create `/opt/people-management/scripts/restore_db.sh`:

```bash
#!/bin/bash

# Database restore script
# Usage: ./restore_db.sh <backup_file>

set -e

BACKUP_FILE="$1"
DB_NAME="peoplemgmt_db"
DB_USER="peoplemgmt_user"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

echo "WARNING: This will overwrite the existing database!"
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Stop application
sudo systemctl stop people-management-api

# Drop and recreate database
sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;"

# Restore from backup
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | psql -U "$DB_USER" -d "$DB_NAME"
else
    psql -U "$DB_USER" -d "$DB_NAME" < "$BACKUP_FILE"
fi

# Start application
sudo systemctl start people-management-api

echo "Database restore completed successfully"
```

#### 2. Point-in-Time Recovery

```bash
#!/bin/bash

# Point-in-time recovery script
# Usage: ./pitr_restore.sh <base_backup> <target_time>

BASE_BACKUP="$1"
TARGET_TIME="$2"

if [ -z "$BASE_BACKUP" ] || [ -z "$TARGET_TIME" ]; then
    echo "Usage: $0 <base_backup.tar.gz> <YYYY-MM-DD HH:MM:SS>"
    exit 1
fi

# Stop PostgreSQL
sudo systemctl stop postgresql

# Restore base backup
cd /var/lib/postgresql/14
sudo -u postgres tar -xzf "$BASE_BACKUP"

# Configure recovery
sudo -u postgres cat > recovery.conf << EOF
restore_command = 'cp /var/lib/postgresql/14/archive/%f %p'
recovery_target_time = '$TARGET_TIME'
recovery_target_action = 'promote'
EOF

# Start PostgreSQL
sudo systemctl start postgresql

echo "Point-in-time recovery completed"
```

## Maintenance Procedures

### Regular Maintenance Tasks

#### 1. Database Maintenance

Create `/opt/people-management/scripts/db_maintenance.sh`:

```bash
#!/bin/bash

# Database maintenance script

set -e

DB_NAME="peoplemgmt_db"
DB_USER="peoplemgmt_user"

echo "Starting database maintenance..."

# Update statistics
echo "Updating table statistics..."
psql -U "$DB_USER" -d "$DB_NAME" -c "ANALYZE;"

# Vacuum tables
echo "Vacuuming tables..."
psql -U "$DB_USER" -d "$DB_NAME" -c "VACUUM (ANALYZE, VERBOSE);"

# Reindex if needed
echo "Reindexing database..."
psql -U "$DB_USER" -d "$DB_NAME" -c "REINDEX DATABASE $DB_NAME;"

# Check for long-running queries
echo "Checking for long-running queries..."
psql -U "$DB_USER" -d "$DB_NAME" -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';"

echo "Database maintenance completed"
```

#### 2. Log Cleanup

```bash
#!/bin/bash

# Log cleanup script

set -e

LOG_DIR="/var/log/people-management"
NGINX_LOG_DIR="/var/log/nginx"
RETENTION_DAYS=30

echo "Cleaning up old log files..."

# Application logs
find "$LOG_DIR" -name "*.log" -mtime +$RETENTION_DAYS -delete
find "$LOG_DIR" -name "*.log.*" -mtime +$RETENTION_DAYS -delete

# Nginx logs
find "$NGINX_LOG_DIR" -name "people-management-*.log" -mtime +$RETENTION_DAYS -delete
find "$NGINX_LOG_DIR" -name "people-management-*.log.*" -mtime +$RETENTION_DAYS -delete

echo "Log cleanup completed"
```

#### 3. System Health Check

Create `/opt/people-management/scripts/health_check.sh`:

```bash
#!/bin/bash

# System health check script

set -e

echo "=== System Health Check Report ==="
echo "Date: $(date)"
echo

# Check disk space
echo "=== Disk Usage ==="
df -h | grep -E "(/$|/var|/opt)"
echo

# Check memory usage
echo "=== Memory Usage ==="
free -h
echo

# Check CPU load
echo "=== CPU Load ==="
uptime
echo

# Check database connections
echo "=== Database Connections ==="
sudo -u postgres psql -c "SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active';"
echo

# Check application status
echo "=== Application Status ==="
systemctl status people-management-api --no-pager
echo

# Check Nginx status
echo "=== Nginx Status ==="
systemctl status nginx --no-pager
echo

# Check PostgreSQL status
echo "=== PostgreSQL Status ==="
systemctl status postgresql --no-pager
echo

# Check recent errors in logs
echo "=== Recent Errors ==="
tail -n 50 /var/log/people-management/error.log | grep -i error || echo "No recent errors found"
echo

echo "=== Health Check Completed ==="
```

### Update Procedures

#### 1. Application Update Script

Create `/opt/people-management/scripts/update_app.sh`:

```bash
#!/bin/bash

# Application update script

set -e

APP_DIR="/opt/people-management/app"
BACKUP_DIR="/var/backups/people-management"
DATE=$(date +%Y%m%d_%H%M%S)

echo "Starting application update..."

# Backup current version
echo "Creating backup..."
tar -czf "$BACKUP_DIR/pre_update_backup_$DATE.tar.gz" "$APP_DIR"

# Stop application
echo "Stopping application..."
sudo systemctl stop people-management-api

# Update code
echo "Updating code..."
cd "$APP_DIR"
git fetch origin
git checkout main
git pull origin main

# Update dependencies
echo "Updating dependencies..."
uv sync --no-dev

# Run database migrations
echo "Running database migrations..."
uv run alembic upgrade head

# Update static files (if any)
echo "Updating static files..."
# Add static file update commands here

# Start application
echo "Starting application..."
sudo systemctl start people-management-api

# Wait for startup
sleep 10

# Health check
echo "Performing health check..."
curl -f http://localhost:8000/health || {
    echo "Health check failed! Rolling back..."
    sudo systemctl stop people-management-api
    cd "$APP_DIR"
    git checkout HEAD~1
    sudo systemctl start people-management-api
    exit 1
}

echo "Application update completed successfully"
```

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

```bash
# Check service status
sudo systemctl status people-management-api

# Check logs
sudo journalctl -u people-management-api -f

# Check application logs
tail -f /var/log/people-management/api.log

# Check configuration
cd /opt/people-management/app
uv run python -c "from server.core.config import get_settings; print(get_settings())"
```

#### 2. Database Connection Issues

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database connectivity
sudo -u postgres psql -c "SELECT version();"

# Check user permissions
sudo -u postgres psql -c "SELECT usename, usecreatedb, usesuper FROM pg_user WHERE usename = 'peoplemgmt_user';"

# Test application database connection
cd /opt/people-management/app
uv run python -c "
from server.database.db import engine
from sqlalchemy import text
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database connection successful')
"
```

#### 3. High Memory Usage

```bash
# Check memory usage by process
ps aux --sort=-%mem | head -20

# Check Python process memory
ps -o pid,ppid,%mem,%cpu,cmd --sort=-%mem | grep python

# Monitor memory usage over time
watch -n 5 'free -h && echo && ps aux --sort=-%mem | head -10'
```

#### 4. Slow API Responses

```bash
# Check database query performance
sudo -u postgres psql peoplemgmt_db -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"

# Check for long-running queries
sudo -u postgres psql peoplemgmt_db -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '1 minute';"

# Check Nginx access logs for slow requests
awk '$NF > 1000 { print $0 }' /var/log/nginx/people-management-access.log
```

### Emergency Procedures

#### 1. Emergency Shutdown

```bash
#!/bin/bash
# Emergency shutdown script

echo "Emergency shutdown initiated..."

# Stop application
sudo systemctl stop people-management-api

# Stop nginx
sudo systemctl stop nginx

# Stop postgresql (if safe to do so)
read -p "Stop PostgreSQL? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo systemctl stop postgresql
fi

echo "Emergency shutdown completed"
```

#### 2. Disaster Recovery

```bash
#!/bin/bash
# Disaster recovery script

set -e

echo "Starting disaster recovery..."

# Restore from latest backup
LATEST_BACKUP=$(ls -t /var/backups/people-management/full_backup_*.sql.gz | head -1)
if [ -n "$LATEST_BACKUP" ]; then
    echo "Restoring from: $LATEST_BACKUP"
    /opt/people-management/scripts/restore_db.sh "$LATEST_BACKUP"
else
    echo "No backup found!"
    exit 1
fi

# Restart all services
sudo systemctl start postgresql
sudo systemctl start people-management-api
sudo systemctl start nginx

echo "Disaster recovery completed"
```

---

This deployment guide provides comprehensive instructions for deploying the People Management System in production environments. Follow the procedures carefully and adapt them to your specific infrastructure requirements.