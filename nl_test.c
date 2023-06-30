#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <linux/netlink.h>
#include <unistd.h>
#include <stdint.h>

#include "src/nl_debug.h"

struct event_desc event_text_desc[] = {
		{ EVENT_DRIVER_INIT, TO_STR(EVENT_DRIVER_INIT) },
		{ EVENT_DRIVER_DEINIT, TO_STR(EVENT_DRIVER_DEINIT) },
		{ EVENT_TRACING_STARTED, TO_STR(EVENT_TRACING_STARTED) },
		{ EVENT_TRACING_FINISHED, TO_STR(EVENT_TRACING_FINISHED) },
		{ EVENT_BIO_INCOMING, TO_STR(EVENT_BIO_INCOMING) },
		{ EVENT_BIO_PASSTHROUGH, TO_STR(EVENT_BIO_PASSTHROUGH) },
		{ EVENT_BIO_SNAP, TO_STR(EVENT_BIO_SNAP) },
		{ EVENT_BIO_INC, TO_STR(EVENT_BIO_INC) },
		{ EVENT_BIO_CLONED, TO_STR(EVENT_BIO_CLONED) },
		{ EVENT_BIO_READ_COMPLETE, TO_STR(EVENT_BIO_READ_COMPLETE) },
		{ EVENT_BIO_QUEUED, TO_STR(EVENT_BIO_QUEUED) },
		{ EVENT_BIO_RELEASED, TO_STR(EVENT_BIO_RELEASED) },
		{ EVENT_BIO_HANDLE_WRITE, TO_STR(EVENT_BIO_HANDLE_WRITE) },
		{ EVENT_BIO_FREE, TO_STR(EVENT_BIO_FREE) },
		{ EVENT_COW_WRITE_MAPPING, TO_STR(EVENT_COW_WRITE_MAPPING) },
		{ EVENT_COW_WRITE_DATA, TO_STR(EVENT_COW_WRITE_DATA) },
		{ EVENT_DEBUG, TO_STR(EVENT_DEBUG) },
};

const char *event2str(enum msg_type_t type)
{
	int i;

	for (i = 0; i < EVENT_LAST; i++)
		if (event_text_desc[i].event == type)
			return event_text_desc[i].desc;

	return NULL;
}

int main(void)
{
	int sock_fd;
	struct sockaddr_nl user_sockaddr;

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

	while (1) {
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
		printf("[%llu] %24.24s [%2d] %32.32s(), line %d", msg->timestamp, event2str(msg->type), msg->type,  msg->source.func, msg->source.line);
		if (msg->params.id) {
			printf(", bio ID: %llx, sector: %llu, size: %d", msg->params.id, msg->params.sector, msg->params.size);
		}
		printf("\n");
		free(nl_msghdr);
	}

	close(sock_fd);
	return 0;
}
