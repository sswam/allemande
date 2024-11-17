// 2>/dev/null; . shebang-c

/*
 * MP4 Fast Start
 * Version: 1.0.7
 *
 * This program quickly moves the 'moov' atom to the start of MP4 files,
 * to improve streaming, using fallocate to "punch a hole" for it.
 *
 * Usage: mp4-fast-start [mp4_file ...]
 *
 * Options:
 *   -h, --help    Show this help message and exit
 *
 * Example:
 *   mp4-fast-start video1.mp4 video2.mp4
 */

#define _GNU_SOURCE

#include <arpa/inet.h>
#include <fcntl.h>
#include <inttypes.h>
#include <libgen.h>
#include <linux/falloc.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/statvfs.h>
#include <sys/types.h>
#include <unistd.h>
#include <stdbool.h>
#include <signal.h>
#include <sys/stat.h>

void segv_handler(int sig) {
	fflush(stdout);
	signal(sig, SIG_DFL);
	raise(sig);
}

#define MAX_ATOM_SIZE (100 * 1024 * 1024) // 100 MB max atom size

#define SEARCH_BUFFER_SIZE (10 * 1024 * 1024) // 10 MB search buffer

struct atom {
	uint32_t size;
	uint8_t name[4];
	uint8_t data[];
};

struct atom64 {
	uint32_t one;
	uint8_t name[4];
	uint64_t size;
	uint8_t data[];
};

static unsigned long get_fs_block_size(const char *path)
{
	struct statvfs buf = {0};
	if (statvfs(path, &buf) == -1)
		return 0;
	return buf.f_bsize;
}

static void hexdump(const void *data, size_t size)
{
	const uint8_t *p = data;
	size_t i;

	for (i = 0; i < size; i++) {
		printf("%02x ", (unsigned)p[i]);
		if ((i + 1) % 16 == 0)
			printf("\n");
	}
	printf("\n");
}

static ssize_t pread_all(int fd, void *buf, size_t count, off_t offset)
{
	ssize_t total_nread = 0;
	ssize_t nread;
	char *p = buf;

	while ((size_t)total_nread < count) {
		nread = pread(fd, p, count - total_nread, offset);
		if (nread == -1)
			return -1;
		if (nread == 0)
			break;
		p += nread;
		offset += nread;
		total_nread += nread;
	}
	return total_nread;
}

static ssize_t pwrite_all(int fd, const void *buf, size_t count, off_t offset)
{
	ssize_t total_nwritten = 0;
	ssize_t nwritten;
	const char *p = buf;

	while ((size_t)total_nwritten < count) {
		nwritten = pwrite(fd, p, count - total_nwritten, offset);
		if (nwritten == -1)
			return -1;
		p += nwritten;
		offset += nwritten;
		total_nwritten += nwritten;
	}
	return total_nwritten;
}

static struct atom read_atom_header(int fd, off_t offset)
{
	struct atom header = {0};
	ssize_t nread;

	nread = pread_all(fd, &header, sizeof(header), offset);
	if (nread != (ssize_t)sizeof(header)) {
		perror("Error reading atom header");
		memset(&header, 0, sizeof(header));
	}

	header.size = ntohl(header.size);

	return header;
}

/*@null@*/ static struct atom *read_atom(int fd, off_t offset, const char *name)
{
	struct atom header = {0};
	/*@out@*/ struct atom *atom;
	ssize_t nread;

	header = read_atom_header(fd, offset);
	if (header.size == 0)
		return NULL;

	if (name != NULL && memcmp(header.name, name, 4) != 0) {
		fprintf(stderr, "Atom name does not match\n");
		return NULL;
	}

	if (header.size > MAX_ATOM_SIZE) {
		fprintf(stderr, "Atom size too large: %" PRIu32 "\n", header.size);
		return NULL;
	}

	atom = malloc(header.size);
	if (atom == NULL) {
		perror("Error allocating memory");
		return NULL;
	}

	nread = pread_all(fd, atom, header.size, offset);
	if (nread != (ssize_t)header.size) {
		perror("Error reading atom");
		goto free_atom;
	}

	return atom;

free_atom:
	free(atom);
	return NULL;
}

static int write_atom(int fd, struct atom *atom, off_t offset)
{
	ssize_t nwritten;
	uint32_t size = ntohl(atom->size);

	nwritten = pwrite_all(fd, atom, (size_t)size, offset);
	if (nwritten != (ssize_t)size) {
		perror("Error writing atom");
		printf("Bytes written: %zd of %" PRIu32 "\n", nwritten, size);
		return -1;
	}

	return 0;
}

