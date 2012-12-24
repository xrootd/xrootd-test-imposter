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
import AuthHelper
from Utils import *

class LoginHelper:
  """Class to aid in performing an xrootd login sequence."""

  def __init__(self, context):
    self.context = context
    self.mh = MessageHelper.MessageHelper(context)
    
  def build_request(self, streamid=None, requestid=None, pid=None, username=None,
                    reserved=None, zone=None, capver=None, role=None, dlen=None):
    """Return a packed representation of a kXR_login request. The default 
    request values can be individually modified by the optional keyword args."""
    request_struct = get_struct('ClientLoginRequest')
    
    params = \
    {'streamid'  : streamid   if streamid   else self.context['streamid'],
     'requestid' : requestid  if requestid  else self.requestid,
     'pid'       : pid        if pid        else os.getpid(),
     'username'  : username   if username   else ''.ljust(8, "\0"),
     'reserved'  : reserved   if reserved   else '\0',
     'zone'      : zone       if zone       else '\0',
     'capver'    : capver     if capver     else chr(XProtocol.XLoginCapVer.kXR_asyncap \
                                                     | XProtocol.XLoginVersion.kXR_ver003),
     'role'      : role       if role       else '0',
     'dlen'      : dlen       if dlen       else 0}
    
    return self.mh.build_message(request_struct, params)
  
  def build_response(self, streamid=None, status=None, dlen=None, sessid=None,
                     sec=None):
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Login')
                      
    # Check if client needs to authenticate
    auth = AuthHelper.AuthHelper(self.context) 
    if not sec:
      sec = auth.get_sec_token()
                      
    params = \
    {'streamid'  : streamid   if streamid   else 0,
     'status'    : status     if status     else XProtocol.XResponseType.kXR_ok,
     'dlen'      : dlen       if dlen       else len(sec) + 16,
     'sessid'    : sessid     if sessid     else gen_sessid(),
     'sec'       : sec}
    
    return self.mh.build_message(response_struct, params)
  
  @property
  def requestid(self):
    return XProtocol.XRequestTypes.kXR_login
  
  @property
  def request_format(self):
    return struct_format(get_struct('ClientLoginRequest'))

