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
import MessageHelper
from Utils import flatten, format_length

class LoginHelper:
  """Class to aid in performing an xrootd login sequence."""

  def __init__(self, context, username, admin):
    self.streamid = context['streamid']
    self.user = username
    self.admin = admin
    self.mh = MessageHelper.MessageHelper(context)
    
  @property
  def request(self):
    request_struct = self.mh.get_struct('ClientLoginRequest')
    params = {'streamid'  : self.streamid,
              'requestid' : self.requestid,
              'pid'       : self.pid,
              'username'  : self.username,
              'reserved'  : '\0',
              'zone'      : '\0',
              'capver'    : self.capver,
              'role'      : self.role,
              'dlen'      : self.dlen}     
    
    return self.mh.build_request(request_struct, params)
  
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
    return chr(XProtocol.XLoginCapVer.kXR_asyncap \
           | XProtocol.XLoginVersion.kXR_ver003)

  @property
  def role(self):
    return '1' if self.admin else '0'
    
  @property
  def dlen(self):
    return 0
    
  def unpack_request(self):
    pass
    
  def unpack_response(self, response):
    response_struct = self.mh.get_struct('ServerResponseHeader') \
                    + self.mh.get_struct('ServerResponseBody_Login')
    format = '>'
    
    for member in response_struct:
      if member['name'] == 'sec': continue
      
      if member.has_key('size'):
        format += str(member['size']) + member['type']
      else: 
        format += member['type']
    
    if len(response) > 24:
      # Authentication needed
      auth = True
      response = struct.unpack(format + (str(len(response) 
                                             - format_length(format)) + 's'), 
                               response)
    else:
      # Authentication not needed
      auth = False
      response = struct.unpack(format, response)

    return self.mh.get_responseid(response[1]), \
           {'message': response, 'auth': auth}
