Enable the extension; the path to it should be in $EXTENSION_PY.

  $ { echo '[extensions]'; echo "trees=$EXTENSION_PY"; } >> $HGRCPATH
  $ { echo '[trees]'; echo 's135 = s1 s3 s5'; } >> $HGRCPATH

Create test repos.

  $ for r in rflat rflat/s1 rflat/s2 rflat/s3 rflat/s4 rflat/s5 rflat/s6 \
  > r1 r1/s1 'r1/s1/s1.1 with spaces' r1/s2 r1/s2/s2.1 r1/s2/s2.2 \
  > r1/s2/s2.2/s2.2.1
  > do
  >     hg init "$r"
  >     echo "$r" > "$r/x" && hg -R "$r" ci -qAm "$r"
  > done
  $ hg tconfig -R rflat --set --walk
  $ hg tconfig -R r1    --set s1 s2
  $ hg tconfig -R r1/s1 --set 's1.1 with spaces'
  $ hg tconfig -R r1/s2 --set --walk

  $ hg tclone -q r1 r2
  $ hg tclone -q r1 r3 s1 file:$TESTTMP/r2 s2
  $ hg tclone    r1 r4 s1 file:$TESTTMP/r3 s2
  cloning r1
  updating (to branch default|working directory) (re)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  created $TESTTMP/r4
  
  cloning $TESTTMP/r1/s1
  updating (to branch default|working directory) (re)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  created $TESTTMP/r4/s1
  
  cloning $TESTTMP/r1/s1/s1.1 with spaces
  updating (to branch default|working directory) (re)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  created $TESTTMP/r4/s1/s1.1 with spaces
  
  cloning $TESTTMP/r3/s2
  updating (to branch default|working directory) (re)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  created $TESTTMP/r4/s2
  
  cloning $TESTTMP/r3/s2/s2.1
  updating (to branch default|working directory) (re)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  created $TESTTMP/r4/s2/s2.1
  
  cloning $TESTTMP/r3/s2/s2.2
  updating (to branch default|working directory) (re)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  created $TESTTMP/r4/s2/s2.2
  
  cloning $TESTTMP/r3/s2/s2.2/s2.2.1
  updating (to branch default|working directory) (re)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  created $TESTTMP/r4/s2/s2.2/s2.2.1

