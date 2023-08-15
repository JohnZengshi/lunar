@echo off
chcp 65001 > nul

set "file_path=env\pyvenv.cfg"
set "temp_file=%temp%\temp_pyvenv.cfg"

REM 创建一个临时文件，将修改后的内容写入其中
echo home = %cd%\lib\Python38> "%temp_file%"
echo include-system-site-packages = false>> "%temp_file%"
echo version = 3.8.17>> "%temp_file%"

REM 备份原始的pyvenv.cfg文件
copy "%file_path%" "%file_path%.bak"

REM 将临时文件替换原始的pyvenv.cfg文件
copy "%temp_file%" "%file_path%" /y

REM 删除临时文件
del "%temp_file%"

REM pyvenv.cfg文件已成功修改。


REM 打开 PowerShell 并激活 Python 虚拟环境
if exist %cd%\lunar.pyc (
  powershell.exe -Command "Set-ExecutionPolicy RemoteSigned;env\Scripts\activate;python lunar.pyc"
) else (
  powershell.exe -Command "Set-ExecutionPolicy RemoteSigned;env\Scripts\activate;python lunar.py"
)