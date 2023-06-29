#ifdef KERNEL_MODULE
#include <net/sock.h>
#include <linux/netlink.h>
#include <linux/skbuff.h>
#endif

#include "kernel-config.h"
#include "elastio-snap.h"

#define NL_MCAST_GROUP 1

enum msg_type_t {
	EVENT_DRIVER_INIT,
	EVENT_DRIVER_DEINIT,
	EVENT_TRACING_STARTED,
	EVENT_TRACING_FINISHED,
	EVENT_BIO_INCOMING,
	EVENT_BIO_PASSTHROUGH,
	EVENT_BIO_SNAP,
	EVENT_BIO_INC,
	EVENT_BIO_CLONED,
	EVENT_BIO_READ_COMPLETE,
	EVENT_BIO_HANDLE_WRITE,
	EVENT_BIO_FREE,
	EVENT_COW_WRITE_MAPPING,
	EVENT_COW_WRITE_DATA,
	EVENT_DEBUG
};

struct params_t {
	uint64_t id;
	uint32_t size; // in sectors
	uint64_t sector;
};

struct msg_header_t {
	uint8_t type;
	uint64_t timestamp;
	struct params_t params;
} __attribute__((packed));

int nl_send_event(enum msg_type_t type, struct params_t *params);
void netlink_release(void);
int netlink_init(void);
