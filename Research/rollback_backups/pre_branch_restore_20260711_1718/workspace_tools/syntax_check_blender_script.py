import py_compile, sys
py_compile.compile(sys.argv[-1], doraise=True)
print('SCRIPT_COMPILE_OK', sys.argv[-1])