static int find_moov_atom_near_end(int fd, off_t file_size, off_t *moov_start)
{
	off_t start;
	static uint8_t buffer[SEARCH_BUFFER_SIZE];
	ssize_t nread;
	off_t pos;
	ssize_t i;
	struct atom header;

	/* 10MB will be okay for most, but we should search progressively
	 * further back in the file, also we should check the start first,
	 * because it might already be a fast start file */

	printf("File size: %jd\n", (intmax_t)file_size);

	start = (file_size > SEARCH_BUFFER_SIZE) ? file_size - SEARCH_BUFFER_SIZE : 0;
	start = (start + 3) & ~3; // align to 4-byte boundary

	for (pos = start; pos <= file_size - 8; pos += nread - 7) {
		printf("Current position: %jd\n", (intmax_t)pos);
		nread = pread_all(fd, buffer, sizeof(buffer), pos);
		printf("Bytes read: %zd\n", nread);
		if (nread <= 0) {
			perror("Error reading file");
			return -1;
		}

		for (i = 0; i <= nread - 8; i += 1) {
			if (memcmp(buffer + i + 4, "moov", 4) != 0)
				continue;
			printf("MOOV atom found at position %jd\n", (intmax_t)(pos + i));
			hexdump(buffer + i, sizeof(struct atom));
			header = read_atom_header(fd, pos + i);
			if (header.size == 0) {
				fprintf(stderr, "Error reading MOOV atom header\n");
				continue;
			}
			printf("Atom size: %" PRIu32 "\n", header.size);
			if (pos + i + header.size != file_size) {
				fprintf(stderr, "Atom size is incorrect, continuing search\n");
				continue;
			}
			*moov_start = pos + i;
			return 0;
		}
	}

	fprintf(stderr, "MOOV atom not found\n");
	return -1;
}

typedef int (*atom_callback)(struct atom *, void *);

/* Find all child atoms under the parent atom, recursively
 * Note: all atom sizes must be in network byte order */
static int find_child_atoms(struct atom *parent, const char *path, atom_callback callback,
			    void *data)
{
	struct atom *child;
	int status = 0;
	off_t offset;
	uint32_t parent_size;

	parent_size = ntohl(parent->size);

	fprintf(stderr, "Finding child atoms: %s\n", path);

	if (parent_size < sizeof(struct atom)) {
		fprintf(stderr, "Invalid parent atom size: %" PRIu32 "\n", parent_size);
		return -1;
	}

	for (offset = sizeof(struct atom); offset <= (off_t)(parent_size - sizeof(struct atom));
	     offset += ntohl(child->size)) {
		child = (struct atom *)((char *)parent + offset);
		/* check for the end of the atom, if it is nul padded */
		if (memcmp(&child->name, "\0\0\0\0", 4) == 0)
			break;
		/* check for a matching child atom name */
		if (strncmp((char *)child->name, path, 4) == 0) {
			/* is this the end of the path? */
			if (strlen(path) == 4)
				status += callback(child, data);
			/* check for the path separator */
			else if (path[4] == '.')
				find_child_atoms(child, path + 5, callback, data);
			/* invalid path: software error */
			else {
				fprintf(stderr, "Invalid atom path: %s\n", path);
				exit(1);
			}
		}
	}
	/* The status is zero for success, or negatve the number of errors */
	return status;
}

/* List all atoms under the parent atom, recursively
 * Note: all atom sizes must be in network byte order */
void list_atoms(struct atom *parent, int level) {
	struct atom *child;
	off_t offset;
	uint32_t parent_size;
	uint32_t child_size;

	parent_size = ntohl(parent->size);

	// Print the current atom with proper indentation
	for (int i = 0; i < level; i++) {
		printf("  "); // Two spaces for each level of indentation
	}
	printf("%c%c%c%c (size: %u)\n",
		parent->name[0], parent->name[1], parent->name[2], parent->name[3],
		parent_size);

	// Traverse child atoms
	for (offset = sizeof(struct atom); offset <= (off_t)(parent_size - sizeof(struct atom));
		offset += ntohl(child->size)) {
		child = (struct atom *)((char *)parent + offset);
		child_size = ntohl(child->size);

		// Check for zero atom size
		if (child_size == 0) {
			fprintf(stderr, "Warning: Zero atom size encountered\n");
			break;
		}

		// Check for invalid atom size, which would go outside the parent atom
		if (offset + child_size > parent_size) {
			fprintf(stderr, "Warning: Invalid atom size encountered\n");
			break;
		}

		// Check for unlikely atom names
		if (child->name[0] < 0x20 || child->name[0] > 0x7E ||
			child->name[1] < 0x20 || child->name[1] > 0x7E ||
			child->name[2] < 0x20 || child->name[2] > 0x7E ||
			child->name[3] < 0x20 || child->name[3] > 0x7E) {
			break;
		}

		// Check for the end of the atom, if it is null padded
		if (memcmp(&child->name, "\0\0\0\0", 4) == 0)
			break;

		// Recursively list child atoms
		list_atoms(child, level + 1);
	}
}

