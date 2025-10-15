# Plumbing Estimator - Automated Setup Script for Windows
# Run this script with: powershell -ExecutionPolicy Bypass -File install.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Plumbing Estimator - Automated Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Found: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "✗ Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.10 or 3.11 from https://www.python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists. Skipping..." -ForegroundColor Yellow
}
else {
    python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Virtual environment created" -ForegroundColor Green
    }
    else {
        Write-Host "✗ Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Virtual environment activated" -ForegroundColor Green
}
else {
    Write-Host "✗ Failed to activate virtual environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
    }
    else {
        Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}
else {
    Write-Host "✗ requirements.txt not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Run setup script to create folders
Write-Host ""
Write-Host "Creating project structure..." -ForegroundColor Yellow
if (Test-Path "setup.py") {
    python setup.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Project structure created" -ForegroundColor Green
    }
    else {
        Write-Host "✗ Failed to create project structure" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}
else {
    Write-Host "⚠ setup.py not found. Creating folders manually..." -ForegroundColor Yellow
    
    # Create directories
    $directories = @("database", "routes", "services", "middleware", "templates", "data", "uploads")
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir | Out-Null
            Write-Host "  Created: $dir/" -ForegroundColor Gray
        }
    }
}

# Verify project structure
Write-Host ""
Write-Host "Verifying project structure..." -ForegroundColor Yellow

$requiredFiles = @(
    "app.py",
    "config.py",
    "requirements.txt",
    "database\__init__.py",
    "database\db.py",
    "database\models.py",
    "routes\__init__.py",
    "routes\auth.py",
    "routes\admin.py",
    "routes\projects.py",
    "routes\drawings.py",
    "services\__init__.py",
    "services\pdf_processor.py",
    "services\detector.py",
    "middleware\__init__.py",
    "middleware\auth.py",
    "templates\login.html",
    "templates\company_select.html",
    "templates\admin.html",
    "templates\main.html"
)

$missingFiles = @()
foreach ($file in $requiredFiles) {
    if (!(Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "⚠ Missing files detected:" -ForegroundColor Yellow
    foreach ($file in $missingFiles) {
        Write-Host "  ✗ $file" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Please create the missing files before running the application." -ForegroundColor Yellow
}
else {
    Write-Host "✓ All required files present" -ForegroundColor Green
}

# Summary
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Make sure all Python files are in their correct folders" -ForegroundColor White
Write-Host "2. Make sure all HTML templates are in templates/ folder" -ForegroundColor White
Write-Host "3. Run the application with:" -ForegroundColor White
Write-Host "   python app.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "The application will be available at:" -ForegroundColor White
Write-Host "   http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Default admin credentials:" -ForegroundColor White
Write-Host "   Email: admin@example.com" -ForegroundColor Cyan
Write-Host "   Password: admin123" -ForegroundColor Cyan
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

# Ask if user wants to start the application now
Write-Host ""
$response = Read-Host "Would you like to start the application now? (y/n)"
if ($response -eq "y" -or $response -eq "Y") {
    Write-Host ""
    Write-Host "Starting application..." -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
    Write-Host ""
    python app.py
}
else {
    Write-Host ""
    Write-Host "You can start the application later by running:" -ForegroundColor White
    Write-Host "   python app.py" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Press Enter to exit"
}