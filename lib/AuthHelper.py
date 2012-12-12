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

import XProtocol
import MessageHelper

from authbind import get_credentials
from Utils import format_length

class AuthHelper:
  
  def __init__(self, context, response):
    self.authparams = ''.join(response[4:])
    self.seclib = context['seclib']
    self.streamid = context['streamid']
    self.sock = context['socket']
    
    self.mh = MessageHelper.MessageHelper(context)
    self.getcredentials()
    
  @property
  def request(self):
    request_struct = self.mh.get_struct('ClientAuthRequest')
    params = {'streamid'  : self.streamid,
              'requestid' : self.requestid,
              'reserved'  : self.reserved,
              'credtype'  : self.credtype,
              'dlen'      : self.credlen,
              'cred'      : self.credentials}
    
    return self.mh.build_request(request_struct, params)

  @property
  def requestid(self):
    return XProtocol.XRequestTypes.kXR_auth
  
  @property
  def reserved(self):
    return 12 * '\0'
  
  @property
  def credtype(self):
    return list(self.credname.ljust(4, '\0'))
    
  def getcredentials(self):
    try:
      self.credname, self.credentials, self.credlen \
      = get_credentials(self.authparams, self.seclib, self.sock.fileno())
      self.credentials = list(self.credentials.ljust(self.credlen, '\0'))
    except IOError, e:
      print "[!] Error authenticating:", e
      sys.exit(1)
      
  def unpack_response(self, response):
    response_struct = self.mh.get_struct('ServerResponseHeader')
    format = '>'
    
    for member in response_struct:
      format += member['type']
    
    if len(response) > format_length(format):
      format += (str(len(response) - format_length(format)) + 'c')
      
    response = struct.unpack(format, response)
    return self.mh.get_responseid(response[1]), response

