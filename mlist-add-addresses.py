#! /usr/bin/env python
"""
Adds addresses from a a file (each line containing "email@address full name")
to a specific mailing list
"""
"""
Copyright (c) since 2006, GECAD Technologies. All rights reserved.
For feedback and/or bugs in this script, please send an e-mail to:
  "AXIGEN Team" <team@axigen.com>
"""
_CVSID='$Id: mlist-add-addresses.py,v 1.2 2016/05/23 17:00:47 nini@qa1 Exp $'
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

  PARAMS=['file', 'domain', 'mail-list']
  PARAMSV={'file': None, 'domain': None, 'mail-list': None}

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
  if not c.hasDomain(PARAMSV['domain']):
    print >>sys.stderr, 'ERROR: Domain does not exist in AXIGEN'
    sys.exit(1)
  f=open(PARAMSV['file'], 'r')
  c.goto_root_context()
  c.update_domain(PARAMSV['domain'])
  c.update_list(PARAMSV['mail-list'])
  for l in f:
    ls=l.strip()
    if len(ls)<1:
      continue
    ls=ls.split()
    email=ls[0]
    if len(ls)>1:
      name=' '.join(ls[1:])
    else:
      name='NULL-NAME'
      print >>sys.stderr, 'WARNING: address "%s" contains no name. Will assinging "NULL-NAME".' % email
    try:
      c.mlist_add_user(email, name)
    except:
      print >>sys.stderr, 'WARNING: Failed to add address "%s" to mailing list' % email
      continue
    c.done()
  c.commit()

