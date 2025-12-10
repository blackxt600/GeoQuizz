@echo off
REM Script wrapper pour Git qui contourne le probleme de configuration
REM Usage: git.bat [commandes git normales]
REM Exemple: git.bat status, git.bat commit -m "message", etc.

set HOME=C:\temp
git %*
