@echo off
echo ================================
echo    Lancement de GeoQuizz
echo ================================
echo.

REM Vérifier si l'environnement virtuel existe
if not exist "venv\" (
    echo Creation de l'environnement virtuel...
    python -m venv venv
    echo.
)

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

REM Installer les dépendances
echo Installation des dependances...
pip install -r requirements.txt
echo.

REM Lancer l'application
echo Lancement du serveur...
echo.
python app.py

pause
