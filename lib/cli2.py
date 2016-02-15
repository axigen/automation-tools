#! /usr/bin/env python
"""
AXIGEN CLI Control Module

This module implements the base CLI class to be able to transparently access
  AXIGEN's CLI commands via methods, along with some useful methods to process
  the data returned by the standard CLI class commands.

In order to be able to use this module, please copy it either into the same
  directory as the script that imports it, or in a directory from
  sys.path/PYTHONPATH.
"""
"""
IMPORTANT: This Python module is still in beta. However, it has been tested, at
  least with the example scripts found on http://www.axigen.com/. Please use it
  with caution.

Copyright (c) since 2006, GECAD Technologies. All rights reserved.
Please send any bugs and/or feedback related to this class to:
  AXIGEN Team <team@axigen.com>
"""
CVSID='$Id: cli2.py,v 1.26 2016/02/12 15:08:17 nini Exp $'
__version__=CVSID.split()[2]
__all__=['CLI', 'strtime2epoch']

import socket
from sys import stdout as STDOUT
from sys import stdin as STDIN
import re
import os

CRLF='\r\n'


#####################################################
###               Base Classes                    ###
#####################################################

class CLIException(Exception):
  """Base class for all AXIGEN CLI Exceptions"""

class CLIErrorException(CLIException):
  """Generic exceptions class for AXIGEN CLI"""
  def __init__(self, text):
    self.args=[text]

