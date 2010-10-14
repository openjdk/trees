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

# Use $hg from the environment, if set.
HG		:= $(word 1,${hg} hg)

# Installation.
PREFIX		:= ${HG_INSTALL_BASE}/hg
SRC_D		:= .
TREES_PY	:= ${SRC_D}/trees.py
SRC_F		:= trees.py
GET_PY_VER	:= import sys; print ".".join(sys.version.split(".")[0:2])
PY_VER		:= $(shell python -c '${GET_PY_VER}')
DST_D		= ${PREFIX}/lib/python${PY_VER}/site-packages/hgext
DST_F		= $(addprefix ${DST_D}/,${SRC_F})

# Testing.
TEST_RESULTS	:= test-results
TR		:= ${TEST_RESULTS}
TEST_CMDS1	= list paths st up
TEST_CMDS2	= in out pull push
TESTS_1		:= $(foreach r,r1 r2 r3 r4,$(addprefix ${r}.,${TEST_CMDS1}))
TESTS_2		:= $(foreach r,r1 r2,$(addprefix ${r}.,${TEST_CMDS2}))
TESTS		= $(TESTS_1) $(TESTS_2) r4.config hs.paths

HGRC		:= ${TR}/hgrc
RUN_HG		:= HGRCPATH=${HGRC} ${HG}

QUIET		:= @

.PHONY:  all install test version ${TESTS} r1.cset r2.cset FORCE

all:
	${QUIET} echo '${MAKE} install [PREFIX=...]'
	${QUIET} echo '${MAKE} test [ARGS=...]'
	${QUIET} echo '${MAKE} ${TESTS_1} [ARGS=...]'
	${QUIET} echo '${MAKE} ${TESTS_2} [ARGS=...]'
	${QUIET} echo '${MAKE} r4.config hs.paths [ARGS=...]'

clean:
	rm -fr "${TR}" "${SRC_D}"/*.pyc

install:  ${DST_F}

# File still seen as out of date, even with cp -p.  Grrr.
${DST_D}/%: ${SRC_D}/%
	cp -p '$^' '$@' && touch '$@'

test:  ${TESTS}

version:
	${RUN_HG} version

${TR}:
	mkdir -p ${TR}

${HGRC}:  ${SRC_D}/tests/hgrc makefile
	${QUIET} [ -d '${TR}' ] || mkdir -p '${TR}'
	${QUIET} cp '$<' '$@'
	${QUIET} \
	{ \
	echo; \
	echo '[extensions]'; \
	echo 'trees = ${TREES_PY}'; \
	echo; \
	echo '[trees]'; \
	echo 's1s2 = s1 s2'; \
	echo 'hs-closed = src/closed test/closed'; \
	} >> '$@'

${TR}/r1:  ${HGRC}
	rm -fr '$@'
	${QUIET} echo creating '$@' ...
	${QUIET} \
	all=''; \
	for r in '$@' \
		'$@/s1' \
		'$@/s1/s1.1 with spaces' \
		'$@/s2' \
		'$@/s2/s2.1' \
		'$@/s2/s2.2' \
		'$@/s2/s2.2/s2.2.1'; \
	do \
		${RUN_HG} init "$$r" && \
		echo $$r > "$$r/x" && \
		${RUN_HG} -R "$$r" ci -qAm "$$r"; \
		if [ -n "$$all" ]; \
		then \
			all="$$all\n$${r:-.}"; \
		else \
			all="$${r:-.}"; \
		fi; \
	done; \
	root=`${RUN_HG} -R $@ root`; \
	echo "$$all" | sed 's!$@!'"$$root"'!' > '$@.list.ref'
	${QUIET} { \
		echo s1; echo s2; \
	} >> '$@'/.hg/trees
	${QUIET} { \
		echo 's1.1 with spaces'; \
	} >> '$@'/s1/.hg/trees
	${QUIET} { \
		echo s2.1; echo s2.2; echo s2.2/s2.2.1; \
	} >> '$@'/s2/.hg/trees

${TR}/r2:  ${TR}/r1 ${TREES_PY}
	rm -fr '$@'
	${RUN_HG} tclone ${ARGS} $< '$@'
	${QUIET} sed 's!$<!$@!' ${<}.list.ref > ${@}.list.ref
	${QUIET} cp -p ${<}.list.ref ${@}.paths.ref
	@ echo

${TR}/r3:  ${TR}/r1 ${TR}/r2 ${TREES_PY}
	rm -fr '$@'
	${RUN_HG} tclone $< '$@' s1 file:${TR}/r2 s2
	${QUIET} sed 's!$<!$@!' ${<}.list.ref > ${@}.list.ref
	${QUIET} sed 's!$</s2!${TR}/r2/s2!' ${<}.list.ref > ${@}.paths.ref
	@ echo

${TR}/r4:  ${TR}/r1 ${TR}/r2 ${TREES_PY}
	rm -fr '$@'
	${RUN_HG} tclone $< '$@' s1 file:${TR}/r2 s2
	${QUIET} sed 's!$<!$@!' ${<}.list.ref > ${@}.list.ref
	@ echo

%.up:	rev	= tip
r1.%:	rlocal	= '${TR}/r1'
r1.%:	rother	= '${TR}/r2'
r2.%:	rlocal	= '${TR}/r2'
r2.%:	rother	=
r3.%:	rlocal	= '${TR}/r3'
r4.%:	rlocal	= '${TR}/r4'

rx_treecmd	= t$(subst $(basename $@).,,$@)
rx_redirect	= 2>&1 | tee ${TR}/${@}.raw
rx_pathsfilt	= sed -n 's/default[ 	]*=[ 	]*//p' ${TR}/${@}.raw > ${TR}/${@}.out
rx_diff		= if [ -f ${TR}/${@}.ref ]; then diff -u ${TR}/${@}.ref ${TR}/${@}.out; fi

