#! /usr/bin/env python
"""
Script that searches for patterns in each account personal data. Search is
being done in the attribute names. For example, searching for businessAddress
will return all the accounts, because all of them contain this keyword as
attribute.

Copyright (c) since 2007, GECAD Technologies. All rights reserved.
For feedback and/or bugs in this script, please send an e-mail to:
  "AXIGEN Team" <team@axigen.com>
"""
_CVSID='$Id: search-details.py,v 1.3 2016/05/23 16:54:29 nini@qa1 Exp $'
if __name__=='__main__':
  import sys
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

  def show_help():
    print >>sys.stderr, """
Basic usage:
  %s pattern=<pattern-to-search-for> \\
    [host=<cli host>] [port=<cli port>] [pass=<admin password>] \\
    [debug=<debug level>]

  Where, each parameter is:
  pattern - the pattern to search for
  host    - CLI host to connect to; default: localhost
  port    - CLI port to connect to; default: 7000
  pass    - if specified, will use this password, otherwise will ask for one
  debug   - if set to 1 will display all the protocol communication over CLI
  """ % (sys.argv[0])

  #defaults
  pattern=None
  cliHost=None
  cliPort=None
  cliPass=None
  cliDebug=None

  for param in sys.argv[1:]:
    if param.startswith('pattern='):
      pattern=param[8:]
      continue
    if param.startswith('host='):
      cliHost=param[5:]
      continue
    if param.startswith('port='):
      cliPort=param[5:]
      continue
    if param.startswith('pass='):
      cliPass=param[5:]
      continue
    if param.startswith('debug='):
      cliDebug=param[6:]
      continue
  if not pattern:
    print >>sys.stderr, "ERROR: Missing pattern"
    show_help()
    sys.exit(1)
  if cliHost==None:
    cliHost="127.0.0.1"
  if cliPort==None:
    cliPort="7000"
  if not cliPort.isdigit():
    print >>sys.stderr, "Port must be a number"
    sys.exit(1)
  cliPort=int(cliPort)
  c=cli2.CLI(cliHost, cliPort)
  if not cliPass:
    import getpass
    while not cliPass:
      cliPass=getpass.getpass('Enter CLI Admin password: ')
      if not cliPass:
        print >>sys.stderr, 'Empty passwords are not allowed!'
  if cliDebug=="1":
    cli2.CLI.debug=1
  c.auth(cliPass, "admin")
  domains=c.get_domains()
  for domain in domains:
    try:
      c.update_domain(domain)
    except:
      print >>sys.stderr, "ERROR: Could not enter context for domain `%s`" % domain
      continue
    accounts=c.get_accounts()
    for account in accounts:
      try:
        c.update_account(account)
      except:
        print >>sys.stderr, "ERROR: Could not enter account context for: `%s@%s`" % (account, domain)
        continue
      cinfo=c.show_contactinfo()
      matches=[]
      for line in cinfo.split(cli2.CRLF)[2:-3]:
        if pattern.lower() in line.lower():
          matches.append(line)
      if len(matches)>0:
        for match in matches:
          print "%s@%s: %s" % (account, domain, match)
      c.back()
    c.back()
