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

'''manage loosely-coupled nested repositories
'''

import __builtin__
import inspect
import os
import re
import subprocess

from mercurial import cmdutil
from mercurial import commands
from mercurial import hg
from mercurial import pushkey
from mercurial import ui
from mercurial import util
from mercurial.i18n import _

def _checklocal(repo):
    if not repo.local():
        raise util.Abort(_('repository is not local'))

def _expandsubtrees(ui, subtrees):
    '''Expand subtree 'aliases.'

    Each string in subtrees that has a like-named config entry in the [trees]
    section is replaced by the right hand side of the config entry.'''
    l = []
    for subtree in subtrees:
        if '/' in subtree:
            l += [subtree]
        else:
            cfglist = ui.configlist('trees', subtree)
            if cfglist:
                l += _expandsubtrees(ui, cfglist)
            else:
                l += [subtree]
    return l

def _subtreelist(ui, repo, opts):
    l = opts.get('subtrees')
    if l:
        del opts['subtrees']
        return _expandsubtrees(ui, l)
    l = []
    try:
        for line in repo.opener('trees'):
            l += [line.rstrip('\r\n')]
    except:
        pass
    return l

def _subtreegen(ui, repo, opts):
    '''yields (repo, subtree) tuples'''
    l =  _subtreelist(ui, repo, opts)
    if l:
        for subtree in l:
            # Look for file://..., http://..., ssh://..., etc.
            if subtree.split(':', 2)[0] in hg.schemes:
                repo = hg.repository(ui, subtree)
            else:
                yield repo, subtree
        return
    if repo.capable('pushkey'):
        s = repo.listkeys('trees')
        i = 0
        n = len(s)
        while i < n:
            subtree = s[("%d" % i)]
            # Look for file://..., http://..., ssh://..., etc.
            if subtree.split(':', 2)[0] in hg.schemes:
                repo = hg.repository(ui, subtree)
            else:
                yield repo, subtree
            i += 1

def _docmd1(cmd, ui, repo, *args, **opts):
    '''Call cmd for repo and each configured/specified subtree.
    This is for commands which use one repo (e.g., tstatus).'''
    ui.status('[%s]:\n' % repo.root)
    trc = cmd(ui, repo, *args, **opts)
    rc = trc != None and trc or 0
    for subtree in _subtreelist(ui, repo, opts):
        ui.status('\n')
        lr = hg.repository(ui, repo.wjoin(subtree))
        trc = _docmd1(cmd, lr.ui, lr, *args, **opts)
        rc += trc != None and trc or 0
    return rc

def _docmd2(cmd, ui, repo, remote, adjust, **opts):
    '''Call cmd for repo and each configured/specified subtree.
    This is for commands which use two repos (e.g., tincoming, tpush).'''
    ui.status('[%s]:\n' % repo.root)
    trc = cmd(ui, repo, remote, **opts)
    rc = trc != None and trc or 0
    for subtree in _subtreelist(ui, repo, opts):
        ui.status('\n')
        lr = hg.repository(ui, repo.wjoin(subtree))
        remote2 = adjust and os.path.join(remote, subtree) or remote
        trc = _docmd2(cmd, lr.ui, lr, remote2, adjust, **opts)
        rc += trc != None and trc or 0
    return rc

def _makeparentdir(path):
    if path:
        pdir = os.path.split(path.rstrip(os.sep + '/'))[0]
        if pdir and not os.path.exists(pdir):
            os.makedirs(pdir)

def _origcmd(name):
    'Return the callable mercurial will invoke for the given command name.'
    return cmdutil.findcmd(name, commands.table)[1][0]

def _shortpaths(root, subtrees):
    l = []
    if subtrees:
        n = len(root) + 1
        if subtrees[0] == root:
            l = ['.']
        else:
            l = [subtrees[0][n:]]
        for subtree in subtrees[1:]:
            l += [subtree[n:]]
    return l

def _subtreejoin(repo, subtree):
    '''return a string (url or path) referring to subtree within repo'''
    if repo.local():
        return repo.wjoin(subtree)
    return repo.url().rstrip('/') + '/' + subtree

def _walk(ui, repo, opts):
    l = []
    for dirpath, subdirs, files in os.walk(repo.root, True):
        if '.hg' in subdirs:
            subdirs.remove('.hg')
            l += [dirpath]
    return sorted(l)

