#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <check.h>

#define TEST 1

#include "../htmlsplit.c"

START_TEST(test_get_options_defaults)
{
	struct options opts = {0};
	char *argv[] = {"program", NULL};
	int argc = 1;

	int result = get_options(argc, argv, &opts);
	ck_assert_int_eq(result, 0);
	ck_assert_int_eq(opts.chunk_size, DEFAULT_CHUNK_SIZE);
}
END_TEST

START_TEST(test_get_options_chunk_size)
{
	struct options opts = {0};
	char *argv[] = {"program", "-c", "8192", NULL};
	int argc = 3;

	int result = get_options(argc, argv, &opts);
	ck_assert_int_eq(result, 0);
	ck_assert_int_eq(opts.chunk_size, 8192);
}
END_TEST

START_TEST(test_get_options_invalid_chunk_size)
{
	struct options opts = {0};
	char *argv[] = {"program", "-c", "invalid", NULL};
	int argc = 3;

	int result = get_options(argc, argv, &opts);
	ck_assert_int_eq(result, -1);
}
END_TEST

START_TEST(test_process_html_simple)
{
	char *out_buf = NULL;
	size_t out_size = 0;
	const char *input_str = "<html><body>test</body></html>";
	const char *expected = "<html>\n<body>\ntest\n</body>\n</html>\n";

	FILE *input = fmemopen((void*)input_str, strlen(input_str), "r");
	FILE *output = open_memstream(&out_buf, &out_size);
	ck_assert_ptr_nonnull(input);
	ck_assert_ptr_nonnull(output);

	int result = process_html(input, output, DEFAULT_CHUNK_SIZE);
	fclose(input);
	fclose(output);

	ck_assert_int_eq(result, 0);
	ck_assert_str_eq(out_buf, expected);
	free(out_buf);
}
END_TEST

START_TEST(test_process_html_text_between_tags)
{
	char *out_buf = NULL;
	size_t out_size = 0;
	const char *input_str = "Hello<p>World</p>!";
	const char *expected = "Hello\n<p>\nWorld\n</p>\n!\n";

	FILE *input = fmemopen((void*)input_str, strlen(input_str), "r");
	FILE *output = open_memstream(&out_buf, &out_size);

	int result = process_html(input, output, DEFAULT_CHUNK_SIZE);
	fclose(input);
	fclose(output);

	ck_assert_int_eq(result, 0);
	ck_assert_str_eq(out_buf, expected);
	free(out_buf);
}
END_TEST

START_TEST(test_process_html_empty)
{
	char *out_buf = NULL;
	size_t out_size = 0;
	const char *input_str = "";

	FILE *input = fmemopen((void*)input_str, strlen(input_str), "r");
	FILE *output = open_memstream(&out_buf, &out_size);

	int result = process_html(input, output, DEFAULT_CHUNK_SIZE);
	fclose(input);
	fclose(output);

	ck_assert_int_eq(result, 0);
	ck_assert_int_eq(out_size, 0);
	free(out_buf);
}
END_TEST

START_TEST(test_ensure_buffer_space)
{
	char *buffer = malloc(10);
	size_t buf_size = 10;

	int result = ensure_buffer_space(&buffer, &buf_size, 20, 10);
	ck_assert_int_eq(result, 0);
	ck_assert_int_eq(buf_size, 30);

	free(buffer);
}
END_TEST

START_TEST(test_process_complete_tags)
{
	char *out_buf = NULL;
	size_t out_size = 0;
	char *html = strdup("<p>Hello</p><br>");
	size_t content_size = strlen(html);
	FILE *output = open_memstream(&out_buf, &out_size);

	int result = process_complete_tags(&html, &content_size, output);
	fclose(output);

	ck_assert_int_eq(result, 0);
	free(html);
	free(out_buf);
}
END_TEST

Suite *htmlsplit_suite(void)
{
	Suite *s;
	TCase *tc_core;

	s = suite_create("HTMLSplit");
	tc_core = tcase_create("Core");

	tcase_add_test(tc_core, test_get_options_defaults);
	tcase_add_test(tc_core, test_get_options_chunk_size);
	tcase_add_test(tc_core, test_get_options_invalid_chunk_size);
	tcase_add_test(tc_core, test_process_html_simple);
 	tcase_add_test(tc_core, test_process_html_text_between_tags);
 	tcase_add_test(tc_core, test_process_html_empty);
	tcase_add_test(tc_core, test_ensure_buffer_space);
	tcase_add_test(tc_core, test_process_complete_tags);
	suite_add_tcase(s, tc_core);

	return s;
}

int main(void)
{
	int number_failed;
	Suite *s;
	SRunner *sr;

	s = htmlsplit_suite();
	sr = srunner_create(s);

	srunner_run_all(sr, CK_NORMAL);
	number_failed = srunner_ntests_failed(sr);
	srunner_free(sr);

	return (number_failed == 0) ? EXIT_SUCCESS : EXIT_FAILURE;
}
