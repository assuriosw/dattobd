// SPDX-License-Identifier: GPL-2.0-only

/*
 * Copyright (C) 2021 Elastio Software Inc.
 */

// 5.8 == kernel_version

#include "includes.h"
MODULE_LICENSE("GPL");

static inline void dummy(void){
	struct request_queue rq;
	struct bio b;
	blk_qc_t qc = blk_mq_make_request(&rq, &b);
	(void)qc;
}
