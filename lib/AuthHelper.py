#-------------------------------------------------------------------------------
# Copyright (c) 2011-2012 by European Organization for Nuclear Research (CERN)
# Author: Justin Salmon <jsalmon@cern.ch>
#-------------------------------------------------------------------------------
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------

import sys
import socket
import struct
import re
import os

import XProtocol
import MessageHelper

from XrdAuthBind import init, get_credentials, authenticate, get_parms, \
                        AuthenticationError
from Utils import getMessageStruct, getResponseId

class AuthHelper:
  """Class to aid sending/receiving xrootd authentication requests/responses,
  generating security tokens/credentials and authenticating client 
  credentials."""

  def __init__(self, context):
    self.context = context
    self.mh = MessageHelper.MessageHelper(context)
    # Initialize the auth binding extension
    self.init(self.context['config'])

  def build_request(self, authtoken=None, contcred=None, streamid=None, 
                    requestid=None, reserved=None, credtype=None, dlen=None, 
                    cred=None):
    """Return a packed kXR_auth request."""

    if not authtoken and not contcred:
      print "[!] Can't build kXR_auth request: no auth token or continuation \
            credentials supplied"
      sys.exit(1)

    credname, credentials, credlen = \
    self.getcredentials(authtoken, contcred, self.context['socket'].fileno())

    request_struct = getMessageStruct('ClientRequestHdr') + getMessageStruct('ClientAuthRequest')
    params = \
    {'streamid'  : streamid  if streamid   else self.context['streamid'],
     'requestid' : requestid if requestid  else XProtocol.XRequestTypes.kXR_auth,
     'reserved'  : reserved  if reserved   else 12 * '\0',
     'credtype'  : credtype  if credtype   else credname.ljust(4, '\0'),
     'dlen'      : dlen      if dlen       else credlen,
     'cred'      : cred      if cred       else credentials}

    return self.mh.build_message(request_struct, params)

  def build_response(self, cred=None, streamid=None, status=None, dlen=None):
    """Return a packed kXR_auth response."""
    if cred:
      self.auth(cred)

    response_struct = getMessageStruct('ServerResponseHeader')
    params = \
    {'streamid'  : streamid  if streamid   else 0,
     'status'    : status    if status     else XProtocol.XResponseType.kXR_ok,
     'dlen'      : dlen      if dlen       else 0}

    return self.mh.build_message(response_struct, params)

  #=============================================================================
  # Authentication binding function wrappers
  #=============================================================================
  def init(self, config):
    """Initialize the XrdAuthBind extension."""
    try:
      seclib = self._extract_seclib_path(config)
      init(config, seclib)
    except AuthenticationError, e:
      print "[!] Error initializing XrdAuthBind extension: ", e
      raise e
    
  def getcredentials(self, authtoken, contcred, sockfd):
    """Return opaque credentials after acquiring them from the xrootd
    security interface. These can be either the initial credentials or
    some continuation credentials."""
    try:
      credname, creds = get_credentials(authtoken, contcred, sockfd)
      return credname, creds, len(creds)
    except AuthenticationError, e:
      print "[!] Error getting credentials:", e
      raise e

  def getsectoken(self):
    """Return the security token to be sent in a kXR_login response."""
    try:
      token = get_parms()
      return token
    except AuthenticationError, e:
      print "[!] Error getting security token:", e
      raise e

  def auth(self, cred):
    """Authenticate the given opaque credentials."""
    try:
      contparams = authenticate(cred, self.context['socket'].fileno())
      return contparams if contparams else None
    except AuthenticationError, e:
      print "[!] Error authenticating:", e
      raise e

  #=============================================================================
  # Private methods
  #=============================================================================
  def _extract_seclib_path(self, config):
    """Return the path to libXrdSec from the given config file. It's easier
    to do it here than in the extension."""
    _match = re.match('^\s*(xrootd.seclib\s.*)$', config, re.MULTILINE)
    if not _match:
      raise AuthenticationError('xrootd.seclib not specified in config')
    else:
      return _match.groups()[0].split(os.path.sep)[-1].replace('\n', '')
    
