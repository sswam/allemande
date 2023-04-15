#include <cstdio>
#include <iostream>
#include <jsapi.h>
#include <js/CompilationAndEvaluation.h>
#include <js/SourceText.h>
#include <js/Initialization.h>
#include <js/Conversions.h>

using namespace std;

static JSObject* CreateGlobal(JSContext* cx) {
	JS::RealmOptions options;
	static JSClass BoilerplateGlobalClass = {
		"BoilerplateGlobal", JSCLASS_GLOBAL_FLAGS, &JS::DefaultGlobalClassOps};
	return JS_NewGlobalObject(cx, &BoilerplateGlobalClass, nullptr, JS::FireOnNewGlobalHook, options);
}

static bool ConsoleLog(JSContext* cx, unsigned argc, JS::Value* vp) {
	JS::CallArgs args = JS::CallArgsFromVp(argc, vp);

	for (unsigned i = 0; i < args.length(); i++) {
		JS::RootedString str(cx, JS::ToString(cx, args[i]));
		if (!str) {
			return false;
		}

		JS::UniqueChars buffer = JS_EncodeStringToUTF8(cx, str);
		if (!buffer) {
			return false;
		}

		printf("%s%s", i ? " " : "", buffer.get());
	}

	putchar('\n');
	args.rval().setUndefined();
	return true;
}

int test_mozjs(JSContext* cx) {
	// Create the global object
	JS::RootedObject global(cx, CreateGlobal(cx));
	if (!global) {
		return 1;
	}

	JSAutoRealm ar(cx, global);

	// Create the console object
	JS::RootedObject console(cx, JS_NewPlainObject(cx));
	if (!console) {
		return 1;
	}

	// Define the log function for the console object
	JSFunctionSpec consoleMethods[] = {
		JS_FN("log", ConsoleLog, 0, 0),
		JS_FS_END
	};

	if (!JS_DefineFunctions(cx, console, consoleMethods)) {
		return 1;
	}

	// Set the console object as a property of the global object
	JS::RootedValue consoleValue(cx, JS::ObjectValue(*console));
	if (!JS_SetProperty(cx, global, "console", consoleValue)) {
		return 1;
	}

	float x = 2.0;
	string hello = "Hello, world";
	double y;

	JS::CompileOptions options(cx);
	options.setFileAndLine("noname", 1);

	JS::RootedValue hello_val(cx);
	JS::RootedValue x_val(cx);
	JS::RootedValue y_val(cx);

	string code_console_log = "console.log('" + hello + "');";
	JS::SourceText<mozilla::Utf8Unit> source_console_log;
	if (!source_console_log.init(cx, code_console_log.c_str(), code_console_log.length(), JS::SourceOwnership::Borrowed)) {
		cerr << "error 1" << endl;
		return 1;
	}

	if (!JS::Evaluate(cx, options, source_console_log, &hello_val)) {
		cerr << "error 2" << endl;
		return 1;
	}

	string code_x = "x = " + to_string(x) + ";";
	JS::SourceText<mozilla::Utf8Unit> x_source;
	if (!x_source.init(cx, code_x.c_str(), code_x.length(), JS::SourceOwnership::Borrowed)) {
		cerr << "error 3" << endl;
		return 1;
	}

	if (!JS::Evaluate(cx, options, x_source, &x_val)) {
		cerr << "error 4" << endl;
		return 1;
	}

	string code_y = "y = Math.PI * x;";
	JS::SourceText<mozilla::Utf8Unit> y_source;
	if (!y_source.init(cx, code_y.c_str(), code_y.length(), JS::SourceOwnership::Borrowed)) {
		cerr << "error 5" << endl;
		return 1;
	}

	if (!JS::Evaluate(cx, options, y_source, &y_val)) {
		cerr << "error 6" << endl;
		return 1;
	}

	if (!JS::ToNumber(cx, y_val, &y)) {
		cerr << "error 7" << endl;
		return 1;
	}

	cout << "y = " << y << endl;

	return 0;
}


int main(int argc, char* argv[]) {
	if (!JS_Init()) {
		return 1;
	}

	JSContext* cx = JS_NewContext(JS::DefaultHeapMaxBytes);
	if (!cx) {
		return 1;
	}

	if (!JS::InitSelfHostedCode(cx)) {
		goto error;
	}

	test_mozjs(cx);

error:
	JS_DestroyContext(cx);
	JS_ShutDown();
	return 0;
}
