#include <EXTERN.h>
#include <perl.h>

static PerlInterpreter *my_perl;
EXTERN_C void xs_init (pTHX);

int main(int argc, char **argv, char **env) {
//	const char *perl_code = "sub calculate_y {"
//	                            "use Math::Trig;"
//	                            "print $::str, \"\\n\";"
//	                            "$::y = pi * $::x;"
//	                            "print $::y, \"\\n\";"
//	                        "}";

	const char *perl_code =
		"use Math::Trig;"
		"print $str, \"\\n\";"
		"$y = pi * $x;"
		"print $y, \"\\n\";";

//	char *args[] = { "", "-e", (char *)perl_code };
	char *args[] = { "", "-e", "1" };
	int num_args = sizeof(args) / sizeof(args[0]);

	PERL_SYS_INIT3(&argc, &argv, &env);
	my_perl = perl_alloc();
	perl_construct(my_perl);
	PL_exit_flags |= PERL_EXIT_DESTRUCT_END;

	perl_parse(my_perl, xs_init, num_args, args, NULL);
	perl_run(my_perl);

	// Set Perl global variable $x from C
	SV *x_sv = get_sv("x", GV_ADD);
	const int x = 2;
	sv_setiv(x_sv, x);

	// Set Perl global variable $str from C
	SV *str_sv = get_sv("str", GV_ADD);
	const char *str = "Hello, world\n";
	sv_setpv(str_sv, str);

	// Evaluate the Perl code
	eval_pv(perl_code, TRUE);

//	call_pv("calculate_y", G_DISCARD | G_NOARGS);

	// Get Perl global variable $y from C
	SV *y_sv = get_sv("y", 0);
	double y = SvNV(y_sv);
	printf("Y = %lf (printed from C)\n", y);

	perl_destruct(my_perl);
	perl_free(my_perl);
	PERL_SYS_TERM();

	return 0;
}
