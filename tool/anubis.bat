@echo off

powershell.exe -Command "Set-ExecutionPolicy RemoteSigned; ..\env\Scripts\activate;python anubis.py ..\lunar.py ..\lib\aimbot.py ..\lib\inter.py ..\lib\key_validator.py"