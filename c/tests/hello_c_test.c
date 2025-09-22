#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <check.h>

#define TEST 1

#define llm_query mock_llm_query
#include "../.hello_c.c.test"
#undef llm_query

#define BUFFER_SIZE 1024

// Mock function llm_query
char *mock_llm_query(const char *query)
{
	if (strcmp(query, "Please greet Test in en. Be creative, but not more than 50 words.") == 0)
		return strdup("Hello, Test");
	else
		return NULL;
}

START_TEST(test_ai_get_greeting)
{
	struct options opts = {
		.language = "en",
		.name = "Test"
	};
	char *greeting = ai_get_greeting(&opts);
	ck_assert_ptr_nonnull(greeting);
	free(greeting);
}
END_TEST

START_TEST(test_build_shopping_list_simple)
{
	struct options opts = {
		.shopping_items = (char *[]){"Apple", "Banana", "Orange"},
		.item_count = 3
	};

	char *shopping_list = build_shopping_list_simple(&opts);
	ck_assert_ptr_nonnull(shopping_list);

	const char *expected = "\nShopping list:\n- Apple\n- Banana\n- Orange\n";
	ck_assert_str_eq(shopping_list, expected);

	free(shopping_list);
}
END_TEST

START_TEST(test_get_options)
{
	struct options opts = {0};
	char *argv[] = {"program", "-l", "fr", "-n", "Alice", "-s", "Bread", "-s", "Milk", "-a", NULL};
	int argc = 10;

	int result = get_options(argc, argv, &opts);
	ck_assert_int_eq(result, 0);
	ck_assert_str_eq(opts.language, "fr");
	ck_assert_str_eq(opts.name, "Alice");
	ck_assert_int_eq(opts.item_count, 2);
	ck_assert_str_eq(opts.shopping_items[0], "Bread");
	ck_assert_str_eq(opts.shopping_items[1], "Milk");
	ck_assert_int_eq(opts.use_ai, 1);

	free(opts.shopping_items);
}
END_TEST

Suite *hello_c_suite(void)
{
	Suite *s;
	TCase *tc_core;

	s = suite_create("Hello C");
	tc_core = tcase_create("Core");

	tcase_add_test(tc_core, test_ai_get_greeting);
	tcase_add_test(tc_core, test_build_shopping_list_simple);
	tcase_add_test(tc_core, test_get_options);
	suite_add_tcase(s, tc_core);

	return s;
}

int main(void)
{
	int number_failed;
	Suite *s;
	SRunner *sr;

	s = hello_c_suite();
	sr = srunner_create(s);

	srunner_run_all(sr, CK_NORMAL);
	number_failed = srunner_ntests_failed(sr);
	srunner_free(sr);

	return (number_failed == 0) ? EXIT_SUCCESS : EXIT_FAILURE;
}
