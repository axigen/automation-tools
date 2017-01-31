#! /usr/bin/env python
"""
Script that uses the CLI module to display all accounts within a domain, a list
of domains, or all domains.
"""
"""
Copyright (c) since 2007, Axigen Messaging. All rights reserved.
For feedback and/or bugs in this script, please send an e-mail to:
  "AXIGEN Team" <team@axigen.com>
"""
_VERID='$Id: list-accounts.py,v 1.7 2017/01/30 17:22:26 nini@qa1 Exp $'
if __name__=='__main__':
  import sys, os, time
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
  %s file=<accounts file> [host=<cli host>] \\
    [port=<cli port>] [debug=<debug level>] \\
    [pass=<admin password>] [domains=domain1[,domain2[,...]]]

  Where, each parameter is:
  file     - the filename to which the account names will saved, one per line
  host     - CLI host to connect to; default: localhost
  port     - CLI port to connect ro; default: 7000
  debug    - if set to 1 will display all the protocol communication over CLI
  pass     - if specified, will use this password, otherwise will ask for one
  domains  - specifies the domain or list of domains for which to query for accounts
  all      - if equal to 1 will enable retrieval for all available attributes
  names    - will also list the firstName and lastName account attributes
             default: 0 (true means anything other than 0)
  aliases  - will also list the aliases for each account
  info     - if equal to 1 will enable retrieval of attributes from the "SHOW" command as follows:
                ac   - Account Class
                at   - Account Type
                cr   - Customer Reference
  registry - if equal to 1 will enable retrieval of attributes from the "SHOW REGISTRYINFORMATION"
             command as follows:
                id   - Internal ID
                cd   - Creation Date
                md   - Modification Date
                plld - POP3 Last Login Date
                plli - POP3 Last Login IP
                illd - IMAP Last Login Date
                illi - IMAP Last Login IP
                wlld - WebMail Last Login Date
                wlli - WebMail Last Login IP
                alld - Active Sync Last Login Date
                alli - Active Sync Last Login IP
                olld - Outlook Connector Last Login Date
                olli - Outlook Connector Last Login IP
                lld  - Last Login Date
                imc  - Internal Mbox Container ID
                cv   - Configuration Version
                msv  - Mbox Storage Version
                ali  - Associated LDAP ID
                ald  - Associated LDAP DN
                cs   - Configuration Status
                ms   - Mbox Size
                msc  - Mbox message Count
                mfc  - Mbox Folder Count
                mss  - Mbox Storage Status
                msq  - Mbox Allocated Quota


  Examples of usage
  - save all accounts from all domains:
    %s file=myaccounts.txt host=192.168.102.24 port=7001

  - save Creation Date, Mbox size and IMAP Last Login Date:
    %s file=myaccounts.txt registry=1 cd=1 ms=1 illd=1

  - save accounts from example1.org and example2.org domains with first and
    last names:
    %s file=a1.txt domains=example1.org,example2.org names=1
  """ % (sys.argv[0], sys.argv[0], sys.argv[0], sys.argv[0])

  #defaults
  acctFile=None
  cliHost=None
  cliPort=None
  cliPass=None
  cliDebug=None
  domainsList=None

  listAll="0"

  listNames="0"
  listAliases="0"

  listInfo="0"
  listac="0"   # Account Class
  listat="0"   # Account Type
  listcr="0"   # Customer Reference

  listRegistry="0"
  listid="0"
  listcd="0"
  listmd="0"
  listplld="0"
  listplli="0" # POP3 Last Login IP
  listilld="0" # IMAP Last Login Date
  listilli="0" # IMAP Last Login IP
  listwlld="0" # WebMail Last Login Date
  listwlli="0" # WebMail Last Login IP
  listalld="0" # Active Sync Last Login Date
  listalli="0" # Active Sync Last Login IP
  listolld="0" # Outlook Conector Last Login Date
  listolli="0" # Outlook Connector Last Login IP
  listlld="0"  # Last Login Date
  listimc="0"  # Internal Mbox Container ID
  listcv="0"   # Configuration Version
  listmsv="0"  # Mbox Storage Version
  listali="0"  # Associated LDAP ID
  listald="0"  # Associated LDAP DN
  listcs="0"   # Configuration Status
  listms="0"   # Mbox Size
  listmsc="0"  # Mbox message Count
  listmfc="0"  # Mbox Folder Count
  listmss="0"  # Mbox Storage Status
  listmsq="0"  # Mbox Allocated Quota


  for param in sys.argv[1:]:
    if param.startswith('file='):
      acctFile=param[5:]
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
    if param.startswith('domains='):
      domainsList=param[8:]
      continue

    if param.startswith('all='):
      listAll=param[4:]
      continue

    if param.startswith('names='):
      listNames=param[6:]
      continue
    if param.startswith('aliases='):
      listAliases=param[8:]
      continue

    if param.startswith('info='):
      listInfo=param[5:]
      continue
    if param.startswith('ac='):
      listac=param[3:]
      continue
    if param.startswith('at='):
      listat=param[3:]
      continue
    if param.startswith('cr='):
      listcr=param[3:]
      continue

    if param.startswith('registry='):
      listRegistry=param[9:]
      continue
    if param.startswith('id='):
      listid=param[3:]
      continue
    if param.startswith('cd='):
      listcd=param[3:]
      continue
    if param.startswith('md='):
      listmd=param[3:]
      continue
    if param.startswith('plld='):
      listplld=param[5:]
      continue
    if param.startswith('plli='):
      listplli=param[5:]
      continue
    if param.startswith('illd='):
      listilld=param[5:]
      continue
    if param.startswith('illi='):
      listilli=param[5:]
      continue
    if param.startswith('wlld='):
      listwlld=param[5:]
      continue
    if param.startswith('wlli='):
      listwlli=param[5:]
      continue
    if param.startswith('alld='):
      listalld=param[5:]
      continue
    if param.startswith('alli='):
      listalli=param[5:]
      continue
    if param.startswith('olld='):
      listolld=param[5:]
      continue
    if param.startswith('olli='):
      listolli=param[5:]
      continue
    if param.startswith('lld='):
      listlld=param[4:]
      continue
    if param.startswith('imc='):
      listimc=param[4:]
      continue
    if param.startswith('cv='):
      listcv=param[3:]
      continue
    if param.startswith('msv='):
      listmsv=param[4:]
      continue
    if param.startswith('ali='):
      listali=param[4:]
      continue
    if param.startswith('ald='):
      listald=param[4:]
      continue
    if param.startswith('cs='):
      listcs=param[3:]
      continue
    if param.startswith('ms='):
      listms=param[3:]
      continue
    if param.startswith('msc='):
      listmsc=param[4:]
      continue
    if param.startswith('mfc='):
      listmfc=param[4:]
      continue
    if param.startswith('mss='):
      listmss=param[4:]
      continue
    if param.startswith('msq='):
      listmsq=param[4:]
      continue

  if listAll!="0":
    listAll=True
  else:
    listAll=False

  if listNames!="0":
    listNames=True
  else:
    listNames=False
  if listAliases!="0":
    listAliases=True
  else:
    listAliases=False

  if listInfo!="0":
    listInfo=True
  else:
    listInfo=False
  if listac!="0":
    listac=True
  else:
    listac=False
  if listat!="0":
    listat=True
  else:
    listat=False
  if listcr!="0":
    listcr=True
  else:
    listcr=False

  if listRegistry!="0":
    listRegistry=True
  else:
    listRegistry=False
  if listid!="0":
    listid=True
  else:
    listid=False
  if listcd!="0":
    listcd=True
  else:
    listcd=False
  if listmd!="0":
    listmd=True
  else:
    listmd=False
  if listplld!="0":
    listplld=True
  else:
    listplld=False
  if listplli!="0":
    listplli=True
  else:
    listplli=False
  if listilld!="0":
    listilld=True
  else:
    listilld=False
  if listilli!="0":
    listilli=True
  else:
    listilli=False
  if listwlld!="0":
    listwlld=True
  else:
    listwlld=False
  if listwlli!="0":
    listwlli=True
  else:
    listwlli=False
  if listalld!="0":
    listalld=True
  else:
    listalld=False
  if listalli!="0":
    listalli=True
  else:
    listalli=False
  if listolld!="0":
    listolld=True
  else:
    listolld=False
  if listolli!="0":
    listolli=True
  else:
    listolli=False
  if listlld!="0":
    listlld=True
  else:
    listlld=False
  if listimc!="0":
    listimc=True
  else:
    listimc=False
  if listcv!="0":
    listcv=True
  else:
    listcv=False
  if listmsv!="0":
    listmsv=True
  else:
    listmsv=False
  if listali!="0":
    listali=True
  else:
    listali=False
  if listald!="0":
    listald=True
  else:
    listald=False
  if listcs!="0":
    listcs=True
  else:
    listcs=False
  if listms!="0":
    listms=True
  else:
    listms=False
  if listmsc!="0":
    listmsc=True
  else:
    listmsc=False
  if listmfc!="0":
    listmfc=True
  else:
    listmfc=False
  if listmss!="0":
    listmss=True
  else:
    listmss=False
  if listmsq!="0":
    listmsq=True
  else:
    listmsq=False


  if cliHost==None:
    cliHost="127.0.0.1"
  if cliPort==None:
    cliPort="7000"
  if not cliPort.isdigit():
    print >>sys.stderr, "Port must be a number"
    sys.exit(1)
  cliPort=int(cliPort)
  if not acctFile:
    print >>sys.stderr, "Accounts file not specified"
    show_help()
    sys.exit(1)
  fd=open(acctFile, 'w')
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

  if not domainsList:
    myDomainsList=c.getDomainsList()
  else:
    myDomainsList=domainsList.split(',')
  for myDomain in myDomainsList:
    if not myDomain: # empty domain
      continue
    for myAccount in c.getAccountsList(myDomain):
      myAliasStr=''
      ac=''     # Account Class
      at=''     # Account Type
      cr=''     # Customer Reference
      id='';    # Internal ID
      cd='';    # Creation Date
      md='';    # Modification Date
      plld='';  # POP3 Last Login Date
      plli='';  # POP3 Last Login IP
      illd='';  # IMAP Last Login Date
      illi='';  # IMAP Last Login IP
      wlld='';  # WebMail Last Login Date
      wlli='';  # WebMail Last Login IP
      alld='';  # Active Sync Last Login Date
      alli='';  # Active Sync Last Login IP
      olld='';  # Outlook Connector Last Login Date
      olli='';  # Outlook Connector Last Login IP
      lld='';   # Last Login Date
      imc='';   # Internal Mbox Container ID
      cv='';    # Configuration Version
      msv='';   # Mbox Storage Version
      ali='';   # Associated LDAP ID
      ald='';   # Associated LDAP DN
      cs='';    # Configuration Status
      ms='';    # Mbox Size
      msc='';   # Mbox message count
      mfc='';   # Mbox Folder Count
      mss='';   # Mbox Storage Status
      msq='';   # Mbox Allocated Quota
      infoStr=''

      c.goto_root_context()
      c.update_domain(myDomain)
      c.update_account(myAccount)

      if listAliases or listAll:
        myAlias=c.getAccountAliases(myAccount, myDomain)
        myAliasStr='\t%s' % myAlias

      if listInfo or listAll:
        myInfo=c.get_show()
        if listac or listAll:
          ac='\n\tAccount Class: %s' % myInfo['accountClassName']
        if listat or listAll:
          at='\n\tAcccount Type: %s' % myInfo['accountType']
        if listcr or listAll:
          cr='\n\tCustomer Reference: %s' % myInfo['customerReference']

      if listRegistry or listAll:
        myRegistry=c.get_show_registry()
        if listid or listAll:
          id='\n\tInternal ID: %s' % myRegistry['Internal ID']
        if listcd or listAll:
          cd='\n\tCreation Date: %s' % myRegistry['Creation Date']
        if listmd or listAll:
          md='\n\tModification Date: %s' % myRegistry['Modification Date']
        if listplld or listAll:
          plld='\n\tPOP3 Last Login Date: %s' % myRegistry['POP3 Last Login Date']
        if listplli or listAll:
          plli='\n\tPOP3 Last Login IP: %s' % myRegistry['POP3 Last Login IP']
        if listilld or listAll:
          illd='\n\tIMAP Last Login Date: %s' % myRegistry['IMAP Last Login Date']
        if listilli or listAll:
          illi='\n\tIMAP Last Login IP: %s' % myRegistry['IMAP Last Login IP']
        if listwlld or listAll:
          wlld='\n\tWebMail Last Login Date: %s' % myRegistry['WebMail Last Login Date']
        if listwlli or listAll:
          wlli='\n\tWebMail Last Login IP: %s' % myRegistry['WebMail Last Login IP']

        if listalld or listAll:
          alld='\n\tActive Sync Last Login Date: %s' % myRegistry['Active Sync Last Login Date']
        if listalli or listAll:
          alli='\n\tActive Sync Last Login IP: %s' % myRegistry['Active Sync Last Login IP']
        if listolld or listAll:
          olld='\n\tOutlook Connector Last Login Date: %s' % myRegistry['OLK Last Login Date']
        if listolli or listAll:
          olli='\n\tOutlook Connector Last Login IP: %s' % myRegistry['OLK Last Login IP']

        if listlld or listAll:
          lldt = time.gmtime(0)
          for mykey in myRegistry:
            if mykey.find('Last Login Date') > 0:
              mydt = time.strptime(myRegistry[mykey].rsplit(' ',1)[0], '%a, %d %b %Y %H:%M:%S')
              if mydt > lldt:
                lldt = mydt
                lld = myRegistry[mykey]
          lld='\n\tLast Login Date: %s' % lld

        if listimc or listAll:
          imc='\n\tInternal Mbox Container ID: %s' % myRegistry['Internal Mbox Container ID']
        if listcv or listAll:
          cv='\n\tConfiguration Version: %s' % myRegistry['Configuration Version']
        if listmsv or listAll:
          msv='\n\tMbox Storage Version: %s' % myRegistry['Mbox Storage Version']
        if listali or listAll:
          ali='\n\tAssociated LDAP ID: %s' % myRegistry['Associated LDAP ID']
        if listald or listAll:
          ald='\n\tAssociated LDAP DN: %s' % myRegistry['Associated LDAP DN']
        if listcs or listAll:
          cs='\n\tConfiguration Status: %s' % myRegistry['Configuration Status']
        if listms or listAll:
          ms='\n\tMbox size: %s' % myRegistry['Mbox size']
        if listmsc or listAll:
          msc='\n\tMbox message count: %s' % myRegistry['Mbox message count']
        if listmfc or listAll:
          mfc='\n\tMbox folder count: %s' % myRegistry['Mbox folder count']
        if listmss or listAll:
          mss='\n\tMbox Storage Status: %s' % myRegistry['Mbox Storage Status']

      if listmsq or listAll:
          c.config('quotas')
          aquota_tms=c.get_show('totalMessageSize')
          c.back()
          mss='\n\tMbox Allocated Quota: %s Kb' % aquota_tms

      if listNames or listAll:
        c.config_contactinfo()
        myInfo=dict(c.get_show())
        infoStr='\t%s\t%s' % (myInfo['firstName'], myInfo['lastName'])

      print >>fd, "%s@%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s" % (myAccount, myDomain, infoStr, myAliasStr, ac, at, cr, id, cd, md, plld, plli, illd, illi, wlld, wlli, alld, alli, olld, olli, lld, imc, cv, msv, ali, ald, cs, ms, msc, mfc, mss)
  fd.close()
