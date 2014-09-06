#
# Copyright (c) 2010, 2014, Oracle and/or its affiliates. All rights reserved.
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

"""manage loosely-coupled nested repositories

A 'tree' is simply a repository that may contain other repositories (or other
trees) nested within its working directory.  This extension provides commands
that operate on an entire tree, or on selected trees within it.

Each tree stores a list of the repositories contained within it in a
non-versioned file, .hg/trees.  The file lists the path to each contained tree,
relative to the root, one per line.  The file is created when a tree is cloned,
and can be modified using the tconfig command.  It is not updated when pushing
or pulling changesets (tpush, tpull).

The extension is usable on the client even if the hg server does not have the
trees extension enabled; it simply requires a bit more typing when cloning
repos.  Each repo in the tree maintains its own path information in .hg/hgrc, so
that repositories from different locations can be combined into a single tree.

The following example creates a tree called 'myproj' that includes four nested
repositories ('src', 'docs', 'images' and 'styles') with the last two coming
from a different server.  If the hg servers have the trees extension enabled::

    $ hg tclone http://abc/proj myproj
    $ hg tclone --skiproot http://xyz/pub myproj

If the hg servers do not have the trees extension enabled, then simply append
the desired contained repos (subtrees) to the command line::

    $ hg tclone http://abc/proj myproj src docs
    $ hg tclone --skiproot http://xyz/pub myproj images styles

The above is shorthand for five clone operations (three from the first command,
and two more from the second)::

    $ hg clone http://abc/proj       myproj
    $ hg clone http://abc/proj/src   myproj/src
    $ hg clone http://abc/proj/docs  myproj/docs
    $ hg clone http://xyz/pub/images myproj/images
    $ hg clone http://xyz/pub/styles myproj/styles

It also writes the tree configuration to myproj/.hg/trees.  Note that the same
tree can also be created with a single tclone::

    $ hg tclone http://abc/proj myproj src docs http://xyz/pub images styles

More examples::

Show the working directory status for each repo in the tree::

    $ hg tstatus

Pull upstream changes into each repo in the tree and update the working dir::

    $ hg tpull -u

Push local changes from each repo in the tree::

    $ hg tpush

List the tree configuration recursively::

    $ hg tlist
    /path/to/myproj
    /path/to/myproj/src
    /path/to/myproj/docs
    /path/to/myproj/images
    /path/to/myproj/styles

You can create abbreviations for tree lists by adding a [trees] section to your
hgrc file, e.g.::

    [trees]
    jdk-lt = jdk langtools
    ojdk-all = corba hotspot jaxp jaxws jdk-lt

which could be used like this:

    $ hg tclone http://hg.openjdk.java.net/jdk7/jdk7 myjdk7 ojdk-all

to create the myjdk7 tree which contains corba, hotspot, jaxp, jaxws, jdk and
langtools repos.

Show the working directory status, but only for the root repo plus the jdk and
langtools repos::

    $ hg tstatus --subtrees jdk-lt
"""

import __builtin__
import exceptions
import inspect
import os
import re
import subprocess

from mercurial import cmdutil
from mercurial import commands
from mercurial import extensions
from mercurial import hg
from mercurial import localrepo
from mercurial import pushkey
from mercurial import ui
from mercurial import util
from mercurial.i18n import _

testedwith = '''
1.1 1.1.2 1.2 1.2.1 1.3 1.3.1 1.4 1.4.3 1.5 1.5.4
1.6 1.6.4 1.7 1.7.5 1.8 1.8.4 1.9 1.9.3
2.0-rc 2.0 2.0.2 2.1-rc 2.1 2.1.2 2.2-rc 2.2 2.2.3
2.3-rc 2.3 2.3.2 2.4-rc 2.4 2.4.2 2.5-rc 2.5 2.5.4
2.6-rc 2.6 2.6.3 2.7-rc 2.7 2.7.2 2.8-rc 2.8 2.8.2
2.9-rc 2.9
'''

def _checklocal(repo):
    if not isinstance(repo, localrepo.localrepository):
        raise util.Abort(_('repository is not local'))

def _expandsubtrees(ui, subtrees):
    """Expand subtree aliases.

    Each string in subtrees that has a like-named config entry in the [trees]
    section is replaced by the right hand side of the config entry."""
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

