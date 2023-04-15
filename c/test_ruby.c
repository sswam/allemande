#include <ruby.h>

int main(int argc, char **argv) {
	VALUE y;
	double y_val;
//	ruby_sysinit(&argc, &argv);
//	RUBY_INIT_STACK;
//	ruby_init();
//	ruby_init_loadpath();
	ruby_setup();

	rb_eval_string("$x = 2");
	rb_eval_string("puts 'Hello, world'");
	rb_eval_string("$y = Math::PI * $x");
	y = rb_gv_get("y");
	y_val = NUM2DBL(y);

	printf("y = %.2f\n", y_val);

	ruby_cleanup(0);
	return 0;
}

// re: exceptions:
// https://stackoverflow.com/questions/9618957/ruby-interpreter-embed-in-c-code
// If the Ruby code raises an exception and it isn't caught, your C program will terminate. To overcome this, you need to do what the interpreter does and protect all calls that could raise an exception. This can get messy.
// You'll need to look into using the rb_protect function to wrap calls to Ruby that might cause an exception. The Pickaxe book has an example of this.