class CLIBase:
  """
  AXIGEN CLI base class
  This class defines methods for (almost) all AXIGEN CLI's commands.
  """
  debug=0
  context=None
  contexts=[]
  prompt=None
  V={
    'version': None,
    'fullversion': None,
    'platform': None,
    'os': None,
    'datadir': None
  }
  __c=re.compile('(((\+OK)|(-ERR)):.*)\r\n\<([A-Za-z0-9\-]*#?)\> ')
  __noauth=True

  def __init__(self, host='localhost', port=7000, user=None, passwd=None):
    """
    Initialize a new CLI class instance.

    The class constructor creates a socket based on the 'host' and 'port'
    parameters and, optionally, authenticates as the 'admin' user with a
    specified password by calling the auth() method
    """
    self.host=host
    self.port=port
    self.sock=None
    self.user=user
    self.passwd=passwd
    try:
      self.sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.sock.connect((host, port))
    except socket.error:
      if self.sock:
        self.sock=None
      self.sock=None
    if not self.sock:
      raise socket.error, "Connect error"
    self.__get()
    self.get_version_info()
    if user!=None and passwd!=None:
      self.auth(passwd,user)

  def __del__(self):
    """
    Class instance destructor.
    Closes the connection, if opened
    """
    if self.sock:
      self.sock.close()

  def __log(self, s):
    """
    Private method for logging the output of the socket communication to stdout
    """
    STDOUT.write(s.replace('\r\n', '\\r\\n\n'))
    STDOUT.flush()

  def __get(self):
    """
    Private method used by the response() method
    """
    respl=''
    while True:
      resp=self.sock.recv(4096)
      if self.debug==1:
        self.__log(resp)
      respl+=resp
      l=respl.split(CRLF)
      if len(resp)>0:
        if self.__noauth:
          if l[-1][-2:]=='> ' and l[-1][0]=='<':
            break
        else:
          if self.__c.search(respl):
            break
      else:
        break
    self.prompt=l[len(l)-1]
    self.context=l[len(l)-1][1:-2]
    if len(self.context)>0:
      if self.context[len(self.context)-1]=='#':
        self.context=self.context[:-1]
      if self.context=='':
        self.contexts=[]
      else:
        self.contexts=self.context.split('-')
    return respl

  def __put(self, cmd, localdebug=None):
    """
    Private method used by the cmd() method.
    """
    self.sock.send(cmd+CRLF)
    if localdebug!=None:
      if localdebug==1:
        self.__log(cmd+CRLF)
      return
    if self.debug==1:
      self.__log(cmd+CRLF)

  def cmd(self, s):
    """
    Sends a command to the CLI server.
    
    NOTE: The CRLF pair is added automatically to the command.
    """
    self.__put(s)

  def response(self):
    """
    Reads responses from the socket.
    If the debug=1, it outputs the response to the stdout.
    Also, it sets the current context (context and contexts variables).
    Returns a string containing the socket response.
    """
    return self.__get()

  def cmdr(self, s):
    """
    Wrapper to send a command and read its response in one call. Uses the cmd()
    and response() methods.
    """
    self.cmd(s)
    return self.response()

  def parse_resp(self, response):
    """
    Parses a response text (usually returned by the cmdr() or response() methods) and returns the tuple:
    code - integer with the value of 0 (successful +OK response) or 1 (error +ERR response)
    text - the exact response in addition to the +ERR or +OK text (server error reason string)
    response - contains the response, exactly the one given as argument
    """
    if not response:
      return (0, '', response)
    llines=response.split(CRLF)
    lastline=llines[len(llines)-2]
    if lastline[0]=='+':
      text=lastline[5:].rstrip()
      code=1
    elif lastline[0]=='-':
      text=lastline[6:].rstrip()
      code=0
    else:
      text=lastline.rstrip()
      code=0
    return (code, text, response)

  def isok(self, response):
    """
    Calls the parse_resp() method and returns only the 'code', so that it can
    be used inbricated in conditional instructions.
    """
    (code, text)=self.parse_resp(response)
    return code

  def shell(self):
    """
    Spawns a shell-like feature.
    It reads commands from the standard input and sends them to the standard output.

    NOTE: The debug variable is automatically set to 1 during this session, so
      that all the communication is displayed to stdout.
    """
    prevdebug=self.debug
    self.debug=1
    if prevdebug==0:
      STDOUT.write(self.prompt)
    while True:
      cmd=STDIN.readline().rstrip()
      if cmd.lower()=='exit':
        break
      if self.sock: self.__put(cmd, 0)
      if self.sock: self.__get()
    self.debug=prevdebug

  def auth(self, passwd, user='admin'):
    """
    Authenticates the CLI session. If either 'user' or 'passwd' are incorrect,
    it raises an exception
    """
    (code, text, _r)=self.parse_resp(self.cmdr('USER '+user))
    (code, text, _r)=self.parse_resp(self.cmdr(passwd))
    if not code:
      raise CLIErrorException('Authentication failed. Server response: %s' % text)
      return False
    self.__noauth=False
    return True

  def get_version_info(self):
    """
    Parses the response displayed by the GET VERSION command and inserts it
    into the V variable.
    """
    (_c, _t, _r)=self.parse_resp(self.cmdr('GET VERSION'))
    if not _c:
      raise CLIErrorException('GET VERSION failed. Server response: %s' % _t)
    _fver=_r.split(CRLF)[0].split('|')
    self.V['fullversion']=_fver[0]
    self.V['version']=self.V['fullversion'].split()[0]
    if len(_fver)>1:
      self.V['os']=_fver[1]
      self.V['platform']=_fver[2]
    else:
      self.V['os']='UNKNOWN'
      self.V['platform']='UNKNOWN'
    if 'bsd' in self.V['os'].lower():
      self.V['datadir']='/var/axigen'
    else:
      self.V['datadir']='/var/opt/axigen'

  def commit(self):
    """
    Executes the COMMIT command.
    Raises CLIErrorException if the command returns a -ERR response.
    """
    (code, text, resp)=self.parse_resp(self.cmdr('COMMIT'))
    if not code:
      raise CLIErrorException('Commit failed. Server response: %s' % text)

  def done(self):
    """
    Executes the DONE command.
    Raises CLIErrorException if the command returns a -ERR response.
    """
    (code, text, resp)=self.parse_resp(self.cmdr('DONE'))
    if not code:
      raise CLIErrorException('DONE command failed. Server response: %s' % text)

  def back(self):
    """
    Switches to the previous context without saving changes.
    Raises CLIErrorException if the command returns a -ERR response.
    """
    if self.context=='':
      return
    (code, text, resp)=self.parse_resp(self.cmdr('BACK'))
    if not code:
      raise CLIErrorException('%s command failed. Server response: %s' % (backcmd, text))

  def help(self):
    """
    Executes the HELP command
    Raises CLIErrorException if the command returns a -ERR response.
    """
    (code, text, resp)=self.parse_resp(self.cmdr('HELP'))
    if not code:
      raise CLIErrorException('Help failed. Server response: %s' % text)
    return resp

  def show(self, param=None):
    """
    Executes the SHOW command.
    Returns CLIErrorException if the server returns an error.
    """
    showcmd='SHOW'
    if param:
      showcmd+=' ATTR '+param
    (code, text, resp)=self.parse_resp(self.cmdr(showcmd))
    if not code:
      raise CLIErrorException('Command SHOW failed. Server response: %s' % text)
    return resp

  def show_registry(self):
    """
    Executes the SHOW REGISTRYINFORMATION command.
    Returns CLIErrorException if the server returns an error.
    """
    showcmd='SHOW REGISTRYINFORMATION'
    (code, text, resp)=self.parse_resp(self.cmdr(showcmd))
    if not code:
      raise CLIErrorException('Command SHOW REGISTRYINFORMATION failed. Server response: %s' % text)
    return resp

  def show_storageinformation(self):
    """
    Executes the SHOW STORAGEINFORMATION command.
    Returns CLIErrorException if the server returns an error.
    """
    showcmd='SHOW STORAGEINFORMATION'
    (code, text, resp)=self.parse_resp(self.cmdr(showcmd))
    if not code:
      raise CLIErrorException('Command SHOW STORAGEINFORMATION failed. Server response: %s' % text)
    return resp

  def show_contactinfo(self):
    """
    Executes the SHOW CONTACTINFO command.
    Returns CLIErrorException if the server returns an error.
    """
    showcmd='SHOW CONTACTINFO'
    (code, text, resp)=self.parse_resp(self.cmdr(showcmd))
    if not code:
      raise CLIErrorException('Command SHOW CONTACTINFO failed. Server response: %s' % text)
    return resp

  def set(self, param):
    """
    Executes the SET command.
    Returns CLIErrorException if the server returns an error.
    """
    (code, text, resp)=self.parse_resp(self.cmdr('SET %s' % param))
    if not code:
      raise CLIErrorException('Command `SET %s` failed. Server response: %s' % (param, text))
    return resp

  def get_show(self, param=None):
    """
    Parses the response to the SHOW command and returns a dictionary of
    attributes and their values.
    Returns CLIErrorException if the server returns an error.
    """
    d={}
    s=self.show(param)
    if param:
      return s.split(CRLF)[0].split(' = ')[1]
    else:
      for line in s.split(CRLF)[2:-3]:
        if '=' not in line:
          continue
        d[line.split(' = ')[0]]=line.split(' = ')[1]
    return d
  
  def get_show_registry(self):
    """
    Parses the response to the SHOW REGISTRYINFORMATION command and returns a
    dictionary of attributes and their values.
    Returns CLIErrorException if the server returns an error.
    """
    d={}
    s=self.show_registry()
    for line in s.split(CRLF)[2:-3]:
      if not '=' in line:
        continue
      d[line.split(' = ')[0]]=line.split(' = ')[1]
    return d

  def get_show_databaseUpdateStatus(self):
    """
    Parses the response to the SHOW databaseUpdateStatus command and returns a
    the output except for the last 2 lines.
    Returns CLIErrorException if the server returns an error.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('SHOW DATABASEUPDATESTATUS'))
    llines=resp.split(CRLF)
    acc=[]
    for line in llines[:-2]:
      acc.append(line.strip())
    return acc

  def get_show_storageinformation(self):
    """
    Parses the response to the SHOW STORAGEINFORMATION command and returns a
    list of storages and their fill/usage information.
    Returns CLIErrorException if the server returns an error.
    """
    d=[]
    s=self.show_storageinformation()
    for line in s.split(CRLF)[1:-2]:
      d.append(line.split())
    return d[:-1]
  
  def get_show_contactinfo(self):
    """
    Parses the response to the SHOW CONTACTINFO command and returns a
    dictionary of attributes and their values.
    Returns CLIErrorException if the server returns an error.
    """
    d={}
    s=self.show_contactinfo()
    for line in s.split(CRLF)[2:-3]:
      if '=' not in line:
        continue
      d[line.split(' = ')[0]]=line.split(' = ')[1]
    return d
  
  def update_domain(self, domain):
    """
    Executes UPDATE DOMAIN and enters the domain context. The argument is the domain name.
    Raises CLIErrorException if the command fails (i.e. the domain does not exist).
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('UPDATE DOMAIN NAME %s' % domain))
    if not code:
      raise CLIErrorException('Could not enter domain context for domain %s. Server response: %s' % (domain, text))

  def create_domain(self, domain, postmasterPasswd, domainLocation=None):
    """
    Executes CREATE DOMAIN and enters the domain context. The argument is the domain name.
    Raises CLIErrorException if the command fails.
    """
    self.require_auth()
    if not domainLocation:
      domainLocation=self.V['datadir']+'/domains/'+domain
    (code, text, resp)=self.parse_resp(self.cmdr('CREATE DOMAIN NAME %s DOMAINLOCATION %s POSTMASTERPASSWD %s' % (domain, domainLocation, postmasterPasswd)))
    if not code:
      raise CLIErrorException('Could not add domain %s. Server response: %s' % (domain, ddbLocation, text))

  def get_domains(self):
    """
    Returns a dictionary object containing the domains returned by the 'LIST
    DOMAINS' CLI command as list members
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('LIST DOMAINS'))
    if not code:
      raise CLIErrorException('Command LIST DOMAINS failed. Server response: %s' % text)
    llines=resp.split(CRLF)
    dom=[]
    for line in llines[5:-3]:
      if int(self.V['version'].split('.')[0])>=5:
        line=line.split()[0]
      dom.append(line.strip())
    return dom

  def add_forwarder(self, name=None):
    """
    Adds a forwarder into AXIGEN. You need to be into a domain context to issue this command.
    Arguments are the forwarder address, , as strings.
    Raises CLIErrorException if the account creation fails.
    """
    self.require_auth()
    cmd='ADD FORWARDER'
    if int(self.V['version'].split('.')[0])>=5:
      cmd='ADD GROUP'
    (code, text, resp)=self.parse_resp(self.cmdr('%s NAME "%s"' % (cmd, name)))
    if not code:
      raise CLIErrorException('Could not add group. Server response: %s' % text)

  def add_forwarder_address(self, address):
    """
    Adds an address for a forwarder. You must be in the domain-forwarder
    context to perform this operation.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('ADD ADDRESS "%s"' % address))
    if not code:
      raise CLIErrorException('Could not add address in this forwarder. Server response: %s' % text)

  def get_forwarders(self):
    """
    Returns a list object containing the forwarders returned by the 'LIST FORWARDERS' command.
    You need to be in a domain context to issue this command.
    """
    self.require_auth()
    cmd='LIST FORWARDERS'
    if int(self.V['version'].split('.')[0])>=5:
      cmd='LIST GROUPS'
    (code, text, resp)=self.parse_resp(self.cmdr(cmd))
    llines=resp.split(CRLF)
    fwd=[]
    for line in llines[5:-3]:
      fwd.append(line.strip())
    return fwd

  get_groups=get_forwarders

  def get_folderRcpts(self):
    """
    Returns a list object containing the forwarders returned by the 'LIST FOLDERRCPTS' command.
    You need to be in a domain context to issue this command.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('LIST FOLDERRCPTS'))
    llines=resp.split(CRLF)
    fr=[]
    for line in llines[5:-3]:
      fr.append(line.strip())
    return fr

  def get_accounts(self, pattern=None):
    """
    Returns a list object containing the accounts returned by the 'LIST ACCOUNTS' command.
    ATM, you need to be in a domain context to issue this command.
    """
    self.require_auth()
    _cmd='LIST ACCOUNTS'
    if pattern:
      _cmd=_cmd+' '+pattern
    (code, text, resp)=self.parse_resp(self.cmdr(_cmd))
    llines=resp.split(CRLF)
    acc=[]
    for line in llines[5:-3]:
      acc.append(line.strip().lower())
    return acc

  def get_mlists(self, pattern=None):
    """
    Returns a list object containing the mailing lists returned by the 'LIST
    LISTS' command.
    """
    self.require_auth()
    _cmd='LIST LISTS'
    if pattern:
      _cmd=_cmd+' '+pattern
    (code, text, resp)=self.parse_resp(self.cmdr(_cmd))
    llines=resp.split(CRLF)
    mls=[]
    for line in llines[5:-3]:
      mls.append(line.strip())
    return mls

  def list_users(self, onlyAddresses=False):
    """
    Returns a list object containing the mailing list members returned by the 'LIST
    USERS' command.
    """
    self.require_auth()
    _cmd='LIST USERS'
    (code, text, resp)=self.parse_resp(self.cmdr(_cmd))
    llines=resp.split(CRLF)
    mlm=[]
    for line in llines[5:-3]:
      linesplit=line.split(' | ')
      email=linesplit[0].strip()
      name=linesplit[1].strip()
      if onlyAddresses:
        member=email
      else:
        member=(email, name); 
      mlm.append(member)
    return mlm

  def get_aliases(self):
    """
    Returns a list object containing the accounts returned by the 'LIST
    ALIASES' command, for an account or domain.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('LIST ALIASES'))
    llines=resp.split(CRLF)
    acc=[]
    for line in llines[2:-3]:
      acc.append(line.strip())
    return acc

  def upload_wmfilter(self, wmstream):
    """
    Exectutes the UPLOAD WMFILTER command and sends the wmstream string to the
    server.
    """
    self.sock.send('UPLOAD WMFILTER'+CRLF)
    resp=self.sock.recv(4096)
    if resp[0:3]!='+OK':
      raise CLIErrorException('Could not upload wmfilter. Server response: %s' % resp.strip())
    for line in wmstream.split(CRLF):
      if line.startswith('.'):
        line='.'+line
      self.sock.send(line+CRLF)
    self.sock.send('.'+CRLF)
    resp=self.sock.recv(4096)
    if resp[0:3]!='+OK':
      raise CLIErrorException('Could not upload wmfilter. Server response: %s' % resp.strip())

  def show_account(self, account):
    """
    Returns a dictionary object containing the attributes of an account as keys
    and their values.
    ATM, you need to be in a domain context to issue this command.
    """
    self.require_auth()
    a={}
    (code, text, resp)=self.parse_resp(self.cmdr('SHOW ACCOUNT NAME %s' % account))
    llines=resp.split(CRLF)
    if not code:
      raise CLIErrorException('Coult not show attributes for account %s' % account)
    for l in llines[2:-2]:
      eqpos=l.find(' = ')
      a[l[:eqpos]]=l[eqpos+3:]
    del a['']
    return a

  def add_account(self, user=None, passwd=None):
    """
    Adds an account into AXIGEN. You need to be into a domain context to issue
    this command. Arguments are the username and password, as strings.
    Raises CLIErrorException if the account creation fails.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('ADD ACCOUNT NAME "%s" PASSWORD "%s"' % (user, passwd)))
    if not code:
      raise CLIErrorException('Could not add account. Server response: %s' % text)

  def del_account(self, user=None):
    """
    Deletes an account from AXIGEN. You need to be into a domain context to issue
    this command. Arguments are the username and password, as strings.
    Raises CLIErrorException if the account creation fails.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('REMOVE ACCOUNT NAME "%s"' % user))
    if not code:
      raise CLIErrorException('Could not remove account. Server response: %s' % text)

  def update_account(self, user=None):
    """
    Updates an account into AXIGEN. You need to be into a domain context to issue this command.
    Argument is the username, as string.
    Raises CLIErrorException if the account update process fails.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('UPDATE ACCOUNT NAME "%s"' % user))
    if not code:
      raise CLIErrorException('Could not update account details. Server response: %s' % text)

  def add_alias(self, alias=None):
    """
    Adds an alias to an account.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('ADD ALIAS "%s"' % alias))
    if not code:
      raise CLIErrorException('Could not add alias. Server response: %s' % text)

  def update_folderRcpt(self, folderRcpt):
    """
    Raises CLIErrorException if the folderRcpt update process fails.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('UPDATE FOLDERRCPT NAME "%s"' % folderRcpt))
    if not code:
      raise CLIErrorException('Could not update folderrcpt. Server response: %s' % text)

  def update_forwarder(self, forwarder):
    """
    Enters the forwarder context for a specified forwarder. Argument is the forwarder name, as string.
    Raises CLIErrorException if the forwarder update process fails.
    """
    self.require_auth()
    myname='FORWARDER'
    if int(self.V['version'].split('.')[0])>=5:
      myname='GROUP'
    (code, text, resp)=self.parse_resp(self.cmdr('UPDATE %s NAME "%s"' % (myname, forwarder)))
    if not code:
      raise CLIErrorException('Could not update forwarder details. Server response: %s' % text)

  def update_list(self, list):
    """
    Updates a list into AXIGEN. Argument is the mailing list name, as string.
    Raises CLIErrorException if the list update process fails
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('UPDATE LIST NAME "%s"' % list))
    if not code:
      raise CLIErrorException('Could not update list. Server response: %s' % text)

  def add_mlist(self, list, password, adminEmail):
    """
    Adds a mailing list into AXIGEN. Argument is the mailing list name, as string.
    Raises CLIErrorException if the list update process fails
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('ADD LIST NAME "%s" PASSWORD "%s" ADMINEMAIL "%s"' % (list, password, adminEmail)))
    if not code:
      raise CLIErrorException('Could not update list. Server response: %s' % text)

  def mlist_del_user(self, email):
    """
    Removes a member from a mailing list
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('REMOVE USER EMAIL "%s"' % email))
    if not code:
      raise CLIErrorException('Could not remove member from mlist. Server response: %s' % text)

  def mlist_add_user(self, email, name):
    """
    Adds a user into a mailing list
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('ADD USER EMAIL "%s" NAME "%s"' % (email, name)))
    if not code:
      raise CLIErrorException('Could not add user to mlist. Server response: %s' % text)

  def config_webmaildata(self):
    """
    Enters the webmaildata context for a user.
    Raises CLIErrorException if server returns an error.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('CONFIG WEBMAILDATA'))
    if not code:
      raise CLIErrorException('Could not enter webmaildata context. Server response: %s' % text)

  def config(self, context):
    """
    Enters a config context.
    Raises CLIErrorException if server returns an error.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('CONFIG %s' % context))
    if not code:
      raise CLIErrorException('Could not enter %s context. Server response: %s' % (context, text))

  def config_quotas(self):
    """
    Enters the quotas context for a user.
    Raises CLIErrorException if server returns an error.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('CONFIG QUOTAS'))
    if not code:
      raise CLIErrorException('Could not enter quotas context. Server response: %s' % text)

  def config_limits(self):
    """
    Enters the limits context for a user.
    Raises CLIErrorException if server returns an error.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('CONFIG LIMITS'))
    if not code:
      raise CLIErrorException('Could not enter limits context. Server response: %s' % text)

  def config_migrationdata(self):
    """
    Enters the migrationdata context for a domain.
    Raises CLIErrorException if server returns an error.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('CONFIG MIGRATIONDATA'))
    if not code:
      raise CLIErrorException('Could not enter migrationdata context. Server response: %s' % text)

  def config_contactinfo(self):
    """
    Enters the contactinfo context for an account.
    Raises CLIErrorException if server returns an error.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('CONFIG CONTACTINFO'))
    if not code:
      raise CLIErrorException('Could not enter contactinfo context. Server response: %s' % text)

  def config_ftpbackup(self):
    """
    Enters the ftpBackup context for an account.
    Raises CLIErrorException if server returns an error.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('CONFIG FTP-BACKUP'))
    if not code:
      raise CLIErrorException('Could not enter ftpBackup context. Server response: %s' % text)

  def set_webmaildata(self, settings=None):
    """
    Updates some attributes from the webmaildata context, given as parameter
    via the `settings' dictionary.
    Returns CLIErrorException if the server returns an error.
    """
    self.require_auth()
    for attr in settings.keys():
      self.set('%s %s' % (attr, settings[attr]))
 
  def set_data(self, settings=None):
    """
    Updates some attributes from the {webmail,migration}data context, given as parameter
    via the `settings' dictionary.
    Returns CLIErrorException if the server returns an error.
    """
    self.require_auth()
    for attr in settings.keys():
      self.set('%s %s' % (attr, settings[attr]))
 
  def remove_account(self, user=None):
    """
    Removes the account, given by its name.
    Raises CLIErrorException if the account deletion fails.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('REMOVE ACCOUNT NAME "%s"' % user))
    if not code:
      raise CLIErrorException('Could not remove account. Server response: %s' % text)

  def enter_commands(self):
    """
    Enters the 'commands' context.
    Raises CLIErrorException if the command fails.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('ENTER COMMANDS'))
    if not code:
      raise CLIErrorException('Could not enter commands context. Server response: %s' % text)

  def config_filters(self):
    """
    Enters the '*-filters' context. * may be server, domain or account.
    Raises CLIErrorException if the command fails.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('CONFIG FILTERS'))
    if not code:
      raise CLIErrorException('Could not enter filters context. Server response: %s' % text)

  def update_kav(self):
    """
    Enter Kaspersky AV context
    Raises CLIErrorException if server returns an error.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('UPDATE INTEGRATEDFILTER KASPERSKY-AV'))
    if not code:
      raise CLIErrorException('Could not update filter. Server response: %s' % text)

  def update_kav_kas_db(self):
    """
    Update Kaspersky database
    Raises CLIErrorException if server returns an error.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('UPDATE DATABASE'))
    if not code:
      raise CLIErrorException('Could not update filter. Server response: %s' % text)

  def update_kas(self):
    """
    Enter Kaspersky AS context
    Raises CLIErrorException if server returns an error.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('UPDATE INTEGRATEDFILTER KASPERSKY-AS'))
    if not code:
      raise CLIErrorException('Could not update filter. Server response: %s' % text)



  def enter_migration(self):
    """
    Enters the 'migration' context.
    Raises CLIErrorException if the command fails.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('ENTER MIGRATION'))
    if not code:
      raise CLIErrorException('Could not enter migration context. Server response: %s' % text)

  def filesystem_mount_dom(self, domain, mount_point=None):
    """
    Executes a filesystem mount command for a domain
    """
    self.require_auth()
    if not mount_point:
      mount_point=self.V['datadir']+os.sep+'run'+os.sep+'backup-mount'
    (code, text, resp)=self.parse_resp(self.cmdr('FILESYSTEM MOUNT "%s" domain "%s"' % (mount_point, domain)))
    if not code:
      raise CLIErrorException('Could not enter server context. Server response: %s' % text)

  def filesystem_umount(self, mount_point=None):
    """
    Executes a filesystem mount command for a domain
    """
    self.require_auth()
    if not mount_point:
      mount_point=self.V['datadir']+os.sep+'run'+os.sep+'backup-mount'
    (code, text, resp)=self.parse_resp(self.cmdr('FILESYSTEM UNMOUNT "%s"' % mount_point))
    if not code:
      raise CLIErrorException('Could not enter server context. Server response: %s' % text)

  def config_server(self):
    """
    Enters 'server' context.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('CONFIG SERVER'))
    if not code:
      raise CLIErrorException('Could not enter server context. Server response: %s' % text)

  def enter_commands_server(self):
    """
    Enters directly in the 'commands-server' context.
    """
    self.enter_commands()
    self.enter_server()

  def enter_commands_storage(self):
    """
    Enters directly in the 'commands-storage' context.
    """
    self.enter_commands()
    self.enter_storage()

  def save_config(self):
    """
    Saves the configuration to disk
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('SAVE CONFIG'))
    if not code:
      raise CLIErrorException('Could not save config. Server response: %s' % text)

  def migrate(self, account=None, rhost=None, rport=143, ruser=None, rpass=None, overridequota=True, verbose=True):
    """
    Migrates an account.
    ATM, you need to be in the 'domain' context to be able to issue this command.
    """
    self.require_auth()
    options=''
    if overridequota==True:
      options+=' OVERRIDEQUOTA YES'
    if verbose==True:
      options+=' VERBOSE YES'
    (code, text, resp)=self.parse_resp(
      self.cmdr('MIGRATE ACCOUNT %s REMOTEHOST %s REMOTEPORT %d REMOTEUSER %s REMOTEPASS %s%s' % 
      (account, rhost, rport, ruser, rpass, options)
    ))
    if not code:
      raise CLIErrorException('Migration failed. Server response: %s' % text)
  
  def require_auth(self):
    """
    Raises an exception if no authentication has been made, yet.
    """
    if self.context in ['login', 'password']:
      raise CLIErrorException('You are not authenticated.')
  
  def goto_root_context(self):
    """
    Executes 'BACK' until the root context.
    Raises CLIErrorException if the 'BACK' command fails.
    """
    self.require_auth()
    for i in self.contexts:
      self.back()
    if self.context!='':
      raise CLIErrorException('Falling back %d contexts did not set us to the root context')

  def goto_context(self, context):
    """
    Executes 'BACK' until the desired context.
    Raises CLIErrorException if the 'BACK' command fails.
    """
    self.require_auth()
    for i in self.contexts:
      if self.context==context:
        break
      self.back()
    if self.context!='':
      raise CLIErrorException('Falling back %d contexts did not set us to the root context')

  def register_domain(self, domainLocation=None):
    """
    Registers a domain location, given as parameter.
    Raises CLIErrorException if the server returns an error.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('REGISTER DOMAIN DOMAINLOCATION %s' % domainLocation))
    if not code:
      raise CLIErrorException('Could not register DDB %s. Server response: %s' % (domainLocation, text))

  def unregister_domain(self, domain=None):
    """
    Unregisters a domain (location), given as parameter.
    Raises CLIErrorException if the server returns an error.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('UNREGISTER DOMAIN NAME %s' % domain))
    if not code:
      raise CLIErrorException('Could not unregister DDB %s. Server response: %s' % (domain, text))

  def list_filters(self):
    """
    Returns a list with all the filters for any of the server, domain or account contexts.
    Raises CLIErrorException if the command fails.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('LIST FILTERS'))
    if not code:
      raise CLIErrorException('Could not enter filters context. Server response: %s' % text)
    if ('List of Socket Filters' not in resp) or \
      ('List of Script Filters' not in resp) or \
      ('List of Active Filters' not in resp):
      return None
    f={'Socket': [], 'Script': [], 'Active': []}
    c=''
    for line in resp.split('\r\n'):
      if line=='List of Socket Filters:':
        c='Socket'
        continue
      if line=='List of Script Filters:':
        c='Script'
        continue
      if line=='List of Active Filters:':
        c='Active'
        continue
      if not c:
        continue
      if not '|' in line:
        continue
      if 'name' in line and 'type' in line and 'file' in line:
        continue
      if 'priority' in line and 'filterName' in line and 'filterType' in line:
        continue
      rline=''
      for k in line.split('|'):
        rline+=' | '+k.strip()
      f[c].append(rline)
    return f
  
  def list_mboxes(self):
    """
    Lists mboxes for an account.
    Must be in domain-account-quotas context
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('LIST MBOXES'))
    if not code:
      raise CLIErrorException('Could not list mboxes. Server response: %s' % text)
    llines=resp.split(CRLF)
    mbs=[]
    for line in llines[5:-3]:
      mbs.append(line.strip(CRLF))
    return mbs

  def list_addresses(self):
    """
    Lists addresses for a forwarder.
    Must be in domain-forwarder/domain-group context
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('LIST ADDRESSES'))
    if not code:
      raise CLIErrorException('Could not list addresses. Server response: %s' % text)
    llines=resp.split(CRLF)
    add=[]
    for line in llines[2:-3]:
      add.append(line.strip())
    return add

  def show_mboxquota(self, mboxName):
    """
    Shows quota for a specific mbox
    Must be in domain-account-quotas context
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('SHOW MBOXQUOTA MBOXNAME "%s"' % mboxName))
    if not code:
      raise CLIErrorException('Could not show mboxquota. Server response: %s' % text)
    llines=resp.split(CRLF)
    mbq={}
    for line in llines[2:-3]:
      line=line.strip()
      ll=line.split('=')
      mbq[ll[0]]=ll[1]
    return mbq

  def compact_all(self, forced=False):
    """
    Executes a COMPACT ALL command. Must be in a domain context
    """
    self.require_auth()
    cmd="COMPACT ALL"
    if forced:
      cmd+=" FORCED"
    (code, text, resp)=self.parse_resp(self.cmdr(cmd))
    if not code:
      raise CLIErrorException('Compact failed. Server response: %s' % text)

  def compact_usid(self, usid, forced=False):
    """
    Executes a COMPACT STORAGE USID <usid> [FORCED] command. Must be in a domain context
    """
    self.require_auth()
    cmd="COMPACT STORAGE USID %s" % usid
    if forced:
      cmd+=" FORCED"
    (code, text, resp)=self.parse_resp(self.cmdr(cmd))
    if not code:
      raise CLIErrorException('Compact failed. Server response: %s' % text)
    return resp.split(CRLF)[:-2]

  def find_invalid_msg(self, accounts="*", purge=False):
    """
    Executes a FINDINVALIDMSG command. Must be in a domain context
    """
    self.require_auth()
    cmd="FINDINVALIDMSG "+accounts
    if purge:
      cmd+=" PURGE"
    (code, text, resp)=self.parse_resp(self.cmdr(cmd))
    if not code:
      raise CLIErrorException('Find invalid messages command failed. Server response: %s' % text)
    return resp.split(CRLF)[:-2]

  def list_storages(self):
    """\
    Lists all storages available in a domain.
    Returns a list object.
    """
    self.require_auth()
    (code, text, resp)=self.parse_resp(self.cmdr('LIST STORAGES'))
    if not code:
      raise CLIErrorException('Could not enter filters context. Server response: %s' % text)
    usids=[]
    for line in resp.split(CRLF)[2:-3]:
      usids.append(line.split()[0])
    return usids

class CLI(CLIBase):
  """
  AXIGEN CLI Control class
  This class defines methods for (almost) all AXIGEN CLI's commands.
  """
  def registerDomain(self, domainLocation=None):
    """
    Transparently registers a domain location, without having to switch
    contexts.
    """
    self.goto_root_context()
    self.register_domain(domainLocation)
    self.commit()
    self.save_config()
  
  def unregisterDomain(self, domainName=None):
    """
    Transparently unregisters a domain (location), without having to manually
    switch contexts.
    """
    self.goto_root_context()
    self.unregister_domain(domainName)
    self.save_config()

  def addAccount(self, domain, accountName, accountPass):
    """
    Adds an account transparently, without having to switch contexts.
    """
    self.goto_root_context()
    self.update_domain(domain)
    self.add_account(accountName, accountPass)
    self.commit()
    self.commit()

  def delAccount(self, domain, accountName):
    """
    Removes an account transparently, without having to switch contexts.
    """
    self.goto_root_context()
    self.update_domain(domain)
    self.del_account(accountName)
    self.commit()

  def addForwarder(self, domain, forwarderName, addrList=[]):
    """
    Adds a forwarder transparently, without having to switch contexts.
    """
    self.goto_root_context()
    self.update_domain(domain)
    self.add_forwarder(forwarderName)
    for addr in addrList:
      self.add_forwarder_address(addr)
    self.commit()
    self.commit()

  def addDomain(self, domain, postmasterPasswd, domainLocation):
    """
    Adds a domain transparently, without having to switch contexts.
    TODO: domainLocation should be automatically generable
    """
    self.goto_root_context()
    self.create_domain(domain, postmasterPasswd, domainLocation)
    self.commit()
    self.save_config()

  def getDomainsList(self):
    """
    Returns a dictionary containing the domains from the remote AXIGEN server
    with each domain's details as sub-dictionaries.
    Handles the contexts transparently.
    """
    self.goto_root_context()
    return self.get_domains()

  def hasDomain(self, domain):
    """
    Returns True if the domain name given as parameter exists in AXIGEN, or
    False otherwise.
    """
    return domain in self.getDomainsList()

  def hasAccount(self, domain, account):
    """
    Returns True if the account name given as parameter exists in specified domain, or
    False otherwise.
    """
    return account in self.getAccountsList(domain)

  def getDomainIfExists(self, domain):
    """
    Returns the domain name if exists, raises an exception if it doesn't, or
    returns the first domain name defined in AXIGEN, if domain=None.
    """
    if domain:
      if self.hasDomain(domain):
        return domain
      else:
        raise CLIErrorException('Specified domain does not exist in AXIGEN: %s' % domain)
    dl=self.getDomainsList()
    if len(dl)>0:
      return dl[0]
    raise CLIErrorException('No domains defined in AXIGEN')

  def getAccountsList(self, domain=None):
    """
    Returns a list containing the account names within a specific domain.
    If domain=None, then the domain is considered the first domain from the
    domains list.
    """
    dl=self.getDomainsList()
    if domain==None and len(dl)>0:
      domain=dl[0]
    if not domain:
      raise CLIErrorException('No domain specified and none exists AXIGEN')
    self.goto_root_context()
    self.update_domain(domain)
    return self.get_accounts()

  def getForwardersList(self, domain=None):
    """
    Returns a list containing the forwarders names within a specific domain.
    If domain=None, then the domain is considered the first domain from the
    domains list.
    """
    dl=self.getDomainsList()
    if domain==None and len(dl)>0:
      domain=dl[0]
    if not domain:
      raise CLIErrorException('No domain specified and none exists AXIGEN')
    self.goto_root_context()
    self.update_domain(domain)
    return self.get_forwarders()

  def migrateAccount(self, account, domain, remoteImapHost, remoteImapPort, remoteImapUser, remoteImapPass, overrideQuota=False, verbose=False):
    """
    Migrates an account using the internal CLI Migration feature.
    """
    self.goto_root_context()
    self.update_domain(domain)
    self.migrate(account, remoteImapHost, remoteImapPort, remoteImapUser, remoteImapPass)

  def uploadWmFilter(self, account, domain, wmstream):
    """
    Adds a WM filter for a specific account.
    """
    self.goto_root_context()
    self.update_domain(domain)
    self.update_account(account)
    self.upload_wmfilter(wmstream)
    self.commit()

  def accountDetails(self, account=None, domain=None):
    """
    Returns a dictionary object containing the attributes of an account as keys
    and their values. If account or domain is None, the first one is considered.
    """
    dl=self.getDomainsList()
    if domain==None and len(dl)>0:
      domain=dl[0]
    if not domain:
      raise CLIErrorException('No domain specified and none exists AXIGEN')
    if not account:
      account=self.getAccountsList(domain)[0]
    self.goto_root_context()
    self.update_domain(domain)
    return self.show_account(account)

  def setAccountWebmailData(self, account=None, domain=None, settings={}):
    """
    Sets some attributes for an account's webmail data. The settings are given
    as parameter.
    """
    if not account:
      account=self.getAccountsList(domain)[0]
    self.goto_root_context()
    self.update_domain(self.getDomainIfExists(domain))
    self.update_account(account)
    self.config_webmaildata()
    self.set_webmaildata(settings)
    self.done()
    self.commit()

  def setAccountData(self, account=None, domain=None, settings={}):
    """
    Sets some attributes for an account's details. The settings are given
    as parameter.
    """
    if not account:
      account=self.getAccountsList(domain)[0]
    self.goto_root_context()
    self.update_domain(self.getDomainIfExists(domain))
    self.update_account(account)
    self.set_data(settings)
    self.commit()
    self.commit()

  def setAccountContactData(self, account=None, domain=None, settings={}):
    """
    Sets some attributes for an account's details. The settings are given
    as parameter.
    """
    if not account:
      account=self.getAccountsList(domain)[0]
    self.goto_root_context()
    self.update_domain(self.getDomainIfExists(domain))
    self.update_account(account)
    self.config_contactinfo()
    self.set_data(settings)
    self.done()
    self.commit()
    self.commit()

  def setAccountQuotas(self, account=None, domain=None, settings={}):
    """
    Sets some attributes for an account's details. The settings are given
    as parameter.
    """
    if not account:
      account=self.getAccountsList(domain)[0]
    self.goto_root_context()
    self.update_domain(self.getDomainIfExists(domain))
    self.update_account(account)
    self.config_quotas()
    self.set_data(settings)
    self.done()
    self.commit()

  def setDomainMigrationData(self, domain=None, settings={}):
    """
    Sets some attributes for an domain's migration data. The settings are given
    as parameter.
    """
    self.goto_root_context()
    self.update_domain(self.getDomainIfExists(domain))
    self.config_migrationdata()
    self.set_data(settings)
    self.done()
    self.commit()

  def setDomainData(self, domain=None, settings={}):
    """
    Sets some attributes for an domain's migration data. The settings are given
    as parameter.
    """
    self.goto_root_context()
    self.update_domain(self.getDomainIfExists(domain))
    self.set_data(settings)
    self.commit()

  def getAccountWebmailData(self, account=None, domain=None):
    """
    Returns a dictionary containing the account's webmaildata settings.
    """
    domain=self.getDomainIfExists(domain)
    if not account:
      account=self.getAccountsList(domain)[0]
    self.goto_root_context()
    self.update_domain(self.getDomainIfExists(domain))
    self.update_account(account)
    self.config_webmaildata()
    return self.get_show()

  def getAccountQuotas(self, account=None, domain=None):
    """
    Returns a dictionary containing the account's webmaildata settings.
    """
    domain=self.getDomainIfExists(domain)
    if not account:
      account=self.getAccountsList(domain)[0]
    self.goto_root_context()
    self.update_domain(self.getDomainIfExists(domain))
    self.update_account(account)
    self.config_quotas()
    return self.get_show()

  def getAccountData(self, account=None, domain=None):
    """
    Returns a dictionary containing the account's data settings.
    """
    domain=self.getDomainIfExists(domain)
    if not account:
      account=self.getAccountsList(domain)[0]
    self.goto_root_context()
    self.update_domain(domain)
    self.update_account(account)
    data=dict(self.get_show())
    if (int(self.V['version'].split('.')[0])>6) or (int(self.V['version'].split('.')[0])==6 and int(self.V['version'].split('.')[1])>=2):
      self.config_contactinfo()
      data.update(self.get_show())
      self.back()
    else:
      data.update(self.get_show_contactinfo())
    data.update({'emailAddress': data['name'].strip('"')+'@'+domain.strip('"')})
    return data

  def getAccountAliases(self, account=None, domain=None):
    """
    Returns a list of the account's aliases.
    """
    domain=self.getDomainIfExists(domain)
    if not account:
      account=self.getAccountsList(domain)[0]
    self.goto_root_context()
    self.update_domain(domain)
    self.update_account(account)
    data=self.get_aliases()
    return data

  def getAccountRegistry(self, account=None, domain=None):
    """
    Returns a dictionary containing the account's data settings.
    """
    domain=self.getDomainIfExists(domain)
    if not account:
      account=self.getAccountsList(domain)[0]
    self.goto_root_context()
    self.update_domain(domain)
    self.update_account(account)
    data=dict(self.get_show_registry())
    return data

  def getShowDatabaseUpdateStatusKAS(self):
    """
    Returns the output of show databaseupdatestatus for KAS
    """
    self.goto_root_context()
    self.config_server()
    self.config_filters()
    self.update_kas()
    data=self.get_show_databaseUpdateStatus()
    return data

  def getShowDatabaseUpdateStatusKAV(self):
    """
    Returns the output of show databaseupdatestatus for KAV
    """
    self.goto_root_context()
    self.config_server()
    self.config_filters()
    self.update_kav()
    data=self.get_show_databaseUpdateStatus()
    return data

  def mListAddUser(self, list=None, domain=None, email=None, name=None):
    """
    Adds a user to a mailing list
    """
    self.goto_root_context()
    self.update_domain(domain)
    self.update_list(list)
    self.mlist_add_user(email, name)
    self.done()
    self.commit()



#####################################################
###            Other useful methods               ###
#####################################################

def __myint(x):
  """
  Private method that returns 0 if a string cannot be converted to int, or the
  result of the int() call
  """
  try:
    y=int(x)
  except ValueError:
    y=0
  return y

def __myfloat(x):
  """
  Private method that returns 0.0 if a string cannot be converted to float, or
  the result of the float() call
  """
  try:
    y=float(x)
  except ValueError:
    y=0.0
  return y

def strtime2epoch(s):
  """
  Public method that converts a string containing a time specification, into a
  float number, epoch.
  """
  import time
  return time.mktime(time.strptime(s, '%a, %d %b %Y %H:%M:%S'))


#####################################################
###            Main build-in method               ###
#####################################################

if __name__=='__main__':
  # only displays help when invoked directly
  __name__='cli2'
  help('cli2')
