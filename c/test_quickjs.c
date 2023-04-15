#include <stdio.h>
#include <string.h>
#include <quickjs.h>
#include <quickjs-libc.h>

int main(int argc, char *argv[]) {
	float x = 2.0;
	const char *hello = "Hello, world";
	JSRuntime *rt = NULL;
	JSContext *ctx = NULL;
	JSValue hello_val = JS_UNDEFINED;
	JSValue global_obj = JS_UNDEFINED;
	JSValue x_val = JS_UNDEFINED;
	const char *script = "print(hello); y = Math.PI * x; print('world', y);";
	JSValue result = JS_UNDEFINED;
	JSValue y_val = JS_UNDEFINED;
	double y = 0;

	rt = JS_NewRuntime();
	ctx = JS_NewContext(rt);

	js_std_add_helpers(ctx, 0, NULL);

	hello_val = JS_NewString(ctx, hello);

	global_obj = JS_GetGlobalObject(ctx);

	JS_SetPropertyStr(ctx, global_obj, "hello", hello_val);

	x_val = JS_NewFloat64(ctx, x);
	JS_SetPropertyStr(ctx, global_obj, "x", x_val);

	if (JS_IsException(result = JS_Eval(ctx, script, strlen(script), "<eval_script>", 0))) {
		js_std_dump_error(ctx);
		fprintf(stderr, "eval failed\n");
		goto fail;
	}

//	js_std_loop(ctx);

	y_val = JS_GetPropertyStr(ctx, global_obj, "y");
	JS_ToFloat64(ctx, &y, y_val);

	printf("y = %.2f\n", y);

fail:
//	JS_FreeValue(ctx, hello_val);
//	JS_FreeValue(ctx, x_val);
//	JS_FreeValue(ctx, y_val);
//	JS_FreeValue(ctx, result);
	JS_FreeValue(ctx, global_obj);
//	js_std_free_handlers(rt);

	JS_FreeContext(ctx);
	JS_FreeRuntime(rt);

	return 0;
}

//	q. Why does js_std_free_handlers(rt) cause a segfault?
//	a. Because it is not needed.

//	XXX TODO This randomly segfaults / aborts / works if I free hello_val...
