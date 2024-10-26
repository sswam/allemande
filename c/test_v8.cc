#include <iostream>
#include <libplatform/libplatform.h>
#include <v8.h>

using namespace v8;

// Custom console.log() function
void ConsoleLogCallback(const FunctionCallbackInfo<Value>& args) {
	Isolate* isolate = args.GetIsolate();
	HandleScope handle_scope(isolate);

	if (args.Length() == 0) {
		return;
	}

	String::Utf8Value utf8_value(isolate, args[0]);
	std::cout << *utf8_value << std::endl;
}

int main(int argc, char *argv[]) {
	float x = 2.0;
	std::string hello = "Hello, world";

	V8::InitializeICUDefaultLocation(argv[0]);
	V8::InitializeExternalStartupData(argv[0]);
	std::unique_ptr<Platform> platform = platform::NewDefaultPlatform();
	V8::InitializePlatform(platform.get());
	V8::Initialize();

	Isolate::CreateParams create_params;
	create_params.array_buffer_allocator = ArrayBuffer::Allocator::NewDefaultAllocator();
	Isolate *isolate = Isolate::New(create_params);

	{
		Isolate::Scope isolate_scope(isolate);
		HandleScope handle_scope(isolate);

		Local<Context> context = Context::New(isolate);
		Context::Scope context_scope(context);

		// Binding custom console.log() function
		Local<Object> global = context->Global();
		Local<Object> console = Object::New(isolate);
		Maybe<bool> console_set_result = global->Set(context, String::NewFromUtf8Literal(isolate, "console"), console);
		if (console_set_result.IsNothing() || !console_set_result.FromJust()) {
			std::cout << "Failed to set console object" << std::endl;
			return 1;
		}
		Local<FunctionTemplate> log_template = FunctionTemplate::New(isolate, ConsoleLogCallback);
		Maybe<bool> log_set_result = console->Set(context, String::NewFromUtf8Literal(isolate, "log"), log_template->GetFunction(context).ToLocalChecked());
		if (log_set_result.IsNothing() || !log_set_result.FromJust()) {
			std::cout << "Failed to set console.log() function" << std::endl;
			return 1;
		}

		// main script
		Local<String> hello_str = String::NewFromUtf8(isolate, hello.c_str()).ToLocalChecked();
		context->Global()->Set(context, String::NewFromUtf8(isolate, "hello").ToLocalChecked(), hello_str).FromJust();

		Local<Number> x_val = Number::New(isolate, x);
		context->Global()->Set(context, String::NewFromUtf8(isolate, "x").ToLocalChecked(), x_val).FromJust();

		const char* script_source = "console.log(hello); y = Math.PI * x;";
		Local<String> source = String::NewFromUtf8(isolate, script_source).ToLocalChecked();
		// string types: NewStringType::kNormal, NewStringType::kInternalized, NewStringType::kUndetectable
		Local<Script> script = Script::Compile(context, source).ToLocalChecked();
//		script->Run(context);
		Local<Value> result_val = script->Run(context).ToLocalChecked();
		double result = result_val->NumberValue(context).ToChecked();

		Local<Value> y_val = context->Global()->Get(context, String::NewFromUtf8(isolate, "y").ToLocalChecked()).ToLocalChecked();
		double y = y_val->NumberValue(context).ToChecked();

		std::cout << "result = " << result << std::endl;
		std::cout << "y = " << y << std::endl;
	}

	isolate->Dispose();
	V8::Dispose();
	V8::DisposePlatform();
	delete create_params.array_buffer_allocator;

	return 0;
}
