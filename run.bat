@echo off
REM Algo Solver - Full Stack Application Runner (Windows)
REM Combines Python optimization engine with Java Spring Boot + React frontend

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PYTHON_DIR=%SCRIPT_DIR%python"
set "DATA_DIR=%SCRIPT_DIR%data\output"
set "JAVA_DIR=%SCRIPT_DIR%java"
set "FRONTEND_DIR=%SCRIPT_DIR%frontend"

if "%1"=="" goto help
if "%1"=="start" goto start
if "%1"=="dev" goto dev
if "%1"=="frontend" goto frontend
if "%1"=="backend" goto backend
if "%1"=="build" goto build
if "%1"=="generate" goto generate
if "%1"=="results" goto results
if "%1"=="install" goto install
if "%1"=="clean" goto clean
goto help

:start
echo.
echo ========================================
echo Starting Full-Stack Application
echo ========================================
echo.
echo Building frontend...
cd /d "%FRONTEND_DIR%"
call npm run build
echo [✓] Frontend built to java\src\main\resources\static
echo.
echo Starting Spring Boot server...
cd /d "%JAVA_DIR%"
call mvn spring-boot:run
goto :eof

:dev
echo.
echo ========================================
echo Starting Development Servers
echo ========================================
echo.
echo This will start:
echo   • Frontend dev server: http://localhost:3000
echo   • Backend API server:  http://localhost:8080
echo.
echo Starting backend first...
cd /d "%JAVA_DIR%"
start "AlgoSolver Backend" cmd /c "mvn spring-boot:run"
timeout /t 5 /nobreak > nul
echo [✓] Backend running
echo.
echo Starting frontend...
cd /d "%FRONTEND_DIR%"
call npm run dev
goto :eof

:frontend
echo.
echo ========================================
echo Starting Frontend Dev Server Only
echo ========================================
echo.
echo Dev server: http://localhost:3000
echo API proxy:  http://localhost:8080
cd /d "%FRONTEND_DIR%"
call npm run dev
goto :eof

:backend
echo.
echo ========================================
echo Starting Backend API Server Only
echo ========================================
echo.
echo Spring Boot: http://localhost:8080
echo Browser will auto-open
cd /d "%JAVA_DIR%"
call mvn spring-boot:run
goto :eof

:build
echo.
echo ========================================
echo Building Full Application
echo ========================================
echo.
echo Installing frontend dependencies...
cd /d "%FRONTEND_DIR%"
call npm install
echo.
echo Building frontend for production...
call npm run build
echo [✓] Frontend built to java\src\main\resources\static\
echo.
echo Building Spring Boot application...
cd /d "%JAVA_DIR%"
call mvn clean package -DskipTests
echo [✓] Backend packaged to java\target\Algo_Solver-1.0.jar
echo.
echo ========================================
echo Build Complete
echo ========================================
echo Run with: run.bat start
echo Or JAR:   java -jar java\target\Algo_Solver-1.0.jar
goto :eof

:generate
echo.
echo ========================================
echo Generating Product Catalog (~100k products)
echo ========================================
echo.
cd /d "%PYTHON_DIR%"
python main.py
echo [✓] Products generated to: %DATA_DIR%\
goto :eof

:results
echo.
echo ========================================
echo Generated Results
echo ========================================
echo.
echo Files in %DATA_DIR%:
if exist "%DATA_DIR%" (
    dir /B "%DATA_DIR%"
) else (
    echo No results yet. Run 'run.bat generate' first.
)
goto :eof

:install
echo.
echo ========================================
echo Installing All Dependencies
echo ========================================
echo.
echo Installing frontend dependencies...
cd /d "%FRONTEND_DIR%"
call npm install
echo [✓] Frontend dependencies installed
echo.
echo Verifying Maven...
cd /d "%JAVA_DIR%"
call mvn --version
echo [✓] Maven ready
echo.
echo Verifying Python...
cd /d "%PYTHON_DIR%"
python --version
echo [✓] Python ready
echo.
echo ========================================
echo All Dependencies Ready
echo ========================================
goto :eof

:clean
echo.
echo ========================================
echo Cleaning Build Artifacts
echo ========================================
echo.
echo Cleaning frontend...
cd /d "%FRONTEND_DIR%"
if exist "dist" rmdir /S /Q dist
if exist "node_modules" rmdir /S /Q node_modules
echo.
echo Cleaning backend...
cd /d "%JAVA_DIR%"
call mvn clean
if exist "src\main\resources\static" rmdir /S /Q src\main\resources\static
mkdir src\main\resources\static
echo.
echo Cleaning Python cache...
cd /d "%PYTHON_DIR%"
for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /S /Q "%%d"
echo [✓] All build artifacts cleaned
goto :eof

:help
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                    ALGO SOLVER - RUNNER                        ║
echo ║          Python Optimization + Spring Boot + React             ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo Usage: run.bat [command]
echo.
echo 📦 FULL-STACK COMMANDS:
echo   start          Start production app (builds frontend + runs backend)
echo                  → Opens http://localhost:8080 automatically
echo.
echo   dev            Start dev servers (frontend + backend)
echo                  → Frontend: http://localhost:3000 (with hot reload)
echo                  → Backend:  http://localhost:8080
echo.
echo   frontend       Start only frontend dev server (port 3000)
echo   backend        Start only backend server (port 8080)
echo   build          Build complete application for production
echo.
echo 🐍 PYTHON OPTIMIZATION ENGINE:
echo   generate       Generate product catalog (~100k products)
echo   results        Show generated data files
echo.
echo 🛠️  UTILITIES:
echo   install        Install all dependencies (npm + verify Maven/Python)
echo   clean          Remove all build artifacts
echo.
echo 💡 QUICK START:
echo   run.bat install       # First time only
echo   run.bat dev           # Development mode
echo   run.bat generate      # Generate product data
echo.
echo   Or production:
echo   run.bat build         # Build everything
echo   run.bat start         # Run production app (auto-opens browser)
echo.
echo 📚 CONFIGURATION:
echo   - Python engine:  config\app.yaml
echo   - Spring Boot:    java\src\main\resources\application.properties
echo   - Frontend:       frontend\vite.config.js
echo.
echo 🌐 URLs:
echo   Production:  http://localhost:8080  (Spring Boot serves React)
echo   Development: http://localhost:3000  (Vite dev server with HMR)
echo                http://localhost:8080  (Spring Boot API)
echo.
echo ⚙️  DISABLE AUTO-BROWSER:
echo   Edit java\src\main\resources\application.properties:
echo     app.open-browser=false
echo.
goto :eof
