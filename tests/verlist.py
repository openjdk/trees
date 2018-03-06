#
# Copyright (c) 2014, 2018, Oracle and/or its affiliates. All rights reserved.
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

"""verlist extension, to list mercurial repository tags

List the tags in a mercurial repo, separated by spaces.  The tags can be
restricted to a specified range and certain "uninteresting" tags skipped.  The
intended use is to generate a list of mercurial versions that should be tested.

"""

from mercurial import cmdutil
from mercurial import context
from mercurial import ui
from mercurial.i18n import _

def splitrevspec(revspec):
    """revrange is a string, e.g., rev, rev:, rev1:rev2, :rev, :"""
    idx = revspec.find(':')
    if idx < 0:
        return revspec, revspec
    return revspec[:idx], revspec[idx+1:]

def tagslist(repo, beg_rev, end_rev):
    tags = repo.tagslist()
    i = 0
    while context.changectx(repo, tags[i][1]).rev() < beg_rev:
        i += 1
    j = len(tags) - 1
    while context.changectx(repo, tags[j][1]).rev() > end_rev:
        j -= 1
    return tags[i:j + 1]
        
def _verlist(repo, revspec):
    beg, end = splitrevspec(revspec)
    beg = beg and context.changectx(repo, beg).rev() or 0
    end = context.changectx(repo, end or 'tip').rev()
    return tagslist(repo, beg, end)

def _lastmicro(tlist):
    lastmicro = ''
    tags = [tlist[0]] # always include the first tag
    for tag in tlist[1:]:
        pos = tag.find('.')
        if pos > 0 and tag.find('.', pos + 1) > 0:
            lastmicro = tag
        else:
            if lastmicro:
                tags.append(lastmicro)
                lastmicro = ''
            tags.append(tag)
    if lastmicro:
        tags.append(lastmicro)
    return tags

cmdtable = { }
command = cmdutil.command(cmdtable)

@command('verlist',
         [('l', 'lastmicro', None,
           _('list only the last micro version in a minor version family'))],
         _('[rev_range] ...'))
def verlist(ui, repo, *pats, **opts):
    """List the tags in a repo, separated by spaces.

    If one or more rev_ranges are given, limit the tags to the specified ranges.
    By default, all tags are listed.

    The --lastmicro option causes only list the last micro version within a
    minor version family to be listed.  Given a repo with tags 1.0, 1.0.1,
    1.0.2, 1.0.3, and 1.1, 1.1.1, 1.1.2, --lastmicro would list the following
    tags:  1.0, 1.0.3, 1.1, 1.1.2.

    """

    tags = []
    for revspec in pats or [':']:
        tags += _verlist(repo, revspec)
    tags = [x[0] for x in tags] # Just the tag names

    # Skip release candidates, and tip
    tags = filter(lambda t: not t.endswith('-rc') and t != "tip", tags)

    if opts.get('lastmicro'):
        tags = _lastmicro(tags)
    ui.write(' '.join(tags))
    ui.write('\n')
