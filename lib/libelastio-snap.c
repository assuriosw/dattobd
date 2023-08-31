// SPDX-License-Identifier: LGPL-2.1-or-later

/*
 * Copyright (C) 2015 Datto Inc.
 * Additional contributions by Elastio Software, Inc are Copyright (C) 2020 Elastio Software Inc.
 */

#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <string.h>
#include <stdio.h>
#include <sys/stat.h>
#include <dirent.h>
#include "libelastio-snap.h"

/* For any active snapshot/incremental, the reload script is created
 * and placed inside this directory. After the reboot, on the system
 * startup, the kernel mounts it and runs all scripts to restore the
 * last state of the snapshot devices. When the snapshot is destroyed,
 * the relevant script is removed.
 */
#define RELOAD_SCRIPT_PATH		"/etc/elastio/dla"
#define ELIOCTL_BIN_PATH		"/usr/bin/"

#define BUF_SIZE				512
#define RELOAD_SCRIPT_BDEV_SIZE	128
#define RELOAD_SCRIPT_COW_SIZE	256

struct reload_script_params {
	int snapshot;
	unsigned int minor;
	unsigned int cache_size;
	int ignore_snap_errors;
	char bdev[RELOAD_SCRIPT_BDEV_SIZE];
	char cow[RELOAD_SCRIPT_COW_SIZE];
};

int check_reload_dir()
{
	DIR *dir = opendir(RELOAD_SCRIPT_PATH);
	if (dir) {
		closedir(dir);
		return 0;
	}

	return -1;
}

int elastio_snap_get_reload_params(unsigned int minor, struct reload_script_params *rp)
{
	FILE *fd;
	int ret;
	char buf[BUF_SIZE];
	char f_name[BUF_SIZE];
	char mode[32] = { 0 };
	char ignore_errors[16] = { 0 };

	snprintf(f_name, sizeof(f_name), "%s/reload_%d.sh", RELOAD_SCRIPT_PATH, minor);

	fd = fopen(f_name, "r");
	if (!fd)
		return -1;

	if (fread(buf, 1, BUF_SIZE, fd) == 0) {
		fclose(fd);
		return -1;
	}

	ret = sscanf(buf, ELIOCTL_BIN_PATH "elioctl reload-%s -c %u %s %s %u %s",
			mode, &rp->cache_size, rp->bdev, rp->cow, &rp->minor, ignore_errors);

	if (ret != 5 && ret != 6) {
		fclose(fd);
		return -1;
	}

	if (!strcmp(ignore_errors, "-i"))
		rp->ignore_snap_errors = 1;
	else
		rp->ignore_snap_errors = 0;

	if (!strcmp(mode, "snapshot"))
		rp->snapshot = 1;
	else
		rp->snapshot = 0;

	fclose(fd);
	return 0;
}

int elastio_snap_set_reload_params(unsigned int minor, bool snapshot, const struct reload_script_params *rp)
{
	FILE* fd;
	char buf[BUF_SIZE];
	char f_name[BUF_SIZE];

	snprintf(f_name, sizeof(f_name), "%s/reload_%d.sh", RELOAD_SCRIPT_PATH, minor);

	memset(buf, 0, sizeof(buf));
	fd = fopen(f_name, "w");
	if (!fd)
		return -1;

	int ret = snprintf(buf, sizeof(buf), ELIOCTL_BIN_PATH "elioctl reload-%s -c %u %s %s %u %s\n",
			snapshot ? "snapshot" : "incremental", rp->cache_size, rp->bdev,
			rp->cow, rp->minor, rp->ignore_snap_errors ? "-i" : "");

	ret = fwrite(buf, 1, strlen(buf) + 1, fd);
	if (ret == -1) {
		fclose(fd);
		return -1;
	}

	fclose(fd);

	if (chmod(f_name, S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH | S_IXGRP ) == -1) {
		return -1;
	}


	return 0;
}

int elastio_snap_setup_snapshot(unsigned int minor, char *bdev, char *cow, unsigned long fallocated_space, unsigned long cache_size, bool ignore_snap_errors){
	int fd, ret;
	struct setup_params sp;

	fd = open("/dev/elastio-snap-ctl", O_RDONLY);
	if(fd < 0) return -1;

	sp.minor = minor;
	sp.bdev = bdev;
	sp.cow = cow;
	sp.fallocated_space = fallocated_space;
	sp.cache_size = cache_size;
	sp.ignore_snap_errors = ignore_snap_errors;

	ret = ioctl(fd, IOCTL_SETUP_SNAP, &sp);
	if (ret == 0) {
		struct reload_script_params rp;

		if (check_reload_dir()) {
			if (system("mkdir -p " RELOAD_SCRIPT_PATH))
				// if something deletes the path, restore it,
				// and no snapshots for you until you fix it
				return -1;
		}

		rp.minor = minor;
		rp.cache_size = cache_size;
		rp.ignore_snap_errors = ignore_snap_errors;
		strcpy(rp.bdev, bdev);
		strcpy(rp.cow, cow);

		if (elastio_snap_set_reload_params(minor, true, &rp)) {
			ret = ENOENT;
		}
	}

	close(fd);
	return ret;
}

