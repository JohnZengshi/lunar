@echo off
chcp 65001 > nul
setlocal

REM 设置路径和文件名
set "source_folder=.\"
set "destination_folder=.\build\"
set "lunar=lunar"
set "aimbot=aimbot"
set "inter=inter"
set "key_validator=key_validator"
set "__pycache__=.\__pycache__\"
set "lib__pycache__=.\lib\__pycache__\"

REM 创建目标文件夹
if not exist "%destination_folder%" (
    mkdir "%destination_folder%"
)

@REM REM 复制文件夹和文件
@REM xcopy /s /y "%source_folder%env" "%destination_folder%env\"
xcopy /s /y "%source_folder%lib\config" "%destination_folder%lib\config\"
xcopy /s /y "%source_folder%lib\interception" "%destination_folder%lib\interception\"
xcopy /s /y "%source_folder%lib\interception_py" "%destination_folder%lib\interception_py\"
xcopy /s /y "%source_folder%lib\Python38" "%destination_folder%lib\Python38\"
xcopy /s /y "%source_folder%lib\yolov5-master" "%destination_folder%lib\yolov5-master\"
xcopy /s /y "%source_folder%使用说明" "%destination_folder%使用说明\"
xcopy /s /y "%source_folder%更新包使用说明" "%destination_folder%更新包使用说明\"

copy /y "%source_folder%lib\bestv2.pt" "%destination_folder%lib\"
copy /y "%source_folder%setup.bat" "%destination_folder%"
copy /y "%source_folder%install.bat" "%destination_folder%"
copy /y "%source_folder%start.bat" "%destination_folder%"
copy /y "%source_folder%requirements.txt" "%destination_folder%"

REM 执行 pyarmor gen 命令
pyarmor gen --output %destination_folder%lib\ %source_folder%lib\aimbot.py
pyarmor gen --output %destination_folder%lib\ %source_folder%lib\inter.py
pyarmor gen --output %destination_folder%lib\ %source_folder%lib\key_validator.py
pyarmor gen --output %destination_folder% lunar.py

@REM REM 混淆
@REM call python .\tool\anubis.py lunar.py lib\aimbot.py lib\inter.py lib\key_validator.py

@REM rem 使用py_compile编译Python文件
@REM call python -m py_compile %lunar%-obf.py %source_folder%lib\%aimbot%-obf.py %source_folder%lib\%inter%-obf.py %source_folder%lib\%key_validator%-obf.py 


@REM rem 将编译后的.pyc文件复制到指定文件夹，并重命名
@REM copy %__pycache__%%lunar%-obf.cpython-38.pyc %destination_folder%\%lunar%.pyc

@REM copy %lib__pycache__%%aimbot%-obf.cpython-38.pyc %destination_folder%lib\%aimbot%.pyc
@REM copy %lib__pycache__%%inter%-obf.cpython-38.pyc %destination_folder%lib\%inter%.pyc
@REM copy %lib__pycache__%%key_validator%-obf.cpython-38.pyc %destination_folder%lib\%key_validator%.pyc


endlocal
