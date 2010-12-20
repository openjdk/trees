# 
# Copyright (c) 2010, Oracle and/or its affiliates. All rights reserved.
# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
# 
# This code is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 only, as
# published by the Free Software Foundation.
# 
# This code is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# version 2 for more details (a copy is included in the LICENSE file that
# accompanied this code).
# 
# You should have received a copy of the GNU General Public License version
# 2 along with this work; if not, write to the Free Software Foundation,
# Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA.
# 
# Please contact Oracle, 500 Oracle Parkway, Redwood Shores, CA 94065 USA
# or visit www.oracle.com if you need additional information or have any
# questions.
# 

PWD		:= $(shell pwd)
SRC_DIR		:= ${PWD}
DST_DIR		:= ${HOME}/.hgfiles

.PHONY:  all clean install

all:
	@ echo 'Try one of the following:'
	@ echo '${MAKE} install [DST_DIR=...]'
	@ echo '${MAKE} test             # run tests with the default hg'
	@ echo '${MAKE} test-hg-versions # run tests with multiple hg versions'

clean:
	rm -f "${SRC_DIR}"/*.pyc "${SRC_DIR}"/tests/*.t.err

install:  ${DST_DIR}/trees.py

${DST_DIR}/%:  ${SRC_DIR}/%
	cp -p '$^' '$@'

HGEXT_TEST	:= tests
EXTENSION_PY	:= ${SRC_DIR}/trees.py
HG_VERSIONS	:= 1.6:

-include ${HGEXT_TEST}/hgext-test.gmk

