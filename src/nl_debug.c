#include "nl_debug.h"

struct sock *nl_sock = NULL;

static void nl_recv_msg(struct sk_buff *skb)
{
	// TODO
}

void nl_send_msg(void)
{
	struct nlmsghdr *nlsk_mh;
	char* msg = "hello kernel";

	struct sk_buff *skb = nlmsg_new(NLMSG_DEFAULT_SIZE, GFP_KERNEL);
	nlsk_mh = nlmsg_put(skb, 0, 0, NLMSG_DONE, strlen(msg), 0);
	NETLINK_CB(skb).portid = 0;
	NETLINK_CB(skb).dst_group = NL_MCAST_GROUP;
	strcpy(nlmsg_data(nlsk_mh), msg);

	nlmsg_multicast(nl_sock, skb, 0, NL_MCAST_GROUP, GFP_KERNEL);
}

void netlink_release(void)
{
	printk("netlink release\n");
	sock_release(nl_sock->sk_socket);
}

int netlink_init(void)
{
	struct netlink_kernel_cfg cfg = {
		.input = nl_recv_msg,
	};

	printk("netlink init\n");

	nl_sock = netlink_kernel_create(&init_net, NETLINK_USERSOCK, &cfg);
	if (!nl_sock) {
		printk("netlink: error creating socket\n");
		return -ENOTSUPP;
	}

	return 0;
}

