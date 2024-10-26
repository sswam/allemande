START_TEST(test_touch_ctime)
{
	int fd;
	struct statx initial_statx, new_statx;
	__s64 initial_ctime, new_ctime, initial_atime, new_atime, initial_mtime, new_mtime;

	// Create a test file
	fd = open(TEST_FILE, O_CREAT | O_WRONLY, 0644);
	ck_assert_int_ge(fd, 0);
	close(fd);

	// Get initial times
	ck_assert_int_eq(statx(AT_FDCWD, TEST_FILE, 0, STATX_CTIME | STATX_ATIME | STATX_MTIME, &initial_statx), 0);
	initial_ctime = initial_statx.stx_ctime.tv_sec;
	initial_atime = initial_statx.stx_atime.tv_sec;
	initial_mtime = initial_statx.stx_mtime.tv_sec;

	// Sleep for a second to ensure ctime will be different
	sleep(1);

	// Call touch_ctime
	ck_assert_int_eq(touch_ctime(TEST_FILE), 0);

	// Get new times
	ck_assert_int_eq(statx(AT_FDCWD, TEST_FILE, 0, STATX_CTIME | STATX_ATIME | STATX_MTIME, &new_statx), 0);
	new_ctime = new_statx.stx_ctime.tv_sec;
	new_atime = new_statx.stx_atime.tv_sec;
	new_mtime = new_statx.stx_mtime.tv_sec;

	// Check that ctime has been updated
	ck_assert_int_ne(initial_ctime, new_ctime);

	// Check that atime and mtime have not changed
	ck_assert_int_eq(initial_atime, new_atime);
	ck_assert_int_eq(initial_mtime, new_mtime);

	// Clean up
	unlink(TEST_FILE);
}
