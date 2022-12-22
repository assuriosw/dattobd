// SPDX-License-Identifier: GPL-2.0-only

/*
 * Copyright (C) 2017 Datto Inc.
 * Additional contributions by Elastio Software, Inc are Copyright (C) 2020 Elastio Software Inc.
 */

// kernel_version >= 4.10

#include "includes.h"
MODULE_LICENSE("GPL");

static inline void dummy(void){
		int n = (int)REQ_OP_WRITE_ZEROES;
		(void)n;
}

