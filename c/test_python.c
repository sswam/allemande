#include <Python.h>
#include <stdio.h>

int main() { // int argc, char *argv[]) {
	float x = 2;
	float y;
	char *hello = "Hello, world";

	Py_Initialize();

	PyRun_SimpleString("import this");
	PyRun_SimpleString("from math import pi");

	PyObject *main_module = PyImport_AddModule("__main__");
	PyObject *main_dict = PyModule_GetDict(main_module);

	PyObject *msg_object = PyUnicode_FromString(hello);
	PyDict_SetItemString(main_dict, "msg", msg_object);

	PyRun_SimpleString("print(msg)");

	PyObject *x_object = PyFloat_FromDouble(x);
	PyDict_SetItemString(main_dict, "x", x_object);

	PyRun_SimpleString("y = pi * x");

//	PyObject *y_object = PyNumber_Multiply(x_object, pi_object);

	PyObject *y_object = PyDict_GetItemString(main_dict, "y");
	Py_INCREF(y_object);

	y = PyFloat_AsDouble(y_object);

	printf("y = %.2f\n", y);

	Py_DECREF(x_object);
	Py_DECREF(y_object);

	// print ref count for each object
	printf("x_object ref count: %ld\n", x_object->ob_refcnt);
	printf("y_object ref count: %ld\n", y_object->ob_refcnt);

	Py_Finalize();
	return 0;
}