void list_all_atoms_in_file(char *buffer, size_t buffer_length) {
	struct atom *current_atom;
	size_t offset = 0;
	uint32_t size;

	while (offset < buffer_length) {
		current_atom = (struct atom *)(buffer + offset);

		// Check if we have enough space left in the buffer for a complete atom
		if (offset + sizeof(struct atom) > buffer_length) {
			printf("Warning: Incomplete atom at the end of the file\n");
			break;
		}

		// Check for valid atom size
		size = ntohl(current_atom->size);
		if (size == 0 || offset + size > buffer_length) {
			printf("Warning: Invalid atom size encountered\n");
			break;
		}

		// Call list_atoms for the current top-level atom
		list_atoms(current_atom, 0);

		// Move to the next atom
		offset += size;
	}
}

struct __attribute__((packed)) stco {
	uint32_t size;
	uint32_t type; // 'stco'
	uint8_t version;
	uint8_t flags[3];
	uint32_t count;
	uint32_t data[]; // Array of 32-bit chunk offsets
};

struct __attribute__((packed)) co64 {
	uint32_t size;
	uint32_t type; // 'co64'
	uint8_t version;
	uint8_t flags[3];
	uint32_t entry_count;
	uint64_t chunk_offset[]; // Array of 64-bit chunk offsets
};

static int adjust_stco_callback(struct atom *atom, void *data)
{
	uint32_t count, i;
	uint64_t *adjustment = data;
	uint32_t *entry;

	count = ntohl(*(uint32_t *)(atom->data + 4));

	for (i = 0; i < count; i++) {
		entry = (uint32_t *)(atom->data + 8) + i;
		*entry = htonl(ntohl(*entry) + (uint32_t)*adjustment);
		fprintf(stderr, "STCO entry %u: %" PRIu32 "\n", i, *entry);
	}

	return 0;
}

static int adjust_co64_callback(struct atom *atom, void *data)
{
	uint32_t count, i;
	uint64_t *adjustment = data;
	uint64_t *entry;

	count = ntohl(*(uint32_t *)(atom->data + 4));

	for (i = 0; i < count; i++) {
		entry = (uint64_t *)(atom->data + 8) + i;
		*entry = htobe64(be64toh(*entry) + *adjustment);
		fprintf(stderr, "CO64 entry %u: %" PRIu64 "\n", i, *entry);
	}

	return 0;
}

static int adjust_moov_offsets(struct atom *moov, uint64_t adjustment)
{
	int status = 0;
	status +=
	    find_child_atoms(moov, "trak.mdia.minf.stbl.stco", adjust_stco_callback, &adjustment);
	status +=
	    find_child_atoms(moov, "trak.mdia.minf.stbl.co64", adjust_co64_callback, &adjustment);
	return status;
}