List the configuration.

  $ hg tconfig -R rflat
  s1
  s2
  s3
  s4
  s5
  s6

  $ hg tconfig -R r1
  s1
  s2

  $ for r in r1 r2 r3 r4
  > do
  >     echo
  >     hg tlist -R $r
  >     hg tpaths -R $r
  > done
  
  $TESTTMP/r1
  $TESTTMP/r1/s1
  $TESTTMP/r1/s1/s1.1 with spaces
  $TESTTMP/r1/s2
  $TESTTMP/r1/s2/s2.1
  $TESTTMP/r1/s2/s2.2
  $TESTTMP/r1/s2/s2.2/s2.2.1
  [$TESTTMP/r1]:
  
  [$TESTTMP/r1/s1]:
  
  [$TESTTMP/r1/s1/s1.1 with spaces]:
  
  [$TESTTMP/r1/s2]:
  
  [$TESTTMP/r1/s2/s2.1]:
  
  [$TESTTMP/r1/s2/s2.2]:
  
  [$TESTTMP/r1/s2/s2.2/s2.2.1]:
  
  $TESTTMP/r2
  $TESTTMP/r2/s1
  $TESTTMP/r2/s1/s1.1 with spaces
  $TESTTMP/r2/s2
  $TESTTMP/r2/s2/s2.1
  $TESTTMP/r2/s2/s2.2
  $TESTTMP/r2/s2/s2.2/s2.2.1
  [$TESTTMP/r2]:
  default = $TESTTMP/r1
  
  [$TESTTMP/r2/s1]:
  default = $TESTTMP/r1/s1
  
  [$TESTTMP/r2/s1/s1.1 with spaces]:
  default = $TESTTMP/r1/s1/s1.1 with spaces
  
  [$TESTTMP/r2/s2]:
  default = $TESTTMP/r1/s2
  
  [$TESTTMP/r2/s2/s2.1]:
  default = $TESTTMP/r1/s2/s2.1
  
  [$TESTTMP/r2/s2/s2.2]:
  default = $TESTTMP/r1/s2/s2.2
  
  [$TESTTMP/r2/s2/s2.2/s2.2.1]:
  default = $TESTTMP/r1/s2/s2.2/s2.2.1
  
  $TESTTMP/r3
  $TESTTMP/r3/s1
  $TESTTMP/r3/s1/s1.1 with spaces
  $TESTTMP/r3/s2
  $TESTTMP/r3/s2/s2.1
  $TESTTMP/r3/s2/s2.2
  $TESTTMP/r3/s2/s2.2/s2.2.1
  [$TESTTMP/r3]:
  default = $TESTTMP/r1
  
  [$TESTTMP/r3/s1]:
  default = $TESTTMP/r1/s1
  
  [$TESTTMP/r3/s1/s1.1 with spaces]:
  default = $TESTTMP/r1/s1/s1.1 with spaces
  
  [$TESTTMP/r3/s2]:
  default = $TESTTMP/r2/s2
  
  [$TESTTMP/r3/s2/s2.1]:
  default = $TESTTMP/r2/s2/s2.1
  
  [$TESTTMP/r3/s2/s2.2]:
  default = $TESTTMP/r2/s2/s2.2
  
  [$TESTTMP/r3/s2/s2.2/s2.2.1]:
  default = $TESTTMP/r2/s2/s2.2/s2.2.1
  
  $TESTTMP/r4
  $TESTTMP/r4/s1
  $TESTTMP/r4/s1/s1.1 with spaces
  $TESTTMP/r4/s2
  $TESTTMP/r4/s2/s2.1
  $TESTTMP/r4/s2/s2.2
  $TESTTMP/r4/s2/s2.2/s2.2.1
  [$TESTTMP/r4]:
  default = $TESTTMP/r1
  
  [$TESTTMP/r4/s1]:
  default = $TESTTMP/r1/s1
  
  [$TESTTMP/r4/s1/s1.1 with spaces]:
  default = $TESTTMP/r1/s1/s1.1 with spaces
  
  [$TESTTMP/r4/s2]:
  default = $TESTTMP/r3/s2
  
  [$TESTTMP/r4/s2/s2.1]:
  default = $TESTTMP/r3/s2/s2.1
  
  [$TESTTMP/r4/s2/s2.2]:
  default = $TESTTMP/r3/s2/s2.2
  
  [$TESTTMP/r4/s2/s2.2/s2.2.1]:
  default = $TESTTMP/r3/s2/s2.2/s2.2.1

Test tconfig command.

  $ hg init r4/s3
  $ hg tconfig -R r4
  s1
  s2

  $ hg tconfig -R r4 -a s3
  $ hg tconfig -R r4
  s1
  s2
  s3
  $ hg tconfig -R r4 -a s3 # should fail
  abort: subtree s3 already configured
  [255]
  $ hg tconfig -R r4 -d s0 # should fail
  abort: no subtree s0
  [255]

  $ hg tconfig -R r4 -s s1 s2
  $ hg tconfig -R r4
  s1
  s2

  $ hg tconfig -R r4 -s
  abort: use either --walk or subtrees (but not both)
  [255]
  $ hg tconfig -R r4 -d --all
  $ hg tconfig -R r4

  $ hg tconfig -R r4 -s s1 s2 s3
  $ hg tconfig -R r4
  s1
  s2
  s3

  $ hg tconfig -R r4 -d s1
  $ hg tconfig -R r4
  s2
  s3

  $ hg tconfig -R r4 -s s1 s2
  $ hg tconfig -R r4
  s1
  s2

  $ hg tlist -R r4
  $TESTTMP/r4
  $TESTTMP/r4/s1
  $TESTTMP/r4/s1/s1.1 with spaces
  $TESTTMP/r4/s2
  $TESTTMP/r4/s2/s2.1
  $TESTTMP/r4/s2/s2.2
  $TESTTMP/r4/s2/s2.2/s2.2.1
  $ hg tlist -R r4 -w
  $TESTTMP/r4
  $TESTTMP/r4/s1
  $TESTTMP/r4/s1/s1.1 with spaces
  $TESTTMP/r4/s2
  $TESTTMP/r4/s2/s2.1
  $TESTTMP/r4/s2/s2.2
  $TESTTMP/r4/s2/s2.2/s2.2.1
  $TESTTMP/r4/s3
  $ rm -r r4/s3

