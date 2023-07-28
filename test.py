import dis

with open('lib/aimbot.py', 'rb') as f:
    source_code = f.read()

bytecode = compile(source_code, 'lib/aimbot.py', 'exec')
dis.dis(bytecode)
