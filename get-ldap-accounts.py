#! /usr/bin/env python
"""
Queries a LDAP server for fetching a list of accounts and displaying them in a
specific format. Created and tested for Active Directory.
"""
"""
Copyright (c) since 2006, GECAD Technologies. All rights reserved.
For feedback and/or bugs in this script, please send an e-mail to:
  "AXIGEN Team" <team@axigen.com>
"""
_CVSID='$Id: get-ldap-accounts.py,v 1.3 2016/05/23 17:08:43 nini@qa1 Exp $'
if __name__=='__main__':
  import ldap, re, random, base64, sys, os

  #### CONFIG BEGIN - Please change the next lines accordingly
  ldapBindUser = "CN=administrator,cn=Users,DC=example,DC=local"
  ldapBindPass= "yourpassword"
  baseDN = "cn=Users,DC=example,DC=local"
  searchFilter = "(objectClass=user)"
  ldapHost="ldap.server.host"
  accountAttributeName="sAMAccountName"; # "sAMAccountName" for Active Directory
  specialAccounts=['Guest', 'krbtgt', 'ASPNET', 'MI_Viewer']; # Accounts to be excluded
  specialAccountsMask=['^SUPPORT_.*$', '^IUSR_.*$', '^IWAM_.*$']; # Accounts masks to be excluded
  #### CONFIG END

  def printEntry(entry):
    print "# %s" % dn
    for attr in entry:
      for k in range(len(entry[attr])):
        print attr+':', repr(entry[attr][k])
    print
    print

  domain=''
  generatePasswords=False
  if len(sys.argv)>1:
    for arg in sys.argv[1:]:
      if arg.lower().startswith('domain='):
        domain='@'+arg[7:]
      if arg.lower()=='-p':
        generatePasswords=True
      if arg.lower() in ['-h', '/?', '--help']:
        print "AXIGEN LDAP Query Helper"
        print "Usage: %s [-h|--help|/?] [domain=<domain>] [-p]" % os.path.basename(sys.argv[0])
        print "       -h | --help | /? -> print this help"
        print "       -p               -> print a tab delimited password field"
        print "                           (password is base64 encoded of a 16 character"
        print "                           random string)"
        print "       domain=<domain>  -> a @<domain> string will be appended to each"
        print "                           printed user"
        print "                           (useful for the import-accounts.py script)"
        sys.exit()

  l=ldap.open(ldapHost)
  l.simple_bind(ldapBindUser, ldapBindPass)
  searchScope = ldap.SCOPE_SUBTREE
  retrieveAttributes = None 
  ldap_result_id = l.search(baseDN, searchScope, searchFilter, retrieveAttributes)
  result_set = []
  while 1:
    result_type, result_data = l.result(ldap_result_id, 0)
    if (result_data == []):
      break
    else:
      if result_type == ldap.RES_SEARCH_ENTRY:
        result_set.append(result_data)
  for i in result_set:
    for j in i:
      dn=j[0]
      dbentry=j[1]; # dictionary
      acctName=dbentry[accountAttributeName][0]
      if acctName in specialAccounts:
        continue
      matched=False
      for sme in specialAccountsMask:
        m=re.compile(sme)
        if m.match(acctName):
          matched=True
          break
      if matched:
        continue
      p=''
      if generatePasswords:
        for k in range(16):
          p+=chr(random.randint(1,254))
        p='\t'+base64.encodestring(p)[:-1]
      print acctName+domain+p
