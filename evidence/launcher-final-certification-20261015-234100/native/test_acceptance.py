import sys, os
sys.path.insert(0, '.')
import module
ok = True
try:
    assert module.add(2, 3) == 5
    assert module.add(-2, 3) == 1
    assert module.add(0, 0) == 0
except AssertionError:
    ok = False
readme = 'README.md'
if not os.path.isfile(readme):
    ok = False
else:
    with open(readme, 'r', encoding='utf-8') as f:
        if 'áéíóú ñ ¿? € ° "comillas"' not in f.read():
            ok = False
if ok:
    print('ACCEPTANCE_PASS')
    sys.exit(0)
else:
    print('ACCEPTANCE_FAIL')
    sys.exit(1)
