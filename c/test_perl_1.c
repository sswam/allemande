#include <EXTERN.h>
#include <perl.h>

static PerlInterpreter *my_perl;
EXTERN_C void xs_init (pTHX);

int main(int argc, char **argv, char **env) {
	char *perl_args[] = { "", "-e", "use Math::Trig; $x = 2; print 'Hello, world\n'; $y = pi * $x; print $y, '\n'" };
	int num_args = sizeof(perl_args) / sizeof(perl_args[0]);

	PERL_SYS_INIT3(&argc, &argv, &env);
	my_perl = perl_alloc();
	perl_construct(my_perl);
	PL_exit_flags |= PERL_EXIT_DESTRUCT_END;

	perl_parse(my_perl, xs_init, num_args, perl_args, NULL);
	perl_run(my_perl);

	perl_destruct(my_perl);
	perl_free(my_perl);
	PERL_SYS_TERM();

	return 0;
}