Create changesets in r1 and r2.

  $ for r in r1 r2
  > do
  >     for sr in s2 s2/s2.2 s2/s2.2/s2.2.1
  >     do
  >         echo $sr > $r/$sr/file.$r
  >         hg -R $r/$sr add $r/$sr/file.$r
  >         hg -R $r/$sr ci -qm "$r/$sr/file.$r"
  >     done
  > done

Check incoming & outgoing

  $ hg -R r1 tin r2
  [$TESTTMP/r1]:
  comparing with r2
  searching for changes
  no changes found
  
  [$TESTTMP/r1/s1]:
  comparing with r2/s1
  searching for changes
  no changes found
  
  [$TESTTMP/r1/s1/s1.1 with spaces]:
  comparing with r2/s1/s1.1 with spaces
  searching for changes
  no changes found
  
  [$TESTTMP/r1/s2]:
  comparing with r2/s2
  searching for changes
  changeset:   1:02ac722f677c
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     r2/s2/file.r2
  
  
  [$TESTTMP/r1/s2/s2.1]:
  comparing with r2/s2/s2.1
  searching for changes
  no changes found
  
  [$TESTTMP/r1/s2/s2.2]:
  comparing with r2/s2/s2.2
  searching for changes
  changeset:   1:b9139c2dc588
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     r2/s2/s2.2/file.r2
  
  
  [$TESTTMP/r1/s2/s2.2/s2.2.1]:
  comparing with r2/s2/s2.2/s2.2.1
  searching for changes
  changeset:   1:c0662346bf9f
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     r2/s2/s2.2/s2.2.1/file.r2
  
  $ hg -R r2 tin
  [$TESTTMP/r2]:
  comparing with $TESTTMP/r1
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s1]:
  comparing with $TESTTMP/r1/s1
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s1/s1.1 with spaces]:
  comparing with $TESTTMP/r1/s1/s1.1 with spaces
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s2]:
  comparing with $TESTTMP/r1/s2
  searching for changes
  changeset:   1:e87282477f23
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     r1/s2/file.r1
  
  
  [$TESTTMP/r2/s2/s2.1]:
  comparing with $TESTTMP/r1/s2/s2.1
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s2/s2.2]:
  comparing with $TESTTMP/r1/s2/s2.2
  searching for changes
  changeset:   1:19c35aa89db4
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     r1/s2/s2.2/file.r1
  
  
  [$TESTTMP/r2/s2/s2.2/s2.2.1]:
  comparing with $TESTTMP/r1/s2/s2.2/s2.2.1
  searching for changes
  changeset:   1:0830ec9a3521
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     r1/s2/s2.2/s2.2.1/file.r1
  
  $ hg -R r1 tout r2
  [$TESTTMP/r1]:
  comparing with r2
  searching for changes
  no changes found
  
  [$TESTTMP/r1/s1]:
  comparing with r2/s1
  searching for changes
  no changes found
  
  [$TESTTMP/r1/s1/s1.1 with spaces]:
  comparing with r2/s1/s1.1 with spaces
  searching for changes
  no changes found
  
  [$TESTTMP/r1/s2]:
  comparing with r2/s2
  searching for changes
  changeset:   1:e87282477f23
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     r1/s2/file.r1
  
  
  [$TESTTMP/r1/s2/s2.1]:
  comparing with r2/s2/s2.1
  searching for changes
  no changes found
  
  [$TESTTMP/r1/s2/s2.2]:
  comparing with r2/s2/s2.2
  searching for changes
  changeset:   1:19c35aa89db4
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     r1/s2/s2.2/file.r1
  
  
  [$TESTTMP/r1/s2/s2.2/s2.2.1]:
  comparing with r2/s2/s2.2/s2.2.1
  searching for changes
  changeset:   1:0830ec9a3521
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     r1/s2/s2.2/s2.2.1/file.r1
  
  $ hg -R r2 tout
  [$TESTTMP/r2]:
  comparing with $TESTTMP/r1
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s1]:
  comparing with $TESTTMP/r1/s1
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s1/s1.1 with spaces]:
  comparing with $TESTTMP/r1/s1/s1.1 with spaces
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s2]:
  comparing with $TESTTMP/r1/s2
  searching for changes
  changeset:   1:02ac722f677c
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     r2/s2/file.r2
  
  
  [$TESTTMP/r2/s2/s2.1]:
  comparing with $TESTTMP/r1/s2/s2.1
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s2/s2.2]:
  comparing with $TESTTMP/r1/s2/s2.2
  searching for changes
  changeset:   1:b9139c2dc588
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     r2/s2/s2.2/file.r2
  
  
  [$TESTTMP/r2/s2/s2.2/s2.2.1]:
  comparing with $TESTTMP/r1/s2/s2.2/s2.2.1
  searching for changes
  changeset:   1:c0662346bf9f
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     r2/s2/s2.2/s2.2.1/file.r2
  