def _nsnormalize(s):
    if s == 'trees' or s.startswith('trees.'):
        return s
    return 'trees.' + s

def _ns(ui, opts):
    return _nsnormalize(opts.get('tns') or
                        ui.config('trees', 'namespace', 'trees'))

_splitui = None

def _splitsubtrees(l):
    global _splitui
    res = []
    for s in l:
        if "'" in s or '"' in s:
            # Use ui.configlist() for quoted strings; requires hg 1.6 or later.
            if not _splitui:
                _splitui = ui.ui()
            _splitui.setconfig('x', 'x', s)
            res += _splitui.configlist('x', 'x')
        else:
            res += s.split()
    return res

def _subtreelist(ui, repo, opts):
    l = opts.get('subtrees')
    if l:
        del opts['subtrees']
        cansplit = ui.configbool('trees', 'splitargs', True)
        return _expandsubtrees(ui, cansplit and _splitsubtrees(l) or l)
    l = []
    try:
        keys = repo.listkeys(_ns(ui, opts))
        for i in xrange(0, len(keys)):
            l.append(keys[str(i)])
    except:
        pass
    return l

def hg_repo(ui, url, opts):
    parts = url.split(':', 2)
    if len(parts) == 1 or parts[0] == 'file':
        return hg.repository(ui, url)
    return hg.peer(ui, opts, url)

def _subtreegen_listkeys(ui, repo, opts, namespace):
    keys = repo.listkeys(namespace)
    for i in range(len(keys)):
        subtree = keys[("%d" % i)]
        yield repo, subtree

def _subtreegen(ui, repo, opts):
    """yields (repo, subtree) tuples"""
    l =  _subtreelist(ui, repo, opts)
    namespace = _ns(ui, opts)
    yielded = False
    if l:
        for subtree in l:
            # Look for file://..., http://..., ssh://..., etc.
            if subtree.split(':', 2)[0] in hg.schemes:
                if not yielded:
                    for r, st in _subtreegen_listkeys(ui, repo, opts, namespace):
                        yield r, st
                repo = hg_repo(ui, subtree, opts)
                yielded = False
            else:
                yielded = True
                yield repo, subtree
    if not yielded:
        for r, st in _subtreegen_listkeys(ui, repo, opts, namespace):
            yield r, st

def _docmd1(cmd, ui, repo, *args, **opts):
    """Call cmd for repo and each configured/specified subtree.

    This is for commands which operate on a single tree (e.g., tstatus,
    tupdate)."""

    ui.status('[%s]:\n' % repo.root)
    # XXX - should be done just once.
    cmdopts = dict(opts)
    for o in subtreesopts:
        if o[1] in cmdopts:
            del cmdopts[o[1]]
    trc = cmd(ui, repo, *args, **cmdopts)
    rc = trc != None and trc or 0
    for subtree in _subtreelist(ui, repo, opts):
        ui.status('\n')
        lr = hg.repository(ui, repo.wjoin(subtree))
        trc = _docmd1(cmd, lr.ui, lr, *args, **opts)
        rc += trc != None and trc or 0
    return rc

def _docmd2(cmd, ui, repo, remote, adjust, **opts):
    """Call cmd for repo and each configured/specified subtree.

    This is for commands which operate on two trees (e.g., tpull, tpush)."""

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
    """Return the callable mercurial will invoke for the given command name."""
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

def _stripfilescheme(url):
    if url.startswith('file:'):
        i = 5
        while url[i:i+1] == '//':
            i += 1
        url = url[i:]
    return url

def _subtreejoin(repo, subtree):
    """Return a string (url or path) referring to subtree within repo."""
    u = _stripfilescheme(repo.url()).rstrip('/')
    return u + '/' + subtree

def _walk(ui, repo, opts):
    l = []
    for dirpath, subdirs, files in os.walk(repo.root, True):
        if '.hg' in subdirs:
            subdirs.remove('.hg')
            l += [dirpath]
    return sorted(l)

def _readfile(path):
    f = None
    try:
        f = open(path, 'r')
        s = f.read()
        f.close()
        return s
    except:
        if f:
            f.close()
        return None

