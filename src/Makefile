ctests: bsglarray_test

clean:
	rm -f *.o
	rm -f bsglarray_test
	rm -rf build/temp.*/
	rm -rf build/lib.*/

bsglarray_test: bsglarray.c bsglarray.h bsglarray_test.c
	gcc bsglarray.c bsglarray_test.c -o $@ -g -std=c99 -Wall

pythonmodules:
	python setup.py build