Pull, merge, push.

  $ hg -R r2 tpull
  [$TESTTMP/r2]:
  pulling from $TESTTMP/r1
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s1]:
  pulling from $TESTTMP/r1/s1
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s1/s1.1 with spaces]:
  pulling from $TESTTMP/r1/s1/s1.1 with spaces
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s2]:
  pulling from $TESTTMP/r1/s2
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  (run 'hg heads' to see heads, 'hg merge' to merge)
  
  [$TESTTMP/r2/s2/s2.1]:
  pulling from $TESTTMP/r1/s2/s2.1
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s2/s2.2]:
  pulling from $TESTTMP/r1/s2/s2.2
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  (run 'hg heads' to see heads, 'hg merge' to merge)
  
  [$TESTTMP/r2/s2/s2.2/s2.2.1]:
  pulling from $TESTTMP/r1/s2/s2.2/s2.2.1
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 1 changesets with 1 changes to 1 files (+1 heads)
  (run 'hg heads' to see heads, 'hg merge' to merge)
  $ for r in r2
  > do
  >     for sr in s2 s2/s2.2 s2/s2.2/s2.2.1
  >     do
  >         hg -R $r/$sr merge
  >         hg -R $r/$sr commit -m 'merge with r1'
  >     done
  > done
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  (branch merge, don't forget to commit)
  $ hg -R r2 tpush
  [$TESTTMP/r2]:
  pushing to $TESTTMP/r1
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s1]:
  pushing to $TESTTMP/r1/s1
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s1/s1.1 with spaces]:
  pushing to $TESTTMP/r1/s1/s1.1 with spaces
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s2]:
  pushing to $TESTTMP/r1/s2
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 1 changes to 1 files
  
  [$TESTTMP/r2/s2/s2.1]:
  pushing to $TESTTMP/r1/s2/s2.1
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s2/s2.2]:
  pushing to $TESTTMP/r1/s2/s2.2
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 1 changes to 1 files
  
  [$TESTTMP/r2/s2/s2.2/s2.2.1]:
  pushing to $TESTTMP/r1/s2/s2.2/s2.2.1
  searching for changes
  adding changesets
  adding manifests
  adding file changes
  added 2 changesets with 1 changes to 1 files

  $ for sr in s2 s2/s2.2 s2/s2.2/s2.2.1
  > do
  >     hg -R r1/$sr tip
  > done
  changeset:   3:3d0a1cb52bf2
  tag:         tip
  parent:      2:02ac722f677c
  parent:      1:e87282477f23
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     merge with r1
  
  changeset:   3:76fc250030c4
  tag:         tip
  parent:      2:b9139c2dc588
  parent:      1:19c35aa89db4
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     merge with r1
  
  changeset:   3:015d691fdafe
  tag:         tip
  parent:      2:c0662346bf9f
  parent:      1:0830ec9a3521
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     merge with r1
  
Run tin & tout again (should be nothing incoming) to check exit code.

  $ hg -R r2 tin
  [$TESTTMP/r2]:
  comparing with $TESTTMP/r1
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s1]:
  comparing with $TESTTMP/r1/s1
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s1/s1.1 with spaces]:
  comparing with $TESTTMP/r1/s1/s1.1 with spaces
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s2]:
  comparing with $TESTTMP/r1/s2
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s2/s2.1]:
  comparing with $TESTTMP/r1/s2/s2.1
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s2/s2.2]:
  comparing with $TESTTMP/r1/s2/s2.2
  searching for changes
  no changes found
  
  [$TESTTMP/r2/s2/s2.2/s2.2.1]:
  comparing with $TESTTMP/r1/s2/s2.2/s2.2.1
  searching for changes
  no changes found
  [1]
  $ hg -R r2 tout -q
  [1]