r1.cset: ${TR}/r1 FORCE
	${QUIET} for r in s2 s2/s2.2; \
	do \
		echo $$r >> ${rlocal}/$$r/w; \
		${RUN_HG} -R ${rlocal}/$$r ci -qAm "$@ $$r w"; \
		echo $$r >> ${rlocal}/$$r/x; \
		${RUN_HG} -R ${rlocal}/$$r ci -qAm "$@ $$r x"; \
	done

r2.cset: ${TR}/r2 FORCE
	${QUIET} for r in s1 s2/s2.1 s2/s2.2/s2.2.1; \
	do \
		echo $$r >> ${rlocal}/$$r/y; \
		${RUN_HG} -R ${rlocal}/$$r ci -qAm "$@ $$r y"; \
		echo $$r >> ${rlocal}/$$r/z; \
		${RUN_HG} -R ${rlocal}/$$r ci -qAm "$@ $$r z"; \
	done

${TESTS_1}:  ${TR}/r3 ${TR}/r4
	${RUN_HG} -R ${rlocal} ${rx_treecmd} ${ARGS} ${rev} ${rx_redirect}
	${QUIET} \
	case "$@" in \
	*.paths) ${rx_pathsfilt};; \
	*) mv ${TR}/${@}.raw ${TR}/${@}.out;; \
	esac
	${QUIET} ${rx_diff}
	@ echo

r4.config: ${TR}/r4
	rm -fr ${rlocal}/s3
	${RUN_HG} init ${rlocal}/s3

	cat ${rlocal}/.hg/trees
	${RUN_HG} tconfig -R ${rlocal}

	${RUN_HG} tconfig -R ${rlocal} -a s3
	if ${RUN_HG} tconfig -R ${rlocal} -a s3; then exit 1; fi
	cat ${rlocal}/.hg/trees
	${RUN_HG} tconfig -R ${rlocal}

	${RUN_HG} tconfig -R ${rlocal} -s s1 s2
	cat ${rlocal}/.hg/trees
	${RUN_HG} tconfig -R ${rlocal}

	${RUN_HG} tconfig -R ${rlocal} -s
	cat ${rlocal}/.hg/trees
	${RUN_HG} tconfig -R ${rlocal}

	${RUN_HG} tconfig -R ${rlocal} -s s1 s2 s3
	cat ${rlocal}/.hg/trees
	${RUN_HG} tconfig -R ${rlocal}

	${RUN_HG} tconfig -R ${rlocal} -d s1
	cat ${rlocal}/.hg/trees
	${RUN_HG} tconfig -R ${rlocal}

	${RUN_HG} tconfig -R ${rlocal} -sw
	cat ${rlocal}/.hg/trees
	${RUN_HG} tconfig -R ${rlocal}

r1.in r1.pull r2.out r2.push:  r2.cset
	${RUN_HG} -R ${rlocal} ${rx_treecmd} ${ARGS} ${rother}
r1.out r1.push r2.in r2.pull:  r1.cset
	${RUN_HG} -R ${rlocal} ${rx_treecmd} ${ARGS} ${rother}

# combine repos from different trees (http)
hs_url_o	= http://hg.openjdk.java.net/jdk7/hotspot
hs_url_c	= http://closedjdk.sfbay.sun.com/jdk7/hotspot
${TR}/hs:  ${HGRC} ${TREES_PY}
	rm -fr '$@'
	${RUN_HG} tclone '${hs_url_o}' '$@' pubs '${hs_url_c}-gc' hs-closed
	${QUIET} \
	for p in '${hs_url_o}' '${hs_url_o}'/pubs \
		'${hs_url_c}-gc/src/closed' '${hs_url_c}-gc/test/closed'; \
	do \
		echo "$$p"; \
	done > $@.paths.ref

	@ echo

hs.paths:  ${TR}/hs
	${RUN_HG} -R '$<' tpaths ${ARGS} ${rx_redirect}
	${QUIET} ${rx_pathsfilt}
	${QUIET} ${rx_diff}
