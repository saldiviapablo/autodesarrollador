import sys, py_compile
try:
    py_compile.compile('module.py', doraise=True)
    print('BUILD_PASS')
    sys.exit(0)
except Exception as e:
    print(f'BUILD_FAIL: {e}')
    sys.exit(1)
