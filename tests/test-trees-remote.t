Enable the extension; the path to it should be in $EXTENSION_PY.

  $ { echo '[extensions]'; echo "trees=$EXTENSION_PY"; } >> $HGRCPATH
  $ { echo '[trees]'; echo 'subt = corba jaxp'; } >> $HGRCPATH

Filter the output from clone for compatibility with various mercurial versions.

  $ filt() { grep -v '^requesting all changes'; }

Clone with aliases.

  $ hg tclone -r 0 -U http://hg.openjdk.java.net/jdk7/jdk7 jdkx subt | filt
  cloning http://hg.openjdk.java.net/jdk7/jdk7
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 25 changes to 25 files
  created $TESTTMP/jdkx
  
  cloning http://hg.openjdk.java.net/jdk7/jdk7/corba
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1368 changes to 1368 files
  created $TESTTMP/jdkx/corba
  
  cloning http://hg.openjdk.java.net/jdk7/jdk7/jaxp
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1972 changes to 1972 files
  created $TESTTMP/jdkx/jaxp

  $ hg tpaths -R jdkx
  [$TESTTMP/jdkx]:
  default = http://hg.openjdk.java.net/jdk7/jdk7
  
  [$TESTTMP/jdkx/corba]:
  default = http://hg.openjdk.java.net/jdk7/jdk7/corba
  
  [$TESTTMP/jdkx/jaxp]:
  default = http://hg.openjdk.java.net/jdk7/jdk7/jaxp

  $ rm -fr jdkx

Clone combining separate trees.

  $ hg tclone -r 0 -U http://hg.openjdk.java.net/jdk7/jdk7 jdkx corba \
  > http://hg.openjdk.java.net/jdk7/hotspot jaxp | filt
  cloning http://hg.openjdk.java.net/jdk7/jdk7
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 25 changes to 25 files
  created $TESTTMP/jdkx
  
  cloning http://hg.openjdk.java.net/jdk7/jdk7/corba
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1368 changes to 1368 files
  created $TESTTMP/jdkx/corba
  
  cloning http://hg.openjdk.java.net/jdk7/hotspot/jaxp
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1972 changes to 1972 files
  created $TESTTMP/jdkx/jaxp

  $ hg tpaths -R jdkx
  [$TESTTMP/jdkx]:
  default = http://hg.openjdk.java.net/jdk7/jdk7
  
  [$TESTTMP/jdkx/corba]:
  default = http://hg.openjdk.java.net/jdk7/jdk7/corba
  
  [$TESTTMP/jdkx/jaxp]:
  default = http://hg.openjdk.java.net/jdk7/hotspot/jaxp
