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
from Utils import format_length, struct_format

class AuthHelper:
  
  def __init__(self, context):
    self.context = context
    self.mh = MessageHelper.MessageHelper(context)

  def request(self, authparams, token=None):
    credname, credentials, credlen = \
    self.getcredentials(authparams,
                        token,
                        self.context['seclib'],
                        self.context['socket'].fileno())
    
    request_struct = self.mh.get_struct('ClientAuthRequest')
    params = {'streamid'  : self.context['streamid'],
              'requestid' : self.requestid,
              'reserved'  : 12 * '\0',
              'credtype'  : list(credname.ljust(4, '\0')),
              'dlen'      : credlen,
              'cred'      : credentials}
    
    return self.mh.build_message(request_struct, params)
  
  def response(self, streamid):
    response_struct = self.mh.get_struct('ServerResponseHeader')
                      
    params = {'streamid'  : streamid,
              'status'    : XProtocol.XResponseType.kXR_ok,
              'dlen'      : 0}
    
    return self.mh.build_message(response_struct, params)
  
  @property
  def requestid(self):
    return XProtocol.XRequestTypes.kXR_auth
  
  @property
  def request_format(self):
    return struct_format(self.mh.get_struct('ClientAuthRequest'))
  
  def getcredentials(self, authparams, token, seclib, sockfd):
    try:
      credname, creds = get_credentials(authparams, token, seclib,
                                        sockfd)
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
  
  def unpack_request(self, request):
    request_struct = self.mh.get_struct('ClientAuthRequest')
    format = '>'
    
    for member in request_struct:
      if member['name'] == 'cred':
        continue
      if member.has_key('size'):
        format += (str(member['size']) + member['type'])
      else:
        format += member['type']
        
    format += (str(len(request) - format_length(format)) + 's')
    return struct.unpack(format, request)
      
  def unpack_response(self, response):
    response_struct = self.mh.get_struct('ServerResponseHeader')
    format = '>'
    
    for member in response_struct:
      format += member['type']
    
    if len(response) > format_length(format):
      format += (str(len(response) - format_length(format)) + 's')
      
    response = struct.unpack(format, response)
    return self.mh.get_responseid(response[1]), response