def _writeconfig(repo, namespace, subtrees, append = False):
    confpath = repo.join(namespace or 'trees')
    if subtrees:
        newconfig = '\n'.join(subtrees) + '\n'
        if append or newconfig != _readfile(confpath):
            f = open(confpath, append and 'a' or 'w')
            try:
                f.write(newconfig)
            finally:
                f.close()
    elif os.path.exists(confpath):
        os.remove(confpath)
    return 0

# ---------------- commands and associated recursion helpers -------------------

def _clonerepo(ui, source, dest, opts):
    _makeparentdir(dest)
    # Copied from mercurial/hg.py; need the returned dest repo.
    s, d = hg_clone(ui, opts, source, dest,
                    pull=opts.get('pull'),
                    stream=opts.get('uncompressed'),
                    rev=opts.get('rev'),
                    update=opts.get('updaterev') or not opts.get('noupdate'),
                    branch=opts.get('branch'))
    if isinstance(s, localrepo.localrepository) or isinstance(d.local(), bool):
        return (s, d)
    # peers; return the destination localrepo
    return (s, d.local())

def _skiprepo(ui, source, dest):
    src = None
    try:
        src = hg_repo(ui, source, {})
    except:
        class fakerepo(object):
            def __init__(self, ui, path):
                self.ui = ui
                self._path = path
            def peer(self):
                return self
            def local(self):
                return self._path
            def url(self):
                return self._path
            def wjoin(self, path):
                return os.path.join(self._path, path)
        src = fakerepo(ui, source)
    return (src, hg.repository(ui, dest))

def _clonesubtrees(ui, src, dst, opts):
    subtrees = []
    for src, subtree in _subtreegen(src.ui, src, opts):
        ui.status('\n')
        _clone(ui, _subtreejoin(src, subtree), dst.wjoin(subtree), opts)
        subtrees.append(subtree)
    return subtrees

def _clone(ui, source, dest, opts, skiproot = False):
    if not skiproot and not os.path.exists(os.path.join(dest, '.hg')):
        ui.status('cloning %s\n' % source)
        src, dst = _clonerepo(ui, source, dest, opts)
        ui.status(_('created %s\n') % dst.root)
    else:
        msg = 'skipping %s (destination exists)\n'
        if skiproot:
            msg = 'skipping root %s\n'
        ui.status(msg % source)
        src, dst = _skiprepo(ui, source, dest)
    subtrees = _clonesubtrees(ui, src, dst, opts)
    addconfig(ui, dst, subtrees, opts, True)

# Need to indirect through hg_clone for compatibility w/various hg versions.
hg_clone = None

def clone(ui, source, dest=None, *subtreeargs, **opts):
    '''copy one or more existing repositories to create a tree'''
    global hg_clone
    if not hg_clone:
        hg_clone = compatible_clone()
    if subtreeargs:
        s = __builtin__.list(subtreeargs)
        s.extend(opts.get('subtrees')) # Note:  extend does not return a value
        opts['subtrees'] = s
    if dest is None:
        dest = hg.defaultdest(source)
    _clone(ui, source, dest, opts, opts.get('skiproot'))
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
    """Run a command in each repo in the tree.

    Change directory to the root of each repo and run the command.

    The command is executed directly (i.e., not using a shell), so if i/o
    redirection or other shell features are desired, include the shell
    invocation in the command, e.g.:  hg tcommand -- sh -c 'ls -l > ls.out'

    Mercurial parses all arguments that start with a dash, including those that
    follow the command name, which usually results in an error.  Prevent this by
    using '--' before the command or arguments, e.g.:  hg tcommand -- ls -l"""

    _checklocal(repo)
    l = __builtin__.list((cmd,) + args)
    return _command(ui, repo, l, opts.get('stop'), opts)

def commit(ui, repo, *pats, **opts):
    """commit all files"""
    _checklocal(repo)
    if pats:
        util.Abort('must commit all files')

    hgcommit = _origcmd('commit')
    def condcommit(ui, repo, *pats, **opts):
        '''commit conditionally - only if there is something to commit'''
        needcommit = len(repo[None].parents()) > 1 # merge
        if not needcommit:
            mar = repo.status()[:3] # modified, added, removed
            needcommit = bool(mar[0] or mar[1] or mar[2])
        if needcommit:
            return hgcommit(ui, repo, *pats, **opts)
        ui.status('nothing to commit\n')
        return 0

    return _docmd1(condcommit, ui, repo, *pats, **opts)

