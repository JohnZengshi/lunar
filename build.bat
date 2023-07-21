@echo off
chcp 65001 > nul
setlocal

REM 设置路径和文件名
set "source_folder=.\"
set "destination_folder=.\dist\"
set "lunar_file=lunar.py"

REM 创建目标文件夹
if not exist "%destination_folder%" (
    mkdir "%destination_folder%"
)

@REM REM 复制文件夹和文件
@REM xcopy /s /y "%source_folder%env" "%destination_folder%env\"
xcopy /s /y "%source_folder%lib" "%destination_folder%lib\"
xcopy /s /y "%source_folder%使用说明" "%destination_folder%使用说明\"
copy /y "%source_folder%setup.bat" "%destination_folder%"
copy /y "%source_folder%install.bat" "%destination_folder%"
copy /y "%source_folder%start.bat" "%destination_folder%"
copy /y "%source_folder%requirements.txt" "%destination_folder%"

REM 执行 pyarmor gen 命令
pyarmor gen --output %destination_folder%lib\ %source_folder%lib\aimbot.py
pyarmor gen --output %destination_folder%lib\ %source_folder%lib\inter.py
pyarmor gen --output %destination_folder%lib\ %source_folder%lib\key_validator.py

@REM REM 执行 pyarmor gen lunar.py 命令
pyarmor gen "%source_folder%lunar.py"

endlocal
