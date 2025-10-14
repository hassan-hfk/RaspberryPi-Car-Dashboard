@echo off
echo 🚗 Raspberry Pi Car Dashboard Setup
echo ====================================
echo.

REM Create directory structure
echo 📁 Creating directory structure...
mkdir static\css 2>nul
mkdir static\js 2>nul
mkdir templates 2>nul
echo ✅ Directories created!
echo.

REM Check Python installation
echo 🐍 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.7 or higher.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Found %PYTHON_VERSION%
echo.

REM Create virtual environment
echo 🔧 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo 📦 Installing dependencies...
pip install -r requirements.txt

echo.
echo ✅ Setup complete!
echo.
echo 📋 Next steps:
echo 1. Activate the virtual environment:
echo    venv\Scripts\activate
echo.
echo 2. Run the application:
echo    python app.py
echo.
echo 3. Open your browser and navigate to:
echo    http://localhost:5000
echo.
echo 4. For Raspberry Pi, update the VideoCamera class in app.py
echo    to use the actual camera instead of test video.
echo.
echo 🎉 Happy coding!
pause