def _writeconfig(repo, subtrees):
    f = open(repo.join('trees'), 'w')
    try:
        if subtrees:
            f.write('\n'.join(subtrees) + '\n')
    finally:
        f.close()
    return 0

# ---------------- commands and associated recursion helpers -------------------

def clone(ui, source, dest=None, *subtreeargs, **opts):
    '''copy one or more existing repositories to create a tree'''
    if subtreeargs:
        s = __builtin__.list(subtreeargs)
        s.extend(opts.get('subtrees')) # Note:  extend does not return a value
        opts['subtrees'] = s

    ui.status('cloning %s\n' % source)
    _makeparentdir(dest)
    # Copied from mercurial/hg.py; need the returned dest repo.
    r = hg.clone(hg.remoteui(ui, opts), source, dest,
                 pull=opts.get('pull'),
                 stream=opts.get('uncompressed'),
                 rev=opts.get('rev'),
                 update=opts.get('updaterev') or not opts.get('noupdate'),
                 branch=opts.get('branch'))
    src = r[0]
    dst = r[1]
    ui.status(_('created %s\n') % dst.root)

    subtrees = []
    for src, subtree in _subtreegen(src.ui, src, opts):
        ui.status('\n')
        clone(ui, _subtreejoin(src, subtree), dst.wjoin(subtree), **opts)
        subtrees.append(subtree)
    _writeconfig(dst, subtrees)
    return 0

def _command(ui, repo, argv, stop, opts):
    ui.status('[%s]:\n' % repo.root)
    ui.flush()
    # Mercurial bug?  util.system() drops elements of argv after the first.
    # rc = util.system(argv, cwd=repo.root)
    rc = subprocess.call(argv, cwd=repo.root)
    if rc and stop:
        return rc
    for subtree in _subtreelist(ui, repo, opts):
        ui.status('\n')
        ui.flush()
        lr = hg.repository(ui, repo.wjoin(subtree))
        rc += _command(lr.ui, lr, argv, stop, opts)
        if rc and stop:
            return rc
    return rc

def command(ui, repo, cmd, *args, **opts):
    '''run a command in each repo in the tree.

    Change directory to the root of each repo and run the command.

    Note that mercurial normally parses all arguments that start with a dash,
    including those that follow the command name, which usually results in an
    error.  Prevent this by using '--' before the command or arguments, e.g.:

    hg tcommand -- ls -l
    '''

    _checklocal(repo)
    l = __builtin__.list((cmd,) + args)
    return _command(ui, repo, l, opts.get('stop'), opts)

def config(ui, repo, *subtrees, **opts):
    '''list or change the subtrees configuration

    One of four operations can be selected:  --list, --add, --del, or --set.
    If no operation is specified, --list is assumed.

    If the --walk option is used with --set, the filesystem rooted at
    REPO is scanned and the subtree configuration set to the discovered repos.
    '''

    _checklocal(repo)

    opadd = opts.get('add')
    opdel = opts.get('del')
    oplst = opts.get('list')
    opset = opts.get('set')
    cnt = opadd + opdel + oplst + opset
    if cnt > 1:
        raise util.Abort(_('at most one of --add, --del, --list or --set is ' +
                           'allowed'))
    if cnt == 0 or oplst:
        l = _subtreelist(ui, repo, opts)
        for subtree in l:
            ui.write(subtree + '\n')
        return 0
    if opadd and subtrees:
        l = _subtreelist(ui, repo, opts)
        for subtree in subtrees:
            if subtree in l:
                raise util.Abort(_('subtree %s already configured' % subtree))
            l += [subtree]
        return _writeconfig(repo, l)
    if opdel:
        all = opts.get('all')
        if all + bool(subtrees) != 1:
            raise util.Abort(_('use either --all or subtrees (but not both)'))
        if all:
            return _writeconfig(repo, [])
        l = _subtreelist(ui, repo, opts)
        for subtree in subtrees:
            if not subtree in l:
                raise util.Abort(_('no subtree %s' % subtree))
            l.remove(subtree)
        return _writeconfig(repo, l)
    if opset:
        walk = opts.get('walk')
        if walk + bool(subtrees) != 1:
            raise util.Abort(_('use either --walk or subtrees (but not both)'))
        l = subtrees
        if walk:
            l = _shortpaths(repo.root, _walk(ui, repo, {}))[1:]
        return _writeconfig(repo, l)