int elastio_snap_reload_snapshot(unsigned int minor, char *bdev, char *cow, unsigned long cache_size, bool ignore_snap_errors){
	int fd, ret;
	struct reload_params rp;

	fd = open("/dev/elastio-snap-ctl", O_RDONLY);
	if(fd < 0) return -1;

	rp.minor = minor;
	rp.bdev = bdev;
	rp.cow = cow;
	rp.cache_size = cache_size;
	rp.ignore_snap_errors = ignore_snap_errors;

	ret = ioctl(fd, IOCTL_RELOAD_SNAP, &rp);

	close(fd);
	return ret;
}

int elastio_snap_reload_incremental(unsigned int minor, char *bdev, char *cow, unsigned long cache_size, bool ignore_snap_errors){
	int fd, ret;
	struct reload_params rp;

	fd = open("/dev/elastio-snap-ctl", O_RDONLY);
	if(fd < 0) return -1;

	rp.minor = minor;
	rp.bdev = bdev;
	rp.cow = cow;
	rp.cache_size = cache_size;
	rp.ignore_snap_errors = ignore_snap_errors;

	ret = ioctl(fd, IOCTL_RELOAD_INC, &rp);

	close(fd);
	return ret;
}

int elastio_snap_destroy(unsigned int minor){
	int fd, ret;

	fd = open("/dev/elastio-snap-ctl", O_RDONLY);
	if(fd < 0) return -1;

	ret = ioctl(fd, IOCTL_DESTROY, &minor);
	if (ret == 0) {
		char f_name[BUF_SIZE];

		snprintf(f_name, sizeof(f_name), "%s/reload_%d.sh", RELOAD_SCRIPT_PATH, minor);
		if (access(f_name, F_OK) == 0 && remove(f_name)) {
			ret = ENOENT;
		}
	}

	close(fd);
	return ret;
}

int elastio_snap_transition_incremental(unsigned int minor){
	int fd, ret;
	struct reload_script_params rp;

	if (elastio_snap_get_reload_params(minor, &rp))
		return ENOENT;

	fd = open("/dev/elastio-snap-ctl", O_RDONLY);
	if(fd < 0) return -1;


	ret = ioctl(fd, IOCTL_TRANSITION_INC, &minor);
	if (ret == 0) {
		if (elastio_snap_set_reload_params(minor, false, &rp))
			ret = ENOENT;
	}

	close(fd);
	return ret;
}

int elastio_snap_transition_snapshot(unsigned int minor, char *cow, unsigned long fallocated_space){
	int fd, ret;
	struct reload_script_params rp;
	struct transition_snap_params tp;

	tp.minor = minor;
	tp.cow = cow;
	tp.fallocated_space = fallocated_space;

	if (elastio_snap_get_reload_params(minor, &rp))
		return ENOENT;

	fd = open("/dev/elastio-snap-ctl", O_RDONLY);
	if(fd < 0) return -1;

	ret = ioctl(fd, IOCTL_TRANSITION_SNAP, &tp);
	if (ret == 0) {
		strcpy(rp.cow, cow);
		if (elastio_snap_set_reload_params(minor, true, &rp))
			ret = ENOENT;
	}

	close(fd);
	return ret;
}

int elastio_snap_reconfigure(unsigned int minor, unsigned long cache_size){
	int fd, ret;
	struct reconfigure_params rp;
	struct reload_script_params rsp;

	if (elastio_snap_get_reload_params(minor, &rsp))
		return ENOENT;

	fd = open("/dev/elastio-snap-ctl", O_RDONLY);
	if(fd < 0) return -1;

	rp.minor = minor;
	rp.cache_size = cache_size;

	ret = ioctl(fd, IOCTL_RECONFIGURE, &rp);
	if (ret == 0) {
		rsp.cache_size = cache_size;
		if (elastio_snap_set_reload_params(minor, rsp.snapshot, &rsp))
			ret = ENOENT;
	}

	close(fd);
	return ret;
}

int elastio_snap_info(unsigned int minor, struct elastio_snap_info *info){
	int fd, ret;

	if(!info){
		errno = EINVAL;
		return -1;
	}

	fd = open("/dev/elastio-snap-ctl", O_RDONLY);
	if(fd < 0) return -1;

	info->minor = minor;

	ret = ioctl(fd, IOCTL_ELASTIO_SNAP_INFO, info);

	close(fd);
	return ret;
}

int elastio_snap_get_free_minor(void){
	int fd, ret, minor;

	fd = open("/dev/elastio-snap-ctl", O_RDONLY);
	if(fd < 0) return -1;

	ret = ioctl(fd, IOCTL_GET_FREE, &minor);

	close(fd);

	if(!ret) return minor;
	return ret;
}
