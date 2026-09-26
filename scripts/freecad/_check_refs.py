import re

src = open(r'C:\Users\pmsma\Downloads\BIOBUZZ-Robot\scripts\freecad\dt_build.py').read()
refs = sorted(set(re.findall(r'Parameters\.([A-Za-z_][A-Za-z_0-9]*)', src)))
src2 = open(r'C:\Users\pmsma\Downloads\BIOBUZZ-Robot\scripts\freecad\robot_params.py').read()
aliases = set(re.findall(r'["\']([A-Za-z_][A-Za-z_0-9]*)["\']', src2))
missing = [r for r in refs if r not in aliases]
print('refs:', len(refs))
print('missing:', missing)
m = re.search(r'def create_sheet.*?(?=^def |\Z)', src2, re.M | re.S)
print(m.group(0)[:900] if m else 'no create_sheet')
# also list any pk.* calls
pkcalls = sorted(set(re.findall(r'pk\.([A-Za-z_][A-Za-z_0-9]*)', src)))
print('pk calls:', pkcalls)