def incoming(ui, repo, remote="default", **opts):
    '''show new changesets found in source'''
    _checklocal(repo)
    adjust = remote and not ui.config('paths', remote)
    st = opts.get('subtrees')
    repocount = len(_list(ui, repo, st and {'subtrees': st} or {}))
    rc = _docmd2(_origcmd('incoming'), ui, repo, remote, adjust, **opts)
    # return 0 if any of the repos have incoming changes; 1 otherwise.
    return int(rc == repocount)

def _list(ui, repo, opts):
    l = [repo.root]
    for subtree in _subtreelist(ui, repo, opts):
        dir = repo.wjoin(subtree)
        if os.path.exists(dir):
            lr = hg.repository(ui, dir)
            l += _list(lr.ui, lr, opts)
        else:
            ui.warn('repo %s is missing subtree %s\n' % (repo.root, subtree))
    return l

def list(ui, repo, **opts):
    '''list the repo and configured subtrees, recursively

    The initial list of subtrees is obtained from the command line (if present)
    or from the repo configuration.

    If the --walk option is specified, search the filesystem for subtrees
    instead of using the command line or configuration item.

    If the --short option is specified, "short" paths are listed (relative to
    the top-level repo).'''

    _checklocal(repo)
    if opts.get('walk'):
        l = _walk(ui, repo, opts)
    else:
        l = _list(ui, repo, opts)
    if opts.get('short'):
        l = _shortpaths(repo.root, l)
    for subtree in l:
        ui.write(subtree + '\n')
    return 0

def outgoing(ui, repo, remote=None, **opts):
    '''show changesets not found in the destination'''
    _checklocal(repo)
    adjust = remote and not ui.config('paths', remote)
    st = opts.get('subtrees')
    repocount = len(_list(ui, repo, st and {'subtrees': st} or {}))
    rc = _docmd2(_origcmd('outgoing'), ui, repo, remote, adjust, **opts)
    # return 0 if any of the repos have outgoing changes; 1 otherwise.
    return int(rc == repocount)

def _paths(cmd, ui, repo, search=None, **opts):
    ui.status('[%s]:\n' % repo.root)
    cmd(ui, repo, search)
    for subtree in _subtreelist(ui, repo, opts):
        ui.status('\n')
        lr = hg.repository(ui, repo.wjoin(subtree))
        _paths(cmd, lr.ui, lr, search, **opts)
    return 0

def paths(ui, repo, search=None, **opts):
    '''show aliases for remote repositories'''
    _checklocal(repo)
    return _paths(_origcmd('paths'), ui, repo, search, **opts)

def pull(ui, repo, remote="default", **opts):
    '''pull changes from the specified source'''
    _checklocal(repo)
    adjust = remote and not ui.config('paths', remote)
    st = opts.get('subtrees')
    repocount = len(_list(ui, repo, st and {'subtrees': st} or {}))
    rc = _docmd2(_origcmd('pull'), ui, repo, remote, adjust, **opts)
    # Sadly, pull returns 1 if there was nothing to pull *or* if there are
    # unresolved files on update.  No way to distinguish between them.
    # return 0 if any subtree pulled successfully.
    return int(rc == repocount)

def push(ui, repo, remote=None, **opts):
    '''push changes to the specified destination'''
    _checklocal(repo)
    adjust = remote and not ui.config('paths', remote)
    st = opts.get('subtrees')
    repocount = len(_list(ui, repo, st and {'subtrees': st} or {}))
    rc = _docmd2(_origcmd('push'), ui, repo, remote, adjust, **opts)
    # return 0 if all pushes were successful; 1 if none of the repos had
    # anything to push.
    return int(rc == repocount)

def status(ui, repo, *args, **opts):
    '''show changed files in the working directory'''
    _checklocal(repo)
    return _docmd1(_origcmd('status'), ui, repo, *args, **opts)

def tag(ui, repo, name1, *names, **opts):
    '''add one or more tags for the current or given revision'''
    _checklocal(repo)
    return _docmd1(_origcmd('tag'), ui, repo, name1, *names, **opts)