static int move_moov_to_start(const char *filename, bool simulate)
{
	int status = -1;
	int fd = -1;
	off_t file_size;
	off_t moov_start = 0;
	struct atom *ftyp = NULL;
	struct atom moov_header;
	struct atom *moov = NULL;
	unsigned long block_size;
	uint32_t moov_size, moov_size_rounded, ftyp_size;

	printf("Opening %s\n", filename);

	/* get the file system block size */
	block_size = get_fs_block_size(filename);
	if (block_size == 0) {
		perror("Error getting file system block size");
		goto fail;
	}

	/* open the file */
	fd = open(filename, O_RDWR);
	if (fd == -1) {
		perror("Error opening file");
		goto fail;
	}

	/* get the file size */
	file_size = lseek(fd, 0, SEEK_END);
	if (file_size == -1) {
		perror("Error getting file size");
		goto close_fd;
	}

	/* read the FTYP atom */
	ftyp = read_atom(fd, 0, "ftyp");
	if (ftyp == NULL) {
		perror("Error reading FTYP atom");
		goto close_fd;
	}

	/* look for a MOOV atom at the start of the file */
	moov_header = read_atom_header(fd, (off_t)ntohl(ftyp->size));
	if (moov_header.size == 0) {
		fprintf(stderr, "Error reading MOOV atom header\n");
		goto free_ftyp;
	}
	if (memcmp(moov_header.name, "moov", 4) == 0) {
		fprintf(stderr, "MOOV atom found at start of file, nothing to do\n");
		status = 0;
		goto free_ftyp;
	}

	/* find the MOOV atom near the end of the file */
	if (find_moov_atom_near_end(fd, file_size, &moov_start) != 0) {
		fprintf(stderr, "Error finding MOOV atom\n");
		goto free_ftyp;
	}

	/* read the MOOV atom */
	moov = read_atom(fd, moov_start, "moov");
	if (moov == NULL) {
		perror("Error reading MOOV atom");
		goto close_fd;
	}

	/* round up the MOOV atom size to the nearest block size */
	moov_size = ntohl(moov->size);
	moov_size_rounded = (moov_size + block_size - 1) / block_size * block_size;

	/* insert space for the new MOOV atom */
	if (!simulate && fallocate(fd, FALLOC_FL_INSERT_RANGE, 0, (off_t)moov_size_rounded) != 0) {
		perror("Error inserting space for MOOV atom");
		goto free_moov;
	} else {
		fprintf(stderr, "simulate: Skipping fallocate to insert space for MOOV atom\n");
	}

	/* write the new ftyp atom */
	if (!simulate && write_atom(fd, ftyp, 0) != 0) {
		perror("Error writing FTYP atom");
		goto free_moov;
	} else {
		fprintf(stderr, "simulate: Skipping writing FTYP atom\n");
	}

	/* zero the old ftyp atom */
	ftyp_size = ntohl(ftyp->size);
	memset(ftyp, 0, ftyp_size);
	if (!simulate && pwrite_all(fd, ftyp, ftyp_size, (off_t)moov_size_rounded) != (ssize_t)ftyp_size) {
		perror("Error zeroing old FTYP atom");
		goto free_moov;
	} else {
		fprintf(stderr, "simulate: Skipping zeroing old FTYP atom\n");
	}

	/* Dump all atoms under the moov atom */
	list_atoms(moov, 0);

	/* adjust pointers in the stco atoms in moov */
	if (adjust_moov_offsets(moov, (off_t)moov_size_rounded)) {
		fprintf(stderr, "Error adjusting MOOV atom offsets\n");
		goto free_moov;
	}

	/* write the new moov atom */
	if (!simulate && write_atom(fd, moov, (off_t)ftyp_size) != 0)
		goto free_moov;
	else
		fprintf(stderr, "simulate: Skipping writing MOOV atom\n");

	/* rewrite the header with the rounded size */
	moov->size = htonl(moov_size_rounded);
	if (!simulate && pwrite_all(fd, moov, sizeof(struct atom), (off_t)ftyp_size) !=
	    (ssize_t)sizeof(struct atom)) {
		perror("Error writing MOOV atom header");
		goto free_moov;
	} else {
		fprintf(stderr, "simulate: Skipping writing MOOV atom header\n");
	}

	/* try to remove the original MOOV atom */
	if (moov_start + moov_size == file_size) {
		/* truncate the file */
		if (!simulate && ftruncate(fd, (off_t)(moov_start + moov_size_rounded)) != 0) {
			perror("Error truncating file");
			goto free_moov;
		} else {
			fprintf(stderr, "simulate: Skipping truncating file\n");
		}
	} else {
		/* punch a hole over the original MOOV atom, probably will not
		 * work */
		if (!simulate && fallocate(fd, FALLOC_FL_PUNCH_HOLE, (off_t)(moov_start + moov_size_rounded),
			      (off_t)moov_size) != 0)
			perror("Error removing original MOOV atom with fallocate");
		else
			fprintf(stderr, "simulate: Skipping removing original MOOV atom with fallocate\n");
		/* continue anyway, it's not crucial to remove the
		 * original MOOV atom */
	}

	printf("Successfully moved MOOV atom to start of %s\n", filename);
	if (simulate)
		printf("(simulation only, file was not changed)\n");
	status = 0;

	/* cleanup */
free_moov:
	free(moov);
free_ftyp:
	free(ftyp);
close_fd:
	if (close(fd) != 0) {
		perror("Error closing file");
		status = -1;
	}
fail:
	if (status != 0)
		fprintf(stderr, "Failed to process %s\n", filename);
	return status;
}

int main(int argc, char *argv[])
{
	int i, opt;
	int simulate = 0;

	signal(SIGSEGV, segv_handler);

	while ((opt = getopt(argc, argv, "hn")) != -1) {
		switch (opt) {
		case 'h':
			printf("Usage: %s [-n] [mp4_file ...]\n", basename(argv[0]));
			printf("  -n  Simulate (don't write changes to file)\n");
			exit(0);
		case 'n':
			simulate = 1;
			break;
		default:
			fprintf(stderr, "Try '%s --help' for more information\n", basename(argv[0]));
			exit(1);
		}
	}

	/* process each file */
	for (i = optind; i < argc; i++)
		move_moov_to_start(argv[i], simulate);

	exit(0);
}

/* TODO handle atoms with size = 0, means "until EOF" */
