Pushkey support is required to run this test.

  $ hg init x
  $ hg debugpushkey x Non-Existent-Namespace || exit 80

Enable the extension; the path to it should be in $EXTENSION_PY.

  $ { echo '[extensions]'; echo "trees=$EXTENSION_PY"; } >> $HGRCPATH

Create test repos.

  $ for r in r1 'r1/s1 has a space' r1/s2 'r1/s3 has a space'
  > do
  >     hg init "$r"
  >     echo "$r" > "$r/x" && hg -R "$r" ci -qAm "$r"
  > done
  $ hg tconfig -R r1 --set --walk
  $ hg tconfig -R r1
  s1 has a space
  s2
  s3 has a space

Check remote tree config w/tdebugkeys--using tclone on an http repo would
require a real web server.

This requires mercurial w/pushkey support (1.6 and later).

  $ { echo '[extensions]'; echo "trees = $EXTENSION_PY"; } >> r1/.hg/hgrc
  $ hg -R r1 serve -p $HGPORT  -d --pid-file=r1.pid -E r1.log
  $ cat r1.pid >> $DAEMON_PIDS

  $ hg tdebugkeys http://localhost:$HGPORT/
  0: s1 has a space
  1: s2
  2: s3 has a space

Test splitting of --subtrees args and quoting.

This requires mercurial with quoted config item support (1.6 and later).

  $ hg tpaths -R r1 --subtrees '"s1 has a space" s2' --config trees.splitargs=0
  [$TESTTMP/r1]:
  
  abort: repository $TESTTMP/r1/"s1 has a space" s2 not found!
  [255]
  $ hg tpaths -R r1 --subtrees '"s1 has a space" s2' --config trees.splitargs=1
  [$TESTTMP/r1]:
  
  [$TESTTMP/r1/s1 has a space]:
  
  [$TESTTMP/r1/s2]:

