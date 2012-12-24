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
import tempfile

import XProtocol
import MessageHelper

from authbind import get_credentials, authenticate, get_parms
from Utils import *

class AuthHelper:
  
  def __init__(self, context):
    self.context = context
    self.mh = MessageHelper.MessageHelper(context)

  def build_request(self, authtoken=None, contcred=None, streamid=None, 
                    requestid=None, reserved=None, credtype=None, dlen=None, 
                    cred=None):
    
    if not authtoken and not contcred:
      print "[!] Can't build kXR_auth request: no auth token or continuation \
            credentials supplied"
      sys.exit(1)
      
    credname, credentials, credlen = \
    self.getcredentials(authtoken,
                        contcred,
                        self.context['seclib'],
                        self.context['socket'].fileno())
    
    request_struct = get_struct('ClientAuthRequest')
    params = {'streamid'  : streamid  if streamid   else self.context['streamid'],
              'requestid' : requestid if requestid  else self.requestid,
              'reserved'  : reserved  if reserved   else 12 * '\0',
              'credtype'  : credtype  if credtype   else credname.ljust(4, '\0'),
              'dlen'      : dlen      if dlen       else credlen,
              'cred'      : cred      if cred       else credentials}
    
    return self.mh.build_message(request_struct, params)
  
  def build_response(self, streamid=None, status=None, dlen=None):
    response_struct = get_struct('ServerResponseHeader')
                      
    params = {'streamid'  : streamid  if streamid   else 0,
              'status'    : status    if status     else XProtocol.XResponseType.kXR_ok,
              'dlen'      : dlen      if dlen       else 0}
    
    return self.mh.build_message(response_struct, params)
  
  @property
  def requestid(self):
    return XProtocol.XRequestTypes.kXR_auth
  
  @property
  def request_format(self):
    return struct_format(get_struct('ClientAuthRequest'))
  
  def getcredentials(self, authtoken, contcred, seclib, sockfd):
    try:
      credname, creds = get_credentials(authtoken, contcred, seclib, sockfd)
    except IOError, e:
      print "[!] Error getting credentials:", e
      sys.exit(1)
    return credname, creds, len(creds)
  
  def get_sec_token(self):
    try:
      token = get_parms('sec.protocol ' + self.context['sec.protocol'] + '\n',
                     self.context['seclib'])
    except IOError, e:
      print "[!] Error getting security token:", e
      sys.exit(1)
    
    return token
  
  def auth(self, creds):
    try:
      authenticate(bytearray(creds),
                   self.context['seclib'],
                   'sec.protocol ' + self.context['sec.protocol'] + '\n',
                   self.context['socket'].fileno())
    except IOError, e:
      print "[!] Error authenticating:", e
      sys.exit(1)
