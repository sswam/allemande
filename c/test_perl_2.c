#include <EXTERN.h>
#include <perl.h>

static PerlInterpreter *my_perl;
EXTERN_C void xs_init (pTHX);

int main(int argc, char **argv, char **env) {
	const char *perl_code = "sub calculate_y {"
					"my ($str, $x) = @_;"
					"print $str;"
					"use Math::Trig;"
					"my $y = pi * $x;"
					"print $y, '\\n';"
					"return $y;"
				"}";

	char *args[] = { "", "-e", (char *)perl_code };
	int num_args = sizeof(args) / sizeof(args[0]);
//	STRLEN n_a;

	PERL_SYS_INIT3(&argc, &argv, &env);
	my_perl = perl_alloc();
	perl_construct(my_perl);
	PL_exit_flags |= PERL_EXIT_DESTRUCT_END;

	perl_parse(my_perl, xs_init, num_args, args, NULL);
	perl_run(my_perl);

	dSP;
	ENTER;
	SAVETMPS;
	PUSHMARK(SP);

	const char *str = "Hello, world\n";
	int x = 2;
	XPUSHs(sv_2mortal(newSVpv(str, 0)));
	XPUSHs(sv_2mortal(newSViv(x)));
	PUTBACK;

	int count = call_pv("calculate_y", G_SCALAR);
	SPAGAIN;

	if (count != 1) {
		printf("ERROR: Call to calculate_y returned unexpected number of results: %d\n", count);
	} else {
		double y = POPn;
		printf("Y = %lf (printed from C)\n", y);
	}

	PUTBACK;
	FREETMPS;
	LEAVE;

	perl_destruct(my_perl);
	perl_free(my_perl);
	PERL_SYS_TERM();

	return 0;
}