def addconfig(ui, repo, subtrees, opts, ignoredups = False):
    modified = False
    l = _subtreelist(ui, repo, opts)
    for subtree in subtrees:
        if subtree in l:
            if not ignoredups:
                raise util.Abort(_('subtree %s already configured' % subtree))
        else:
            l += [subtree]
            modified = True
    if modified:
        return _writeconfig(repo, _ns(ui, opts), l)
    return 0

def delconfig(ui, repo, subtrees, opts):
    all = opts.get('all')
    if all and subtrees:
        raise util.Abort(_('use either --all or subtrees (but not both)'))
    if all:
        return _writeconfig(repo, _ns(ui, opts), [])
    l = _subtreelist(ui, repo, opts)
    for subtree in subtrees:
        if not subtree in l:
            raise util.Abort(_('no subtree %s' % subtree))
        l.remove(subtree)
    return _writeconfig(repo, _ns(ui, opts), l)

def expandconfig(ui, repo, args, opts):
    """show recursively-expanded trees config items

    Config items in the [trees] section can be defined in terms of other items;
    this command shows the expanded value.

    returns 0 if at least one config item was found; otherwise returns 1.
    """

    rc = 1
    for item in args:
        rhs = ui.configlist('trees', item)
        if rhs:
            rc = 0
            l = _expandsubtrees(ui, rhs)
            ui.write(' '.join(l))
            ui.write('\n')
    return rc

def _depthmostsplit(subtreemap, subtree):
    repo, sub = os.path.split(subtree)
    while repo:
        if repo in subtreemap:
            return repo, sub
        repo, sub2 = os.path.split(repo)
        sub = subtree[len(repo) + 1:]
    return '.', subtree

def nestconfig(ui, repo, subtrees, opts):
    newtrees = { }
    subtreemap = dict.fromkeys(subtrees)
    for sub in subtrees:
        nestedrepo, nestedsub = _depthmostsplit(subtreemap, sub)
        if nestedrepo in newtrees:
            nl = newtrees[nestedrepo]
            if nestedsub not in nl:
                nl.append(nestedsub)
        else:
            newtrees[nestedrepo] = [nestedsub]
    for sub in subtrees:
        nr = hg_repo(ui, _subtreejoin(repo, sub), {})
        _writeconfig(nr, _ns(ui, opts), newtrees.get(sub))
    return _writeconfig(repo, _ns(ui, opts), newtrees.get('.'))

# tconfig --set --depth example::
#
#   before         after
#   ------------   --------------------
#   $ hg tconfig   $ hg tconfig
#   sub1           sub1
#   sub1/sub1.1    sub2
#   sub2           $ hg -R sub1 tconfig
#   sub2/sub2.1    sub1.1
#   sub2/sub2.2    $ hg -R sub2 tconfig
#                  sub2.1
#                  sub2.2

def setconfig(ui, repo, subtrees, opts):
    walk = opts.get('walk')
    depth = opts.get('depth')
    if walk and subtrees:
        msg = _('subtrees cannot be specified when --walk is used')
        raise util.Abort(msg)
    elif not (subtrees or walk or depth):
        msg = _('specify subtrees, or use --walk and/or --depth')
        raise util.Abort(msg)

    if walk:
        subtrees = _shortpaths(repo.root, _walk(ui, repo, {}))[1:]
    elif not subtrees:
        subtrees = _shortpaths(repo.root, _list(ui, repo, opts))[1:]
    if depth:
        return nestconfig(ui, repo, subtrees, opts)
    return _writeconfig(repo, _ns(ui, opts), subtrees)

