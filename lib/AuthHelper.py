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
from authbind import get_credentials
from Utils import flatten

class AuthHelper:
  
  def __init__(self, response, streamid, sock):
    self.authparams = ''.join(response[4:])
    self.streamid = streamid
    self.sock = sock
    self.getcredentials()
    
  @property
  def request(self):
    request = tuple(flatten(self.streamid, self.requestid, self.reserved,
                            self.credtype, self.credlen, self.credentials))
    return struct.pack('>HH12c4cl' + ('c' * self.credlen), *request)

  @property
  def requestid(self):
    return XProtocol.XRequestTypes.kXR_auth
  
  @property
  def reserved(self):
    return list(12 * '\0')
  
  @property
  def credtype(self):
    return list(self.credname.ljust(4, '\0'))
    
  def getcredentials(self):
    try:
      self.credname, self.credentials, self.credlen \
      = get_credentials(self.authparams, 'libXrdSec.so', self.sock.fileno())
      self.credentials = list(self.credentials.ljust(self.credlen, '\0'))
    except IOError, e:
      print "[!] Error authenticating:", e
      sys.exit(1)
      
  def unpack_response(self, response):
    return struct.unpack('>HHl' + ('c' * (len(response) - 8)), response)

