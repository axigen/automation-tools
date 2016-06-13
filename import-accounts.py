#! /usr/bin/env python
"""
Imports accounts from a specified file, one account per line.
"""
"""
Copyright (c) since 2006, GECAD Technologies. All rights reserved.
For feedback and/or bugs in this script, please send an e-mail to:
  "AXIGEN Team" <team@axigen.com>
"""
_CVSID='$Id: import-accounts.py,v 1.7 2016/05/23 16:38:17 nini@qa1 Exp $'
if __name__=='__main__':
  import sys, os
  sys.path.append(os.path.join(sys.path[0],'lib'))
  sys.path.append('lib')
  sys.path.append('/opt/axigen/scripts/lib')
  try:
    import cli2
  except ImportError:
    print >>sys.stderr, 'ERROR: AXIGEN CLI Module could not be imported.'
    print >>sys.stderr, 'Please place cli.py in one of the following directories:'
    for x in sys.path:
      print >>sys.stderr, '-',x
    sys.exit(1)

# defaults
  CLIHOST='127.0.0.1'
  CLIPORT=7000
  CLIUSER='admin'
  CLIPASS=''

  PARAMS=['accounts-file']
  PARAMSV={'accounts-file': None}

  if len(sys.argv)<len(PARAMS)+1:
    sys.stderr.write('Usage: %s ' % sys.argv[0])
    for p in PARAMS:
      sys.stderr.write('<%s> ' % p)
    sys.stderr.write('[admin-passwd [cli-host[:port]]]')
    print >>sys.stderr
    sys.exit(255)
  for i in range(1, len(PARAMS)+1):
    PARAMSV[PARAMS[i-1]]=sys.argv[i]
  if len(sys.argv)>=len(PARAMS)+2:
    CLIPASS=sys.argv[len(PARAMS)+1]
  if len(sys.argv)>=len(PARAMS)+3:
    CLIHOST=sys.argv[len(PARAMS)+2]
  if ':' in CLIHOST:
    try:
      CLIPORT=int(CLIHOST.split(':')[1])
    except ValueError:
      print >>sys.stderr, 'Error: Non-numeric CLI port passed as parameter'
      sys.exit(1)
    CLIHOST=CLIHOST.split(':')[0]
  if not CLIPASS:
    import getpass
    while not CLIPASS:
      CLIPASS=getpass.getpass('Enter CLI Admin password:')
      if not CLIPASS:
        print >>sys.stderr, 'Empty passwords are not allowed!'

  if os.environ.has_key('CLIDEBUG'):
    if len(os.environ['CLIDEBUG'])>0:
      cli2.CLI.debug=1

  accounts=[]
  f=open(PARAMSV['accounts-file'], 'r')
  lines=f.readlines()
  f.close()
  for l in lines:
    l=l.strip()
    if len(l)==0:
      continue
    lpair=l.split("\t")
    if len(lpair)<2:
      print >>sys.stderr, "!! No password field found. Please TAB-delimit the password field on the same line as the account address"
      continue
    laddr=lpair[0]
    lpass=lpair[1]
    if laddr.count('@')!=1:
      print >>sys.stderr, '!! Invalid address format:', l
      continue
    accounts.append([laddr, lpass])
  c=cli2.CLI(CLIHOST, CLIPORT, CLIUSER, CLIPASS)
  for accpas in accounts:
    acct=accpas[0]
    passwd=accpas[1]
    name=acct.split('@')[0].lower()
    dom=acct.split('@')[1].lower()
    if not c.hasDomain(dom):
      print >>sys.stderr, '!! Domain does not exist for:', acct
      continue
    if name in c.getAccountsList(dom):
      print >>sys.stderr, '!! Account already exists:', acct
      continue
    try:
      c.addAccount(dom, name, passwd)
    except:
      print >>sys.stderr, '!! Failed to add account:', acct
      continue
    print 'Account added:', acct

