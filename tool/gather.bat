@echo off

powershell.exe -Command "Set-ExecutionPolicy RemoteSigned; ..\env\Scripts\activate;python gather.py"