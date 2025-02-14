#include <ctype.h>
#include <dirent.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <getopt.h>

#define VERSION "0.1.3"
#define MAX_PROCESSES 1024
#define MAX_LINE 1024
#define MAX_CMD 256

struct process {
	pid_t pid;
	pid_t ppid;
	char cmdline[MAX_CMD];
	char cmd_name[MAX_CMD];
	long rss;
	long vsz;
	float pcpu;
	float pmem;
};

struct process_group {
	char cmd_name[MAX_CMD];
	char cmdline[MAX_CMD];
	long rss;
	long vsz;
	float pcpu;
	float pmem;
	int count;
};

/* Get total system RAM in KB */
static long get_system_ram(void)
{
	FILE *fp;
	char line[MAX_LINE];
	long total_ram = 0;

	fp = fopen("/proc/meminfo", "r");
	if (!fp)
		return 0;

	while (fgets(line, sizeof(line), fp)) {
		if (strncmp(line, "MemTotal:", 9) == 0) {
			sscanf(line, "MemTotal: %ld", &total_ram);
			break;
		}
	}
	fclose(fp);
	return total_ram;
}

/* Read process information from /proc/[pid] */
static int read_proc_entry(pid_t pid, long total_ram, struct process *proc)
{
	FILE *fp;
	char path[MAX_LINE];
	char line[MAX_LINE];
	char stat[MAX_LINE];

	/* Read stat file */
	snprintf(path, sizeof(path), "/proc/%d/stat", pid);
	fp = fopen(path, "r");
	if (!fp)
		return -1;

	if (!fgets(stat, sizeof(stat), fp)) {
		fclose(fp);
		return -1;
	}
	fclose(fp);

	/* Read status file for memory info */
	snprintf(path, sizeof(path), "/proc/%d/status", pid);
	fp = fopen(path, "r");
	if (!fp)
		return -1;

	proc->rss = 0;
	proc->vsz = 0;

	while (fgets(line, sizeof(line), fp)) {
		if (strncmp(line, "VmRSS:", 6) == 0)
			sscanf(line, "VmRSS: %ld", &proc->rss);
		else if (strncmp(line, "VmSize:", 7) == 0)
			sscanf(line, "VmSize: %ld", &proc->vsz);
	}
	fclose(fp);

	/* Parse basic info from stat */
	char *ptr = strchr(stat, '(');
	char *end = strrchr(stat, ')');
	if (!ptr || !end)
		return -1;

	proc->pid = pid;
	sscanf(end + 1, "%*s %d", &proc->ppid);

	/* Use stat command name as fallback */
	strncpy(proc->cmd_name, ptr + 1, end - ptr - 1);
	proc->cmd_name[end - ptr - 1] = '\0';
	strncpy(proc->cmdline, proc->cmd_name, MAX_CMD - 1);

	/* Try to read actual command line */
	snprintf(path, sizeof(path), "/proc/%d/cmdline", pid);
	fp = fopen(path, "r");
	if (fp) {
		if (fgets(line, sizeof(line), fp)) {
			char *space = strchr(line, ' ');
			if (space)
				*space = '\0';
			if (strlen(line) > 0) {
				strncpy(proc->cmd_name, line, MAX_CMD - 1);
				strncpy(proc->cmdline, line, MAX_CMD - 1);
			}
		}
		fclose(fp);
	}

	proc->pcpu = 0.0f; /* TODO: implement CPU calculation */
	proc->pmem = total_ram ? ((float)proc->rss / total_ram) * 100.0f : 0.0f;

	return 0;
}

static int compare_rss(const void *a, const void *b)
{
	return ((struct process *)b)->rss - ((struct process *)a)->rss;
}

static int compare_vsz(const void *a, const void *b)
{
	return ((struct process *)b)->vsz - ((struct process *)a)->vsz;
}

static int compare_pcpu(const void *a, const void *b)
{
	return ((struct process *)b)->pcpu > ((struct process *)a)->pcpu ? 1 : -1;
}

static int compare_pmem(const void *a, const void *b)
{
	return ((struct process *)b)->pmem > ((struct process *)a)->pmem ? 1 : -1;
}