Test tree aliases.

  $ hg tclone rflat r135 s135
  cloning rflat
  updating (to branch default|working directory) (re)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  created $TESTTMP/r135
  
  cloning $TESTTMP/rflat/s1
  updating (to branch default|working directory) (re)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  created $TESTTMP/r135/s1
  
  cloning $TESTTMP/rflat/s3
  updating (to branch default|working directory) (re)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  created $TESTTMP/r135/s3
  
  cloning $TESTTMP/rflat/s5
  updating (to branch default|working directory) (re)
  1 files updated, 0 files merged, 0 files removed, 0 files unresolved
  created $TESTTMP/r135/s5
  $ hg tpaths -R r135
  [$TESTTMP/r135]:
  default = $TESTTMP/rflat
  
  [$TESTTMP/r135/s1]:
  default = $TESTTMP/rflat/s1
  
  [$TESTTMP/r135/s3]:
  default = $TESTTMP/rflat/s3
  
  [$TESTTMP/r135/s5]:
  default = $TESTTMP/rflat/s5

Test tcommand, tstatus, ttag, tupdate.

  $ hg tlist -R r135
  $TESTTMP/r135
  $TESTTMP/r135/s1
  $TESTTMP/r135/s3
  $TESTTMP/r135/s5
  $ hg tcomm -R r135 pwd
  [$TESTTMP/r135]:
  $TESTTMP/r135
  
  [$TESTTMP/r135/s1]:
  $TESTTMP/r135/s1
  
  [$TESTTMP/r135/s3]:
  $TESTTMP/r135/s3
  
  [$TESTTMP/r135/s5]:
  $TESTTMP/r135/s5
  $ hg tstat -R r135 -q
  $ hg tcomm -R r135 -q -- touch xyz
  $ hg tstat -R r135
  [$TESTTMP/r135]:
  ? xyz
  
  [$TESTTMP/r135/s1]:
  ? xyz
  
  [$TESTTMP/r135/s3]:
  ? xyz
  
  [$TESTTMP/r135/s5]:
  ? xyz
  $ hg tcomm -R r135 -q -- hg add xyz
  $ hg tstat -R r135
  [$TESTTMP/r135]:
  A xyz
  
  [$TESTTMP/r135/s1]:
  A xyz
  
  [$TESTTMP/r135/s3]:
  A xyz
  
  [$TESTTMP/r135/s5]:
  A xyz
  $ hg tcomm -R r135 -q -- hg commit -m 'add xyz'
  $ hg tstat -R r135 -q
  $ hg ttag  -R r135 -d '0 0' xyz
  [$TESTTMP/r135]:
  
  [$TESTTMP/r135/s1]:
  
  [$TESTTMP/r135/s3]:
  
  [$TESTTMP/r135/s5]:
  $ hg tcomm -R r135 -- hg log -l 2
  [$TESTTMP/r135]:
  changeset:   2:83290f94fb2b
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     Added tag xyz for changeset b0a2d2266db8
  
  changeset:   1:b0a2d2266db8
  tag:         xyz
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     add xyz
  
  
  [$TESTTMP/r135/s1]:
  changeset:   2:5e30e7223a0b
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     Added tag xyz for changeset f1afd954409a
  
  changeset:   1:f1afd954409a
  tag:         xyz
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     add xyz
  
  
  [$TESTTMP/r135/s3]:
  changeset:   2:8c6b313fb499
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     Added tag xyz for changeset e16257c3cacc
  
  changeset:   1:e16257c3cacc
  tag:         xyz
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     add xyz
  
  
  [$TESTTMP/r135/s5]:
  changeset:   2:c2c28aac7653
  tag:         tip
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     Added tag xyz for changeset add70ffe0e61
  
  changeset:   1:add70ffe0e61
  tag:         xyz
  user:        test
  date:        Thu Jan 01 00:00:00 1970 +0000
  summary:     add xyz
  
  $ hg tup   -R r135 null
  [$TESTTMP/r135]:
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  
  [$TESTTMP/r135/s1]:
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  
  [$TESTTMP/r135/s3]:
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  
  [$TESTTMP/r135/s5]:
  0 files updated, 0 files merged, 3 files removed, 0 files unresolved
  $ hg tup   -R r135
  [$TESTTMP/r135]:
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved
  
  [$TESTTMP/r135/s1]:
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved
  
  [$TESTTMP/r135/s3]:
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved
  
  [$TESTTMP/r135/s5]:
  3 files updated, 0 files merged, 0 files removed, 0 files unresolved