def config(ui, repo, *subtrees, **opts):
    """list or change the subtrees configuration

    One of five operations can be selected:

    --list:  list the configured subtrees; this is the default if no other
      operation is selected.

    --add:  add the specified subtrees to the configuration.

    --del:  delete the specified subtrees from the configuration.
      Use --del --all to delete all subtrees.

    --set:  set the subtree configuration to the specified subtrees.
      Use --set --walk to walk the filesystem rooted at REPO and set the
      subtree configuration to the discovered repos.  Use --depth
      to write the subtree configuration depth-most, so that each
      subtree is defined within the nearest enclosing repository.  Note
      that --walk and --depth may be used together.

    --expand:  list the value of config items from the [trees] section.
      Items in the [trees] section can be defined in terms of other
      items in the [trees] section; tconfig --expand shows the
      recursively expanded value.  It returns 0 if at least one config
      item was found; otherwise it returns 1.

    Note that with the slight exception of --set --depth, this command
    does not recurse into subtrees; it operates only on the current
    repository.  (To recursively list subtrees, use the tlist command.)

    """

    opadd = opts.get('add')
    opdel = opts.get('del')
    opexp = opts.get('expand')
    oplst = opts.get('list')
    opset = opts.get('set')
    cnt = opadd + opdel + opexp + oplst + opset
    if cnt > 1:
        raise util.Abort(_('at most one of --add, --del, --list, ' +
                           '--set or --expand is allowed'))
    if not opexp and not repo:
        raise util.Abort(_('no repository found'))
    if repo:
        _checklocal(repo)

    if opadd:
        return addconfig(ui, repo, subtrees, opts)
    if opdel:
        return delconfig(ui, repo, subtrees, opts)
    if opexp:
        return expandconfig(ui, repo, subtrees, opts)
    if opset:
        return setconfig(ui, repo, subtrees, opts)

    for subtree in _subtreelist(ui, repo, opts):
        ui.write(subtree + '\n')
    return 0

def diff(ui, repo, *args, **opts):
    """diff repository (or selected files)"""
    _checklocal(repo)
    return _docmd1(_origcmd('diff'), ui, repo, *args, **opts)

def heads(ui, repo, *branchrevs, **opts):
    """show current repository heads or show branch heads"""
    _checklocal(repo)
    st = opts.get('subtrees')
    repocount = len(_list(ui, repo, st and {'subtrees': st} or {}))
    rc = _docmd1(_origcmd('heads'), ui, repo, *branchrevs, **opts)
    # return 0 if any of the repos have matching heads; 1 otherwise.
    return int(rc == repocount)

def incoming(ui, repo, remote="default", **opts):
    """show new changesets found in source"""
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
    """list the repo and configured subtrees, recursively

    The initial list of subtrees is obtained from the command line (if present)
    or from the repo configuration.

    If the --walk option is specified, search the filesystem instead of using
    the command line or repo configuration.

    If the --short option is specified, the listed paths are relative to
    the top-level repo."""

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

def log(ui, repo, *args, **opts):
    '''show revision history of entire repository or files'''
    _checklocal(repo)
    return _docmd1(_origcmd('log'), ui, repo, *args, **opts)

def merge(ui, repo, node=None, **opts):
    '''merge working directory with another revision'''
    _checklocal(repo)

    hgmerge = _origcmd('merge')
    def condmerge(ui, repo, node=None, **opts):
        if len(repo.heads()) > 1:
            return hgmerge(ui, repo, node, **opts)
        ui.status('nothing to merge\n')
        return 0

    return _docmd1(condmerge, ui, repo, node, **opts)

def outgoing(ui, repo, remote=None, **opts):
    '''show changesets not found in the destination'''
    _checklocal(repo)
    adjust = remote and not ui.config('paths', remote)
    st = opts.get('subtrees')
    repocount = len(_list(ui, repo, st and {'subtrees': st} or {}))
    rc = _docmd2(_origcmd('outgoing'), ui, repo, remote, adjust, **opts)
    # return 0 if any of the repos have outgoing changes; 1 otherwise.
    return int(rc == repocount)

def parents(ui, repo, filename=None, **opts):
    _checklocal(repo)
    return _docmd1(_origcmd('parents'), ui, repo, filename, **opts)

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

def summary(ui, repo, **opts):
    """summarize working directory state"""
    _checklocal(repo)
    return _docmd1(_origcmd('summary'), ui, repo, **opts)

def tag(ui, repo, name1, *names, **opts):
    '''add one or more tags for the current or given revision'''
    _checklocal(repo)
    return _docmd1(_origcmd('tag'), ui, repo, name1, *names, **opts)

def tip(ui, repo, **opts):
    '''show the tip revision'''
    _checklocal(repo)
    return _docmd1(_origcmd('tip'), ui, repo, **opts)