static void group_processes(struct process *processes, int proc_count, struct process_group *groups,
			    int *group_count)
{
	*group_count = 0;

	for (int i = 0; i < proc_count; i++) {
		int found = 0;
		for (int j = 0; j < *group_count; j++) {
			if (strcmp(processes[i].cmd_name, groups[j].cmd_name) == 0) {
				groups[j].rss += processes[i].rss;
				groups[j].vsz += processes[i].vsz;
				groups[j].pcpu += processes[i].pcpu;
				groups[j].pmem += processes[i].pmem;
				groups[j].count++;
				found = 1;
				break;
			}
		}

		if (!found && *group_count < MAX_PROCESSES) {
			strncpy(groups[*group_count].cmd_name, processes[i].cmd_name, MAX_CMD - 1);
			strncpy(groups[*group_count].cmdline, processes[i].cmdline, MAX_CMD - 1);
			groups[*group_count].rss = processes[i].rss;
			groups[*group_count].vsz = processes[i].vsz;
			groups[*group_count].pcpu = processes[i].pcpu;
			groups[*group_count].pmem = processes[i].pmem;
			groups[*group_count].count = 1;
			(*group_count)++;
		}
	}
}

static int compare_group_rss(const void *a, const void *b)
{
    const struct process_group *ga = a;
    const struct process_group *gb = b;
    return gb->rss - ga->rss;
}

static int compare_group_vsz(const void *a, const void *b)
{
    const struct process_group *ga = a;
    const struct process_group *gb = b;
    return gb->vsz - ga->vsz;
}

static int compare_group_pcpu(const void *a, const void *b)
{
    const struct process_group *ga = a;
    const struct process_group *gb = b;
    return gb->pcpu > ga->pcpu ? 1 : -1;
}

static int compare_group_pmem(const void *a, const void *b)
{
    const struct process_group *ga = a;
    const struct process_group *gb = b;
    return gb->pmem > ga->pmem ? 1 : -1;
}

static void print_usage(void)
{
    fprintf(stderr, "Usage: top_grouped [-s sort_field] [-n limit]\n");
    fprintf(stderr, "  -s sort_field   Sort by: rss, vsz, pcpu, pmem\n");
    fprintf(stderr, "  -n limit        Number of processes to show\n");
}

int main(int argc, char *argv[])
{
    DIR *proc_dir;
    struct dirent *entry;
    struct process processes[MAX_PROCESSES];
    struct process_group groups[MAX_PROCESSES];
    int proc_count = 0;
    int group_count = 0;
    long total_ram;
    int opt;
    char *sort_by = "rss";
    int limit = 20;

    while ((opt = getopt(argc, argv, "s:n:h")) != -1) {
        switch (opt) {
        case 's':
            sort_by = optarg;
            break;
        case 'n':
            limit = atoi(optarg);
            if (limit <= 0) {
                fprintf(stderr, "Error: Invalid limit\n");
                return 1;
            }
            break;
        case 'h':
            print_usage();
            return 0;
        default:
            print_usage();
            return 1;
        }
    }

    total_ram = get_system_ram();
    if (!total_ram) {
        fprintf(stderr, "Error: Could not get system RAM\n");
        return 1;
    }

    proc_dir = opendir("/proc");
    if (!proc_dir) {
        fprintf(stderr, "Error: Could not open /proc\n");
        return 1;
    }

    while ((entry = readdir(proc_dir)) != NULL && proc_count < MAX_PROCESSES) {
        if (!isdigit(entry->d_name[0]))
            continue;

        pid_t pid = atoi(entry->d_name);
        if (read_proc_entry(pid, total_ram, &processes[proc_count]) == 0)
            proc_count++;
    }
    closedir(proc_dir);

    /* Group processes and sort based on selected field */
    group_processes(processes, proc_count, groups, &group_count);

    if (strcmp(sort_by, "vsz") == 0)
        qsort(groups, group_count, sizeof(struct process_group), compare_group_vsz);
    else if (strcmp(sort_by, "pcpu") == 0)
        qsort(groups, group_count, sizeof(struct process_group), compare_group_pcpu);
    else if (strcmp(sort_by, "pmem") == 0)
        qsort(groups, group_count, sizeof(struct process_group), compare_group_pmem);
    else
        qsort(groups, group_count, sizeof(struct process_group), compare_group_rss);

    printf("VSZ(MB)\tRSS(MB)\t%%CPU\t%%MEM\tCOUNT\tCOMMAND\n");

    for (int i = 0; i < limit && i < group_count; i++) {
        printf("%ld\t%ld\t%.1f\t%.1f\t%d\t%s\n",
            groups[i].vsz / 1024, groups[i].rss / 1024,
            groups[i].pcpu, groups[i].pmem,
            groups[i].count, groups[i].cmdline);
    }

    return 0;
}
