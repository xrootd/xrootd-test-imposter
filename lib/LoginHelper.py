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

import os
import struct

import XProtocol
from Utils import flatten

class LoginHelper:
    """Class to aid in performing an xrootd login sequence."""

    def __init__(self, streamid, username, admin):
      self.streamid = streamid
      self.user = username
      self.admin = admin
      
    @property
    def request(self):
      request = tuple(flatten(self.streamid, self.requestid, self.pid,
                              self.username, '\0', '\0', self.capver,
                              self.role, self.tlen))
      return struct.pack('>HHl10cBcl', *request)
    
    @property
    def response(self):
      pass
    
    @property
    def requestid(self):
      return XProtocol.XRequestTypes.kXR_login
    
    @property
    def pid(self):
      return os.getpid()
    
    @property
    def username(self):
      return list(self.user[:8].ljust(8, "\0"))
    
    @property
    def capver(self):
      return XProtocol.XLoginCapVer.kXR_asyncap \
             | XProtocol.XLoginVersion.kXR_ver003

    @property
    def role(self):
      return '1' if self.admin else '0'
      
    @property
    def tlen(self):
      return 0
      
    def unpack_response(self, response):
      if not len(response) > 24:
        # Authorization not needed
        return {'response': struct.unpack('>HHl16s', response),
                'auth': False}
      else:
        # Authorization needed
        return {'response': struct.unpack('>HHl16s' + ('c' * (len(response) - 24)), response),
                'auth': True}
      
        