def _update(cmd, ui, repo, node=None, rev=None, clean=False, date=None,
            check=False, **opts):
    ui.status('[%s]:\n' % repo.root)
    if _newupdate:
        trc = cmd(ui, repo, node, rev, clean, date, check)
    else:
        trc = cmd(ui, repo, node, rev, clean, date)
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

def defpath(ui, repo, peer=None, peer_push=None, **opts):
    '''examine and manipulate default path settings for a tree.'''
    def walker(r):
        return _list(ui, r, opts)
    return defpath_mod.defpath(ui, repo, peer, peer_push, walker, opts)

def debugkeys(ui, src, **opts):
    '''list the tree configuration using mercurial's pushkey mechanism.

    This works for remote repositories as long as the remote hg server has the
    trees extension enabled.'''
    d = hg_repo(ui, src, opts).listkeys(_ns(ui, opts))
    i = 0
    n = len(d)
    while i < n:
        istr = str(i)
        ui.write("%s: %s\n" % (istr, d[istr]))
        i += 1
    return 0

# ----------------------------- mercurial linkage ------------------------------

if not hasattr(hg, 'remoteui'):
    if hasattr(cmdutil, 'remoteui'):
        # hg < 1.5.4:  remoteui is in cmdutil instead of hg
        hg.remoteui = cmdutil.remoteui
    else:
        # hg < 1.3:  no remoteui
        def _remoteui(ui, opts):
            cmdutil.setremoteconfig(ui, opts)
            return ui
        hg.remoteui = _remoteui

# Tolerate changes to the signature of hg.clone().
def compatible_clone():
    clone_args = inspect.getargspec(hg.clone)[0]
    if not 'branch' in clone_args:
        # hg < 1.5:  no 'branch' parameter (a78bfaf988e1)
        def hg_clone(ui, peeropts, source, dest=None, pull=False, rev=None,
                     update=True, stream=False, branch=None):
            rui = hg.remoteui(ui, peeropts)
            return hg.clone(rui, source, dest, pull, rev, update, stream)
        return hg_clone
    if len(clone_args) < 9:
        # hg < 1.9:  no 'peeropts' parameter (d976542986d2, bd1acea552ff).
        def hg_clone(ui, peeropts, source, dest=None, pull=False, rev=None,
                     update=True, stream=False, branch=None):
            rui = hg.remoteui(ui, peeropts)
            return hg.clone(rui, source, dest, pull, rev, update, stream,
                            branch)
        return hg_clone
    return hg.clone

# hg < 2.3:  no peer() method
if getattr(hg, 'peer', None) is None:
    hg.peer = lambda ui, opts, url: hg.repository(ui, url)

_newupdate = len(inspect.getargspec(commands.update)[0]) >= 7
namespaceopt = [('', 'tns', '',
                 _('trees namespace to use'),
                 _('NAMESPACE'))]
subtreesopts = [('', 'subtrees', [],
                 _('path to subtree'),
                 _('SUBTREE'))] + namespaceopt

if len(commands.globalopts[0]) < 5:
    # hg < 1.5.4:  arg description (5th tuple element) is not supported
    def trimoptions(l):
        i = 0
        for opt in l:
            l[i] = opt[:4]
            i += 1
    trimoptions(namespaceopt)
    trimoptions(subtreesopts)

walkopt = [('w', 'walk', False,
            _('walk the filesystem to discover subtrees'))]

cloneopts = [('', 'skiproot', False,
              _('do not clone the root repo in the tree'))
            ] + subtreesopts
commandopts = [('', 'stop', False,
                _('stop if command returns non-zero'))
              ] + subtreesopts
listopts = [('s', 'short', False,
             _('list short paths (relative to repo root)'))
           ] + walkopt + subtreesopts
configopts = [('a', 'add', False,
               _('add the specified SUBTREEs to config')),
              ('',  'all', False,
               _('with --del, delete all subtrees from config')),
              ('d', 'del', False,
               _('delete the specified SUBTREEs from config')),
              ('e', 'expand', False,
               _('recursively expand config items in the [trees] section')),
              ('l', 'list', False,
               _('list the configured subtrees')),
              ('', 'depth', False,
               _('store subtree configuration depth-most')),
              ('s', 'set', False, _('set the subtree config to SUBTREEs'))
             ] + namespaceopt + walkopt

