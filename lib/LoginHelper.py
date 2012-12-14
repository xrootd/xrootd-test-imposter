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
from Utils import flatten, format_length, struct_format, gen_sessid

class LoginHelper:
  """Class to aid in performing an xrootd login sequence."""

  def __init__(self, context):
    self.context = context
    self.mh = MessageHelper.MessageHelper(context)
    
  def request(self, username, admin):
    request_struct = self.mh.get_struct('ClientLoginRequest')
    params = {'streamid'  : self.context['streamid'],
              'requestid' : self.requestid,
              'pid'       : os.getpid(),
              'username'  : list(username[:8].ljust(8, "\0")),
              'reserved'  : '\0',
              'zone'      : '\0',
              'capver'    : chr(XProtocol.XLoginCapVer.kXR_asyncap \
                                | XProtocol.XLoginVersion.kXR_ver003),
              'role'      : '1' if admin else '0',
              'dlen'      : 0}
    
    return self.mh.build_message(request_struct, params)
  
  def response(self, streamid):
    response_struct = self.mh.get_struct('ServerResponseHeader') + \
                      self.mh.get_struct('ServerResponseBody_Login')
                      
    sec = self.context['secparams']
    params = {'streamid'  : streamid,
              'status'    : XProtocol.XResponseType.kXR_ok,
              'dlen'      : len(sec) + 16,
              'sessid'    : gen_sessid(),
              'sec'       : sec}
    
    return self.mh.build_message(response_struct, params)
  
  @property
  def requestid(self):
    return XProtocol.XRequestTypes.kXR_login
  
  @property
  def request_format(self):
    return struct_format(self.mh.get_struct('ClientLoginRequest'))

  def unpack_request(self, request):
    request_struct = self.mh.get_struct('ClientLoginRequest')
    format = '>'
    
    for member in request_struct:
      format += member['type']
      
    return struct.unpack(format, request)
    
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
