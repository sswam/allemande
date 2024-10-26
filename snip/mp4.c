
static uint64_t read_atom_size(int fd, off_t offset)
{
	uint32_t size32;
	uint64_t size64;

	if (pread_all(fd, &size32, sizeof(size32), offset) != sizeof(size32)) {
		perror("Error reading atom size");
		return 0;
	}

	size32 = ntohl(size32);

	if (size32 == 1) {
		if (pread_all(fd, &size64, sizeof(size64), offset + 8) != sizeof(size64)) {
			perror("Error reading 64-bit atom size");
			return 0;
		}
		return be64toh(size64);
	}

	return size32;
}

