#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <linux/netlink.h>
#include <unistd.h>
#include <stdint.h>

#include "src/nl_debug.h"

int main(void)
{
	int sock_fd;
	struct sockaddr_nl user_sockaddr;
	struct nlmsghdr *nl_msghdr;
	struct msghdr msghdr;
	struct iovec iov;

	struct msg_header_t *msg;

	sock_fd = socket(PF_NETLINK, SOCK_RAW, NETLINK_USERSOCK);

	memset(&user_sockaddr, 0, sizeof(user_sockaddr));
	user_sockaddr.nl_family = AF_NETLINK;
	user_sockaddr.nl_pid = getpid();
	user_sockaddr.nl_groups = NL_MCAST_GROUP;

	int ret = bind(sock_fd, (struct sockaddr*)&user_sockaddr, sizeof(user_sockaddr));
	printf("ret=%d\n", ret);
	while (1) {
		nl_msghdr = (struct nlmsghdr*) malloc(NLMSG_SPACE(256));
		memset(nl_msghdr, 0, NLMSG_SPACE(256));

		iov.iov_base = (void*) nl_msghdr;
		iov.iov_len = NLMSG_SPACE(256);

		msghdr.msg_name = (void*) &user_sockaddr;
		msghdr.msg_namelen = sizeof(user_sockaddr);
		msghdr.msg_iov = &iov;
		msghdr.msg_iovlen = 1;

		recvmsg(sock_fd, &msghdr, 0);

		msg = (struct msg_header_t *)NLMSG_DATA(nl_msghdr);
		printf("Type: %d\n", msg->type);
		printf("Timestamp: %lld\n", msg->timestamp);
		printf("Bio ID: %lld\n", msg->params.id);
		printf("BIO size: %d\n", msg->params.size);
		printf("BIO sector: %d\n", msg->params.sector);
	}

	close(sock_fd);
	return 0;
}
