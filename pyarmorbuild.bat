@echo off
chcp 65001 > nul
setlocal

REM 设置路径和文件名
set "source_folder=.\"
set "destination_folder=.\dist\"

pyarmor gen --output %destination_folder%lib\ %source_folder%lib\aimbot.py
pyarmor gen --output %destination_folder%lib\ %source_folder%lib\inter.py
pyarmor gen --output %destination_folder%lib\ %source_folder%lib\key_validator.py
pyarmor gen %source_folder%lunar.py

endlocal