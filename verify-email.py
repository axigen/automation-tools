#! /usr/bin/env python
"""
Verifies if an e-mail address exists locally in AXIGEN

Copyright (c) since 2006, GECAD Technologies. All rights reserved.
For feedback and/or bugs in this script, please send an e-mail to:
  "AXIGEN Team" <team@axigen.com>
"""
_CVSID='$Id: verify-email.py,v 1.2 2016/10/04 17:06:29 nini@qa1 Exp $'
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

  PARAMS=['address']
  PARAMSV={'address': None}

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
  if os.environ.has_key('CLIDEBUG'):
    if len(os.environ['CLIDEBUG'])>0:
      cli2.CLI.debug=1

  if not CLIPASS:
    import getpass
    while not CLIPASS:
      CLIPASS=getpass.getpass('Enter CLI Admin password:')
      if not CLIPASS:
        print >>sys.stderr, 'Empty passwords are not allowed!'
  c=cli2.CLI(CLIHOST, CLIPORT, CLIUSER, CLIPASS)

  myaccount=PARAMSV['address'].split('@')[0]
  mydomain=PARAMSV['address'].split('@')[1]
  domainList=c.getDomainsList()
  domainContext=None
  accountContext=None
  for dom in domainList:
    c.goto_root_context()
    c.update_domain(dom)
    if mydomain!=dom:
      domAliases=c.get_aliases()
      for domalias in domAliases:
        if mydomain==domalias:
          domainContext='@%s[%s]' % (dom, domalias)
    else:
      domainContext='@%s' % dom
    if domainContext:
      break
  if not domainContext:
    print "NO[domain]"
    sys.exit(1)
  domFwds=c.get_forwarders()
  for fwd in domFwds:
    if fwd==myaccount:
      accountContext='fwd:%s' % fwd
      break
  if accountContext:
    print 'OK:', accountContext
    sys.exit(0)
  domAccounts=c.get_accounts()
  for acc in domAccounts:
    if c.context=='domain-account':
      c.back()
    c.update_account(acc)
    if acc==myaccount:
      accountContext='acct:%s' % acc
    accAliases=c.get_aliases()
    for accalias in accAliases:
      if myaccount==accalias:
        accountContext='acct:%s[%s]' % (acc, accalias)
    if accountContext:
      break
  if not accountContext:
    print 'NO'
    sys.exit(2)
  print 'OK:', accountContext, domainContext

