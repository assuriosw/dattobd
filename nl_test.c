#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <linux/netlink.h>
#include <unistd.h>
#include <stdint.h>
#include <signal.h>

#include "src/nl_debug.h"

enum event_kind_t {
	KIND_EVENT_GENERIC,
	KIND_EVENT_BIO,
	KIND_EVENT_COW
};

struct event_desc {
	enum msg_type_t event;
	enum event_kind_t kind;
	const char *desc;
};

#define CNRM  "\x1B[0m"
#define CRED  "\x1B[31m"
#define CGRN  "\x1B[32m"
#define CYEL  "\x1B[33m"
#define CBLU  "\x1B[34m"
#define CMAG  "\x1B[35m"
#define CCYN  "\x1B[36m"
#define CWHT  "\x1B[37m"
#define CRESET "\033[0m"

struct event_desc event_text_desc[] = {
		{ EVENT_DRIVER_INIT, KIND_EVENT_GENERIC, TO_STR(EVENT_DRIVER_INIT) },
		{ EVENT_DRIVER_DEINIT, KIND_EVENT_GENERIC, TO_STR(EVENT_DRIVER_DEINIT) },
		{ EVENT_SETUP_SNAPSHOT, KIND_EVENT_GENERIC, TO_STR(EVENT_SETUP_SNAPSHOT) },
		{ EVENT_SETUP_UNVERIFIED_SNAP, KIND_EVENT_GENERIC, TO_STR(EVENT_SETUP_UNVERIFIED_SNAP) },
		{ EVENT_SETUP_UNVERIFIED_INC, KIND_EVENT_GENERIC, TO_STR(EVENT_SETUP_UNVERIFIED_INC) },
		{ EVENT_TRANSITION_INC, KIND_EVENT_GENERIC, TO_STR(EVENT_TRANSITION_INC) },
		{ EVENT_TRANSITION_SNAP, KIND_EVENT_GENERIC, TO_STR(EVENT_TRANSITION_SNAP) },
		{ EVENT_TRANSITION_DORMANT, KIND_EVENT_GENERIC, TO_STR(EVENT_TRANSITION_DORMANT) },
		{ EVENT_TRANSITION_ACTIVE, KIND_EVENT_GENERIC, TO_STR(EVENT_TRANSITION_ACTIVE) },
		{ EVENT_TRACING_STARTED, KIND_EVENT_GENERIC, TO_STR(EVENT_TRACING_STARTED) },
		{ EVENT_TRACING_FINISHED, KIND_EVENT_GENERIC, TO_STR(EVENT_TRACING_FINISHED) },
		{ EVENT_BIO_INCOMING, KIND_EVENT_BIO, TO_STR(EVENT_BIO_INCOMING) },
		{ EVENT_BIO_PASSTHROUGH, KIND_EVENT_BIO, TO_STR(EVENT_BIO_PASSTHROUGH) },
		{ EVENT_BIO_SNAP, KIND_EVENT_BIO, TO_STR(EVENT_BIO_SNAP) },
		{ EVENT_BIO_INC, KIND_EVENT_BIO, TO_STR(EVENT_BIO_INC) },
		{ EVENT_BIO_CLONED, KIND_EVENT_BIO, TO_STR(EVENT_BIO_CLONED) },
		{ EVENT_BIO_READ_COMPLETE, KIND_EVENT_BIO, TO_STR(EVENT_BIO_READ_COMPLETE) },
		{ EVENT_BIO_QUEUED, KIND_EVENT_BIO, TO_STR(EVENT_BIO_QUEUED) },
		{ EVENT_BIO_RELEASED, KIND_EVENT_BIO, TO_STR(EVENT_BIO_RELEASED) },
		{ EVENT_BIO_HANDLE_WRITE, KIND_EVENT_BIO, TO_STR(EVENT_BIO_HANDLE_WRITE) },
		{ EVENT_BIO_FREE, KIND_EVENT_BIO, TO_STR(EVENT_BIO_FREE) },
		{ EVENT_COW_READ_MAPPING, KIND_EVENT_COW, TO_STR(EVENT_COW_READ_MAPPING) },
		{ EVENT_COW_WRITE_MAPPING, KIND_EVENT_COW, TO_STR(EVENT_COW_WRITE_MAPPING) },
		{ EVENT_COW_READ_DATA, KIND_EVENT_COW, TO_STR(EVENT_COW_READ_DATA) },
		{ EVENT_COW_WRITE_DATA, KIND_EVENT_COW, TO_STR(EVENT_COW_WRITE_DATA) }
};

