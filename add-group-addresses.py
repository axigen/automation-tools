#! /usr/bin/env python
"""
Script that populates a group with a set of addresses found in a file given as
parameter, with an address on each line.

Copyright (c) since 2007, GECAD Technologies. All rights reserved.
For feedback and/or bugs in this script, please send an e-mail to:
  "AXIGEN Team" <team@axigen.com>
"""
_CVSID='$Id: add-group-addresses.py,v 1.2 2016/05/23 16:57:40 nini@qa1 Exp $'
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
  %s file=<addresses file> group=<group name> \\
    [host=<cli host>] [port=<cli port>] [pass=<admin password>] \\
    [debug=<debug level>]

  Where, each parameter is:
  file  - the filename containing each address to be added, per line
  group - the group in which those addresses will be added. If the group
          doesn't exist, it will be created automatically. The group name MUST
          be in format group@domain for the script to identify the group's
          domain name.
  host  - CLI host to connect to; default: localhost
  port  - CLI port to connect to; default: 7000
  pass  - if specified, will use this password, otherwise will ask for one
  debug - if set to 1 will display all the protocol communication over CLI
  """ % (sys.argv[0])

  #defaults
  addrFile=None
  groupName=None
  cliHost=None
  cliPort=None
  cliPass=None
  cliDebug=None

  for param in sys.argv[1:]:
    if param.startswith('file='):
      addrFile=param[5:]
      continue
    if param.startswith('group='):
      groupName=param[6:]
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
  if cliHost==None:
    cliHost="127.0.0.1"
  if cliPort==None:
    cliPort="7000"
  if not groupName:
    print >>sys.stderr, "ERROR: Group not specified"
    show_help()
    sys.exit(1)
  else:
    if len(groupName.split('@'))!=2:
      print >>sys.stderr, "ERROR: Invalid group name. It must be of group@domain form."
      sys.exit(1)
  if not cliPort.isdigit():
    print >>sys.stderr, "Port must be a number"
    sys.exit(1)
  cliPort=int(cliPort)
  try:
    fd=open(addrFile, 'r')
  except:
    print >>sys.stderr, "Could not open addresses file (%s), or none specified" % addrFile
    show_help()
    sys.exit(1)
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
  group=groupName.split('@')[0]
  domain=groupName.split('@')[1]
  try:
    c.update_domain(domain)
  except:
    print >>sys.stderr, "ERROR: Could not enter context for domain `%s`" % domain
    sys.exit(2)
  if group not in c.get_forwarders():
    print "Group `%s` does not exist in domain `%s`. Trying to create..." % (group, domain)
    try:
      c.add_forwarder(group)
      c.commit()
      print "Successfully created group `%s` in domain `%s`." % (group, domain)
    except:
      print >>sys.stderr, "ERROR: Could not add group `%s` in domain `%s`." % (group, domain)
      sys.exit(2)
  try:
    c.update_forwarder(group)
  except:
    print >>sys.stderr, "ERROR: Could not enter context for group `%s`" % group
    sys.exit(2)
  lineNo=0
  for line in fd:
    lineNo+=1
    addr=line.strip()
    if not addr:
      print >>sys.stderr, "Empty line at %s:%d" % (addrFile, lineNo)
      continue
    try:
      c.add_forwarder_address(addr)
      print ">> Address `%s` successfully added" % addr
    except:
      print >>sys.stderr, "ERROR: Address `%s` could not be added (%s:%d)" % (addr, addrFile, lineNo)
