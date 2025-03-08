@echo off
SolidWriting.exe %*
if %errorlevel% neq 0 (
    echo Hata: %errorlevel%
    pause
)
exit
