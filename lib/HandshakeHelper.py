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

import struct
import MessageHelper


class HandshakeHelper:
  """Class to aid making initial xrootd handshakes."""
  
  def __init__(self, context):
    self.mh = MessageHelper.MessageHelper(context)
    
  @property
  def request(self):
    """Return a packed representation of a client handshake request."""
    request_struct = self.mh.get_struct('ClientInitHandShake')    
    params = {'first'   : 0,
              'second'  : 0, 
              'third'   : 0,
              'fourth'  : 4,
              'fifth'   : 2012}
    
    return self.mh.build_request(request_struct, params)
  
  @property
  def response(self):
    """Return a packed representation of a server handshake response."""
    response_struct = self.mh.get_struct('ServerResponseHeader') \
                    + self.mh.get_struct('ServerInitHandShake')
    params = {'streamid'  : '\0\0',
              'status'    : 0,
              'dlen'      : 8,
              'protover'  : 663,
              'msgvar'    : 1}
    
    return self.mh.build_request(response_struct, params)
  
  def unpack_request(self, request):
    """Return an unpacked tuple representation of a client handshake
    request."""
    request_struct = self.mh.get_struct('ClientInitHandShake')
    format = '>'
    
    for member in request_struct:
      format += member['type']
      
    return struct.unpack(format, request)
  
  def unpack_response(self, response):
    """Return an unpacked tuple representation of a server handshake 
    response."""
    response_struct = self.mh.get_struct('ServerResponseHeader') \
                    + self.mh.get_struct('ServerInitHandShake')
    format = '>'
    
    for member in response_struct:
      format += member['type']
      
    response = struct.unpack(format, response)
    return self.mh.get_responseid(response[1]), response
  