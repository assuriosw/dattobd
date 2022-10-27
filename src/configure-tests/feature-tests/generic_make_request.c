// SPDX-License-Identifier: GPL-2.0-only

/*
 * Copyright (C) 2015 Datto Inc.
 * Additional contributions by Elastio Software, Inc are Copyright (C) 2020 Elastio Software Inc.
 */

// kernel_version < 5.9

#include "includes.h"
MODULE_LICENSE("GPL");

static inline void dummy(void){
	struct bio _bio = { 0 };
	generic_make_request(&_bio);
}
