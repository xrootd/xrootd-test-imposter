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
  
  def __init__(self, context):
    self.context = context
    self.mh = MessageHelper.MessageHelper(context)

  def request(self, authparams):
    credname, credentials, credlen = \
    self.getcredentials(authparams, 
                        self.context['seclib'],
                        self.context['sock'].fileno())
    
    request_struct = self.mh.get_struct('ClientAuthRequest')
    params = {'streamid'  : self.context['streamid'],
              'requestid' : self.requestid,
              'reserved'  : 12 * '\0',
              'credtype'  : list(credname.ljust(4, '\0')),
              'dlen'      : credlen,
              'cred'      : credentials}
    
    return self.mh.build_message(request_struct, params)
  
  @property
  def requestid(self):
    return XProtocol.XRequestTypes.kXR_auth
  
  def getcredentials(self, authparams, seclib, sockfd):
    try:
      credname, cred, credlen = get_credentials(authparams, seclib, sockfd)
      credentials = list(cred.ljust(credlen, '\0'))
    except IOError, e:
      print "[!] Error authenticating:", e
      sys.exit(1)
    return credname, credentials, credlen
      
  def unpack_response(self, response):
    response_struct = self.mh.get_struct('ServerResponseHeader')
    format = '>'
    
    for member in response_struct:
      format += member['type']
    
    if len(response) > format_length(format):
      format += (str(len(response) - format_length(format)) + 'c')
      
    response = struct.unpack(format, response)
    return self.mh.get_responseid(response[1]), response

