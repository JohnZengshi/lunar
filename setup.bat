@echo off

echo Activating virtual environment...
:: Activate virtual environment
powershell -Command "& env\Scripts\Activate"

echo Installing/upgrading pip with Tsinghua mirror...
:: Install/upgrade pip with Tsinghua mirror
powershell -Command "python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip"

echo Setting global index-url to Tsinghua mirror...
:: Set global index-url to Tsinghua mirror
powershell -Command "pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple"


powershell -Command "pip install -r requirements.txt"

echo Script execution complete.