def _update(cmd, ui, repo, node=None, rev=None, clean=False, date=None,
            check=False, **opts):
    ui.status('[%s]:\n' % repo.root)
    trc = cmd(ui, repo, node, rev, clean, date, check)
    rc = trc != None and trc or 0
    for subtree in _subtreelist(ui, repo, opts):
        ui.status('\n')
        lr = hg.repository(ui, repo.wjoin(subtree))
        trc = _update(cmd, lr.ui, lr, node, rev, clean, date, check, **opts)
        rc += trc != None and trc or 0
    return rc

def update(ui, repo, node=None, rev=None, clean=False, date=None, check=False,
           **opts):
    '''update working directory (or switch revisions)'''
    _checklocal(repo)
    rc = _update(_origcmd('update'), ui, repo, node, rev, clean, date, check,
                 **opts)
    return rc and 1 or 0

def version(ui, **opts):
    '''show version information'''
    ui.status('trees extension (version 0.7)\n')

def debugkeys(ui, src, **opts):
    repo = hg.repository(ui, src)
    print(repo.listkeys('trees'))

# ----------------------------- mercurial linkage ------------------------------

subtreesopt = [('', 'subtrees', [],
                _('path to subtree'),
                _('SUBTREE'))]

walkopt = [('w', 'walk', False,
            _('walk the filesystem to discover subtrees'))]

commandopts = [('', 'stop', False,
                _('stop if command returns non-zero'))
              ] + subtreesopt
listopts = [('s', 'short', False,
             _('list short paths (relative to repo root)'))
           ] + walkopt + subtreesopt
configopts = [('a', 'add', False,
               _('add the specified SUBTREEs to config')),
              ('',  'all', False,
               _('with --del, delete all subtrees from config')),
              ('d', 'del', False,
               _('delete the specified SUBTREEs from config')),
              ('l', 'list', False,
               _('list the configured subtrees')),
              ('s', 'set', False, _('set the subtree config to SUBTREEs'))
             ] + walkopt

def _newcte(origcmd, newfunc, extraopts = [], synopsis = None):
    '''generate a cmdtable entry based on that for origcmd'''
    cte = cmdutil.findcmd(origcmd, commands.table)[1]
    if (len(cte) > 2):
        return (newfunc, cte[1] + extraopts, synopsis or cte[2])
    return (newfunc, cte[1] + extraopts, synopsis)

def extsetup(ui = None):
    global cmdtable
    # The cmdtable is initialized here to pick up options added by other
    # extensions (e.g., rebase, bookmarks).
    #
    # Commands tagged with '^' are listed by 'hg help'.
    cmdtable = {
        '^tclone': _newcte('clone', clone, subtreesopt,
                           _('[OPTION]... SOURCE [DEST [SUBTREE]...]')),
        'tcommand': (command, commandopts, _('command [arg] ...')),
        'tconfig': (config, configopts, _('[OPTION]... [SUBTREE]...')),
        'tincoming': _newcte('incoming', incoming, subtreesopt),
        'toutgoing': _newcte('outgoing', outgoing, subtreesopt),
        'tlist': (list, listopts, _('[OPTION]...')),
        'tpaths': _newcte('paths', paths, subtreesopt),
        '^tpull': _newcte('pull', pull, subtreesopt),
        '^tpush': _newcte('push', push, subtreesopt),
        '^tstatus': _newcte('status', status, subtreesopt),
        '^tupdate': _newcte('update', update, subtreesopt),
        'ttag': _newcte('tag', tag, subtreesopt),
        'tversion': (version, [], ''),
        'tdebugkeys': (debugkeys, [], '')
    }

commands.norepo += ' tclone tversion tdebugkeys'

def _treeslistkeys(repo):
    # trees are ordered, so the keys are the non-negative integers.
    s = {}
    i = 0
    try:
        for line in repo.opener('trees'):
            s[("%d" % i)] = line.rstrip('\n\r')
            i += 1
        return s
    except:
        return {}

def reposetup(ui, repo):
    if r.capable('pushkey'):
        # Pushing keys is disabled; unclear whether/how it should work.
        pushkey.register('trees', lambda *x: False, _treeslistkeys)
