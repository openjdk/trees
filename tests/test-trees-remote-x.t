Pushkey support is required to run this test.

  $ hg init x
  $ hg debugpushkey x Non-Existent-Namespace || exit 80

Skip the test unless TREES_REMOTE_URL is set.

  $ [ -n "$TREES_REMOTE_URL" ] || exit 80

If TREES_REMOTE_URL is set, a trees-enabled mercurial server should be
accessible at that url that serves the six repos that would be created by the
following commands:

r=tree-1
hg init $r; touch $r/x; hg -R $r commit -d '0 0' -Am $r
r=tree-1/sub-1
hg init $r; touch $r/x; hg -R $r commit -d '0 0' -Am $r
r=tree-1/sub-2
hg init $r; touch $r/x; hg -R $r commit -d '0 0' -Am $r

hg -R tree-1 tconfig --set sub-1 sub-2

r=tree-2
hg init $r; touch $r/x; hg -R $r commit -d '0 0' -Am $r
r=tree-2/sub-2
hg init $r; touch $r/x; hg -R $r commit -d '0 0' -Am $r
r=tree-2/sub-3
hg init $r; touch $r/x; hg -R $r commit -d '0 0' -Am $r

hg -R tree-2 tconfig --set sub-2 sub-3

Sample hgweb.config for the above repos (replace <dir> with your local path):

[paths]
/tree-1 = <dir>/tree-1
/tree-1/sub-1 = <dir>/tree-1/sub-1
/tree-1/sub-2 = <dir>/tree-1/sub-2
/tree-2 = <dir>/tree-2
/tree-2/sub-2 = <dir>/tree-2/sub-2
/tree-2/sub-3 = <dir>/tree-2/sub-3

Enable the extension; the path to it should be in $EXTENSION_PY.

  $ { echo '[extensions]'; echo "trees=$EXTENSION_PY"; } >> $HGRCPATH

Clone repos.

  $ hg tclone -U "$TREES_REMOTE_URL/tree-1"
  cloning */tree-1 (glob)
  destination directory: tree-1
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  created $TESTTMP/tree-1
  
  cloning */tree-1/sub-1 (glob)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  created $TESTTMP/tree-1/sub-1
  
  cloning */tree-1/sub-2 (glob)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  created $TESTTMP/tree-1/sub-2

  $ hg tclone -U "$TREES_REMOTE_URL/tree-1" t1 sub-1 \
  > "$TREES_REMOTE_URL/tree-2"
  cloning */tree-1 (glob)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  created $TESTTMP/t1
  
  cloning */tree-1/sub-1 (glob)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  created $TESTTMP/t1/sub-1
  
  cloning */tree-2/sub-2 (glob)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  created $TESTTMP/t1/sub-2
  
  cloning */tree-2/sub-3 (glob)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  created $TESTTMP/t1/sub-3

  $ hg tclone -U "$TREES_REMOTE_URL/tree-1" t2 \
  > "$TREES_REMOTE_URL/tree-2" sub-3
  cloning */tree-1 (glob)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  created $TESTTMP/t2
  
  cloning */tree-1/sub-1 (glob)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  created $TESTTMP/t2/sub-1
  
  cloning */tree-1/sub-2 (glob)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  created $TESTTMP/t2/sub-2
  
  cloning */tree-2/sub-3 (glob)
  requesting all changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files
  created $TESTTMP/t2/sub-3
