@echo off

chcp 65001 > nul

powershell -Command "& lib\Python38\python.exe -m venv env"

echo Activating virtual environment...
:: Activate virtual environment
powershell -Command "& env\Scripts\Activate;python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip;pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple;pip install -r requirements.txt;pip install -r ./lib/yolov5-master/requirements.txt"

echo Script execution complete.