int sock_fd;

static void int_handler(int val) {
	printf(CRESET "\n");
	close(sock_fd);
	exit(0);
}

static const char *event2str(enum msg_type_t type)
{
	int i;

	for (i = 0; i < EVENT_LAST; i++)
		if (event_text_desc[i].event == type)
			return event_text_desc[i].desc;

	return NULL;
}

static bool is_generic_event(enum msg_type_t type)
{
	int i;

	for (i = 0; i < EVENT_LAST; i++)
		if (event_text_desc[i].event == type) {
			return event_text_desc[i].kind == KIND_EVENT_GENERIC;
		}

	return false;
}

static bool is_bio_event(enum msg_type_t type)
{
	int i;

	for (i = 0; i < EVENT_LAST; i++)
		if (event_text_desc[i].event == type)
			return event_text_desc[i].kind == KIND_EVENT_BIO;

	return false;
}

static bool is_cow_event(enum msg_type_t type)
{
	int i;

	for (i = 0; i < EVENT_LAST; i++)
		if (event_text_desc[i].event == type)
			return event_text_desc[i].kind == KIND_EVENT_COW;

	return false;
}

int main(void)
{
	struct sockaddr_nl user_sockaddr;

	signal(SIGINT, int_handler);

	sock_fd = socket(PF_NETLINK, SOCK_RAW, NETLINK_USERSOCK);

	memset(&user_sockaddr, 0, sizeof(user_sockaddr));
	user_sockaddr.nl_family = AF_NETLINK;
	user_sockaddr.nl_groups = NL_MCAST_GROUP;
	user_sockaddr.nl_pid = getpid();

	int ret = bind(sock_fd, (struct sockaddr*)&user_sockaddr, sizeof(user_sockaddr));
	if (ret) {
		perror("Couldn't bind the socket");
		return -1;
	}

	while (true) {
		struct iovec iov;
		struct msghdr msghdr;
		struct nlmsghdr *nl_msghdr;

		nl_msghdr = (struct nlmsghdr *) malloc(NLMSG_SPACE(256));
		memset(nl_msghdr, 0, NLMSG_SPACE(256));

		iov.iov_base = (void*) nl_msghdr;
		iov.iov_len = NLMSG_SPACE(256);

		msghdr.msg_name = (void*) &user_sockaddr;
		msghdr.msg_namelen = sizeof(user_sockaddr);
		msghdr.msg_iov = &iov;
		msghdr.msg_iovlen = 1;

		recvmsg(sock_fd, &msghdr, 0);

		struct msg_header_t *msg = (struct msg_header_t *)NLMSG_DATA(nl_msghdr);

		if (is_generic_event(msg->type))
			printf(CYEL);
		else if (is_bio_event(msg->type))
			printf(CCYN);
		else if (is_cow_event(msg->type))
			printf(CMAG);

		printf("[%llu] %24.24s [%2d] ", msg->timestamp, event2str(msg->type), msg->type);
		printf("%32.32s(), line %4d", msg->source.func, msg->source.line);

		if (msg->params.id) {
			printf(", bio ID: %16llx, sector: %16llu, size: %10d", msg->params.id, msg->params.sector, msg->params.size);
		}

		printf(", priv1: %10llu, priv2: %10llu", msg->params.priv1, msg->params.priv2);
		printf(CRESET "\n");
		free(nl_msghdr);
	}

	return 0;
}
