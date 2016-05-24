#! /usr/bin/env python
"""
Renames an account in AXIGEN
"""
"""
Copyright (c) since 2006, GECAD Technologies. All rights reserved.
For feedback and/or bugs in this script, please send an e-mail to:
  "AXIGEN Team" <team@axigen.com>
"""
_CVSID='$Id: rename-account.py,v 1.2 2016/05/23 16:48:56 nini@qa1 Exp $'
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

  if len(args)!=3:
    print >>sys.stderr, "Usage: %s [cliURI] <domain> <account> <new name>" % sys.argv[0]
    print >>sys.stderr, "       cliURI - cli://[user[:password]]@host[:port]"
    sys.exit(1)

  domain=args[0]
  account=args[1]
  newname=args[2]

  if not CLIPASS:
    import getpass
    while not CLIPASS:
      CLIPASS=getpass.getpass('Enter CLI Admin password:')
      if not CLIPASS:
        print >>sys.stderr, 'Empty passwords are not allowed!'
  c=cli2.CLI(CLIHOST, CLIPORT, CLIUSER, CLIPASS)
  if not c.hasDomain(domain):
    print >>sys.stderr, "ERROR: Domain '%s' does not exist in AXIGEN" % domain
    sys.exit(2)
  if not c.hasAccount(domain, account):
    print >>sys.stderr, "ERROR: Account '%s' does not exist in domain '%s'" % (account, domain)
    sys.exit(3)
  try:
    c.setAccountData(account, domain, {'name': newname})
  except:
    print >>sys.stderr, "ERROR: Could not rename '%s' as '%s'" % (account, newname)
    sys.exit(4)
  print "Successfully renamed '%s' as '%s'" % (account, newname)
