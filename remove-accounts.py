#! /usr/bin/env python
"""
Removes accounts from AXIGEN
"""
"""
Copyright (c) since 2006, GECAD Technologies. All rights reserved.
For feedback and/or bugs in this script, please send an e-mail to:
  "AXIGEN Team" <team@axigen.com>
"""
_CVSID='$Id: remove-accounts.py,v 1.3 2016/05/23 16:35:14 nini@qa1 Exp $'
if __name__=='__main__':
  import sys, os
  sys.path.append(os.path.join(sys.path[0],'lib'))
  sys.path.append('/opt/axigen/scripts/lib')
  try:
    import cli2
  except ImportError:
    print >>sys.stderr, 'ERROR: AXIGEN CLI Module could not be imported.'
    print >>sys.stderr, 'Please place cli2.py in one of the following directories:'
    for x in sys.path:
      print >>sys.stderr, '-',x
    sys.exit(1)

  # defaults
  CLIHOST='127.0.0.1'
  CLIPORT=7000
  CLIUSER='admin'
  CLIPASS=''

  args=sys.argv[1:]
  for arg in args:
    if arg[:6].startswith('cli://'):
      args.remove(arg)
      if not '@' in arg[6:]:
        print >>sys.stderr, "WARNING: Incorrect cli url specification. Using defaults"
        continue
      cliuserspec=arg[6:].split('@')[0]
      clihostspec=arg[6:].split('@')[1]
      if ':' in cliuserspec:
        CLIUSER=cliuserspec.split(':')[0]
        CLIPASS=cliuserspec.split(':')[1]
      else:
        CLIUSER=cliuserspec
      if ':' in clihostspec:
        CLIHOST=clihostspec.split(':')[0]
        CLIPORT=clihostspec.split(':')[1]

  if len(args)<1:
    print >>sys.stderr, "Usage: %s [cliURI] account1@domain1 [account2@domain2 [...]] " % sys.argv[0]
    print >>sys.stderr, "       cliURI - cli://[user[:password]]@host[:port]"
    sys.exit(1)
  if not CLIPASS:
    import getpass
    while not CLIPASS:
      CLIPASS=getpass.getpass('Enter CLI Admin password:')
      if not CLIPASS:
        print >>sys.stderr, 'Empty passwords are not allowed!'
  c=cli2.CLI(CLIHOST, int(CLIPORT), CLIUSER, CLIPASS)
  for email in args:
    if '@' not in email:
      print >>sys.stderr, "Incorrect e-mail format: %s" % email
      continue
    acc=email.split('@')[0]
    dom=email.split('@')[1]
    try:
      c.delAccount(dom, acc)
    except:
      print >>sys.stderr, "FAILED:", email
      continue
    print "OK:", email
