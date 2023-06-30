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
	uint64_t priv;
} __attribute__((packed));

struct code_info_t {
	char func[32];
	uint16_t line;
} __attribute__((packed));

struct msg_header_t {
	uint8_t type;
	uint64_t timestamp;
	struct params_t params;
	struct code_info_t source;
} __attribute__((packed));

int nl_send_event(enum msg_type_t type, const char *func, int line, struct params_t *params);
void netlink_release(void);
int netlink_init(void);

#define trace_event_bio(_type, _bio, _priv) 	\
{ 											\
	struct params_t params; 					\
											\
	if (_bio) { 								\
		params.id = (uint64_t) (_bio); 		\
		params.size = bio_size(_bio); 		\
		params.sector = bio_sector(_bio); 	\
	} 										\
											\
	params.priv = (_priv); 					\
	nl_send_event(_type, __func__, __LINE__, &params); \
}

#define trace_event_generic(_type, _priv) 	\
{ 											\
	struct params_t params; 					\
											\
	params.priv = (_priv); 					\
	nl_send_event(_type, __func__, __LINE__, &params); \
}