def _newcte(origcmd, newfunc, extraopts = [], synopsis = None):
    '''generate a cmdtable entry based on that for origcmd'''
    cte = cmdutil.findcmd(origcmd, commands.table)[1]
    # Filter out --exclude and --include, since those do not work across
    # repositories (mercurial converts them to abs paths).
    opts = [o for o in cte[1] if o[1] not in ('exclude', 'include')]
    if len(cte) > 2:
        return (newfunc, opts + extraopts, synopsis or cte[2])
    return (newfunc, opts + extraopts, synopsis)

def extsetup(ui = None):
    # The cmdtable is initialized here to pick up options added by other
    # extensions (e.g., rebase, bookmarks).
    #
    # Commands tagged with '^' are listed by 'hg help'.
    global defpath_mod
    defpath_mod = None
    defpath_opts = []
    try:
        defpath_mod = extensions.find('defpath')
        defpath_opts = __builtin__.list(defpath_mod.opts) + subtreesopts
        defpath_doc = getattr(defpath_mod, 'common_docstring', '')
        if defpath_doc:
            defpath.__doc__ += defpath_doc
    except:
        pass

    global cmdtable
    cmdtable = {
        '^tclone': _newcte('clone', clone, cloneopts,
                           _('[OPTION]... SOURCE [DEST [SUBTREE]...]')),
        'tcommand|tcmd': (command, commandopts, _('command [arg] ...')),
        'tcommit|tci': _newcte('commit', commit, subtreesopts),
        'tconfig': (config, configopts, _('[OPTION]... [SUBTREE]...')),
        'tdiff': _newcte('diff', diff, subtreesopts),
        'theads': _newcte('heads', heads, subtreesopts),
        'tincoming': _newcte('incoming', incoming, subtreesopts),
        'toutgoing': _newcte('outgoing', outgoing, subtreesopts),
        'tlist': (list, listopts, _('[OPTION]...')),
        '^tlog|thistory': _newcte('log', log, subtreesopts),
        'tmerge': _newcte('merge', merge, subtreesopts),
        'tparents': _newcte('parents', parents, subtreesopts),
        'tpaths': _newcte('paths', paths, subtreesopts),
        '^tpull': _newcte('pull', pull, subtreesopts),
        '^tpush': _newcte('push', push, subtreesopts),
        '^tstatus': _newcte('status', status, subtreesopts),
        '^tupdate': _newcte('update', update, subtreesopts),
        'ttag': _newcte('tag', tag, subtreesopts),
        'ttip': _newcte('tip', tip, subtreesopts),
        'tversion': (version, [], ''),
        'tdebugkeys': (debugkeys, namespaceopt, '')
    }
    if defpath_mod:
        cmdtable['tdefpath'] = (defpath, defpath_opts, _(''))
    if getattr(commands, 'summary', None):
        cmdtable['tsummary'] = _newcte('summary', summary, subtreesopts)

commands.norepo += ' tclone tversion tdebugkeys'
commands.optionalrepo += ' tconfig'

def genlistkeys(namespace):
    def _listkeys(repo):
        # trees are ordered, so the keys are the non-negative integers.
        d = {}
        i = 0
        try:
            for line in repo.opener(namespace):
                d[("%d" % i)] = line.rstrip('\n\r')
                i += 1
            return d
        except:
            return {}
    return _listkeys

def reposetup(ui, repo):
    # Pushing keys is disabled; unclear whether/how it should work.
    pushfunc = lambda *x: False
    x = [_nsnormalize(s) for s in ui.configlist('trees', 'namespaces', [])]
    try:
        for ns in [_ns(ui, {})] + x:
            pushkey.register(ns, pushfunc, genlistkeys(ns))
    except exceptions.ImportError:
        # hg < 1.6 - no pushkey.
        def _listkeys(self, namespace):
            # trees are ordered, so the keys are the non-negative integers.
            d = {}
            i = 0
            try:
                for line in self.opener(namespace):
                    d[("%d" % i)] = line.rstrip('\n\r')
                    i += 1
                return d
            except:
                return {}
        setattr(type(repo), 'listkeys', _listkeys)
