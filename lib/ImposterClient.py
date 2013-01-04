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
import struct
import socket
import os

import XProtocol
import MessageHelper
import AuthHelper
import OpenHelper

from Utils import get_struct, get_requestid, gen_sessid


class ImposterClient:
  """Class to aid sending/receiving xrootd client messages."""
    
  def __init__(self, context):
    self.context = context    
    self.mh = MessageHelper.MessageHelper(context)
  
  def send(self, request):
    """Send a packed xrootd request."""
    self.mh.send_message(request)
    
  def receive(self):
    """Receive a packed xrootd response."""
    return self.mh.receive_message()
  
  def unpack(self, response_raw, request):
    """Return an unpacked named tuple representation of a server response."""
    # Check for special cases
    if self.mh.unpack_request(request).type == 'kXR_open':
      open_helper = OpenHelper.OpenHelper(self.context)
      return open_helper.unpack_response(response_raw, request)
    else:
      return self.mh.unpack_response(response_raw, request)
    
  def do_full_handshake(self):
    """Perform handshake/protocol/login/auth/authmore sequence with default 
    values."""
    handshake_request = self.handshake()
    self.send(handshake_request)
    response_raw = self.receive()
    response = self.unpack(response_raw, handshake_request)
    print response
    
    protocol_request = self.kXR_protocol()
    self.send(protocol_request)
    response_raw = self.receive()
    response = self.unpack(response_raw, protocol_request)
    print response
    
    login_request = self.kXR_login()
    self.send(login_request)
    response_raw = self.receive()
    response = self.unpack(response_raw, login_request)
    sessid = response.sessid
    print response
    
    # Check if we need to auth
    if len(response.sec):
      auth_request = self.kXR_auth(authtoken=response.sec)
      self.send(auth_request)
      response_raw = self.receive()
      response = self.unpack(response_raw, auth_request)
      print response
    
      # Check if we need to authmore
      while response.status == XProtocol.XResponseType.kXR_authmore:
        print "More authentication needed, continuing"
        auth_request = self.kXR_auth(contcred=response[-1])
        self.send(auth_request)
        response_raw = self.receive()
        response = self.unpack(response_raw, auth_request)
        print response
      
    if response.status == XProtocol.XResponseType.kXR_ok:
      print "++++++ logged in successfully"
      return sessid
    else:
      print "++++++ login failed (%s): %s" % (response.status, 
                                              response.errmsg) 
  
  def handshake(self, first=None, second=None, third=None, fourth=None, 
                fifth=None):
    """Return a packed representation of a client handshake request."""
    request_struct = get_struct('ClientInitHandShake')    
    params = {'first'   : first   if first  else 0,
              'second'  : second  if second else 0, 
              'third'   : third   if third  else 0,
              'fourth'  : fourth  if fourth else 4,
              'fifth'   : fifth   if fifth  else 2012}
    return self.mh.build_message(request_struct, params)
  
  def kXR_admin(self):
    raise NotImplementedError()
    
  def kXR_auth(self, **kwargs):
    """Return a packed representation of a kXR_auth request. The default 
    request values can be individually modified by the optional keyword args."""
    auth = AuthHelper.AuthHelper(self.context)
    return auth.build_request(**kwargs)
    
  def kXR_bind(self, streamid=None, requestid=None, sessid=None, dlen=None):
    """Return a packed representation of a kXR_bind request."""
    request_struct = get_struct('ClientBindRequest')
    params = \
    {'streamid'  : streamid  if streamid   else self.context['streamid'],
     'requestid' : requestid if requestid  else get_requestid('kXR_bind'),
     'sessid'    : sessid    if sessid     else gen_sessid(),
     'dlen'      : dlen      if dlen       else 0}
    return self.mh.build_message(request_struct, params)   
  
  def kXR_chmod(self, streamid=None, requestid=None, reserved=None, mode=None,
                dlen=None, path=None):
    """Return a packed representation of a kXR_chmod request."""
    request_struct = get_struct('ClientChmodRequest')
    if not path: path = ''
    params = \
    {'streamid'  : streamid  if streamid   else self.context['streamid'],
     'requestid' : requestid if requestid  else get_requestid('kXR_chmod'),
     'reserved'  : reserved  if reserved   else (14 * '\0'),
     'mode'      : mode      if mode       else 0,
     'dlen'      : dlen      if dlen       else len(path),
     'path'      : path}
    return self.mh.build_message(request_struct, params) 
  
  def kXR_close(self):
    """Return a packed representation of a kXR_close request."""
    request_struct = get_struct('ClientCloseRequest')
  
  def kXR_dirlist(self, streamid=None, requestid=None, reserved=None, 
                  options=None, dlen=None, path=None):
    """Return a packed representation of a kXR_dirlist request."""
    request_struct = get_struct('ClientDirlistRequest')
    if not path: path = ''
    params = \
    {'streamid'  : streamid  if streamid   else self.context['streamid'],
     'requestid' : requestid if requestid  else get_requestid('kXR_dirlist'),
     'reserved'  : reserved  if reserved   else (15 * '\0'),
     'options'   : options   if options    else '\0',
     'dlen'      : dlen      if dlen       else len(path),
     'path'      : path}
    return self.mh.build_message(request_struct, params)
    
  def kXR_endsess(self, streamid=None, requestid=None, sessid=None, dlen=None):
    """Return a packed representation of a kXR_endsess request."""
    request_struct = get_struct('ClientEndsessRequest')
    params = \
    {'streamid'  : streamid  if streamid   else self.context['streamid'],
     'requestid' : requestid if requestid  else get_requestid('kXR_endsess'),
     'sessid'    : sessid    if sessid     else (16 * '\0'),
     'dlen'      : dlen      if dlen       else 0}
    return self.mh.build_message(request_struct, params)  
  
  def kXR_getfile(self):
    raise NotImplementedError()
    
  def kXR_locate(self, streamid=None, requestid=None, options=None, 
                 reserved=None, dlen=None, path=None):
    """Return a packed representation of a kXR_locate request."""
    request_struct = get_struct('ClientLocateRequest')
    if not path: path = ''
    params = \
    {'streamid'  : streamid  if streamid   else self.context['streamid'],
     'requestid' : requestid if requestid  else get_requestid('kXR_locate'),
     'options'   : options   if options    else 0,
     'reserved'  : reserved  if reserved   else (14 * '\0'),
     'dlen'      : dlen      if dlen       else len(path),
     'path'      : path}
    return self.mh.build_message(request_struct, params)
    
  def kXR_login(self, streamid=None, requestid=None, pid=None, username=None,
                    reserved=None, zone=None, capver=None, role=None, 
                    dlen=None):
    """Return a packed representation of a kXR_login request."""
    request_struct = get_struct('ClientLoginRequest')
    params = \
    {'streamid'  : streamid   if streamid   else self.context['streamid'],
     'requestid' : requestid  if requestid  else get_requestid('kXR_login'),
     'pid'       : pid        if pid        else os.getpid(),
     'username'  : username   if username   else ''.ljust(8, "\0"),
     'reserved'  : reserved   if reserved   else '\0',
     'zone'      : zone       if zone       else '\0',
     'capver'    : capver     if capver     else chr(XProtocol.XLoginCapVer
                                                     .kXR_asyncap \
                                                     | XProtocol.XLoginVersion
                                                     .kXR_ver003),
     'role'      : role       if role       else '0',
     'dlen'      : dlen       if dlen       else 0}   
    return self.mh.build_message(request_struct, params)
  
  def kXR_mkdir(self, streamid=None, requestid=None, options=None, 
                reserved=None, mode=None, dlen=None, path=None):
    """Return a packed representation of a kXR_mkdir request."""
    request_struct = get_struct('ClientMkdirRequest')
    if not path: path = ''
    params = \
    {'streamid'  : streamid  if streamid   else self.context['streamid'],
     'requestid' : requestid if requestid  else get_requestid('kXR_mkdir'),
     'options'   : options   if options    else '\0',
     'reserved'  : reserved  if reserved   else (13 * '\0'),
     'mode'      : mode      if mode       else 0,
     'dlen'      : dlen      if dlen       else len(path),
     'path'      : path}
    return self.mh.build_message(request_struct, params)
  
  def kXR_mv(self, streamid=None, requestid=None, reserved=None, dlen=None, 
             path=None):
    """Return a packed representation of a kXR_mv request."""
    request_struct = get_struct('ClientMvRequest')
    if not path: path = ''
    params = \
    {'streamid'  : streamid  if streamid   else self.context['streamid'],
     'requestid' : requestid if requestid  else get_requestid('kXR_mv'),
     'reserved'  : reserved  if reserved   else (16 * '\0'),
     'dlen'      : dlen      if dlen       else len(path),
     'path'      : path}
    return self.mh.build_message(request_struct, params)
  
  def kXR_open(self, streamid=None, requestid=None, mode=None, options=None, 
                reserved=None, dlen=None, path=None):
    """Return a packed representation of a kXR_open request."""
    request_struct = get_struct('ClientOpenRequest')
    if not path: path = ''
    params = \
    {'streamid'  : streamid  if streamid   else self.context['streamid'],
     'requestid' : requestid if requestid  else get_requestid('kXR_open'),
     'mode'      : mode      if mode       else 0,
     'options'   : options   if options    else 0,
     'reserved'  : reserved  if reserved   else (12 * '\0'),
     'dlen'      : dlen      if dlen       else len(path),
     'path'      : path}
    return self.mh.build_message(request_struct, params) 
    
  def kXR_ping(self, streamid=None, requestid=None, reserved=None, dlen=None):
    """Return a packed representation of a kXR_ping request."""
    request_struct = get_struct('ClientPingRequest')    
    params = \
    {'streamid'  : streamid  if streamid   else self.context['streamid'],
     'requestid' : requestid if requestid  else get_requestid('kXR_ping'),
     'reserved'  : reserved  if reserved   else (16 * "\0"),
     'dlen'      : dlen      if dlen       else 0}   
    return self.mh.build_message(request_struct, params)   
  
  def kXR_prepare(self):
    """Return a packed representation of a kXR_prepare request."""
    request_struct = get_struct('ClientPrepareRequest')
 
  def kXR_protocol(self, streamid=None, requestid=None, clientpv=None,
                   reserved=None, dlen=None):
    """Return a packed representation of a kXR_protocol request."""
    request_struct = get_struct('ClientProtocolRequest') 
    params = \
    {'streamid'  : streamid   if streamid   else self.context['streamid'],
     'requestid' : requestid  if requestid  else get_requestid('kXR_protocol'),
     'clientpv'  : clientpv   if clientpv   else XProtocol.XLoginVersion
                                                 .kXR_ver003,
     'reserved'  : reserved   if reserved   else (12 * "\0"),
     'dlen'      : dlen       if dlen       else 0}   
    return self.mh.build_message(request_struct, params)
  
  def kXR_putfile(self):
    """Return a packed representation of a kXR_putfile request."""
    request_struct = get_struct('ClientPutfileRequest')
    
  def kXR_query(self):
    """Return a packed representation of a kXR_query request."""
    request_struct = get_struct('ClientQueryRequest')
  
  def kXR_read(self):
    """Return a packed representation of a kXR_read request."""
    request_struct = get_struct('ClientReadRequest')
    
  def kXR_readv(self):
    """Return a packed representation of a kXR_readv request."""
    request_struct = get_struct('ClientReadVRequest')
  
  def kXR_rm(self):
    """Return a packed representation of a kXR_rm request."""
    request_struct = get_struct('ClientRmRequest')
  
  def kXR_rmdir(self):
    """Return a packed representation of a kXR_rmdir request."""
    request_struct = get_struct('ClientRmdirRequest')
    
  def kXR_set(self):
    """Return a packed representation of a kXR_set request."""
    request_struct = get_struct('ClientSetRequest')
  
  def kXR_stat(self, streamid=None, requestid=None, options=None, reserved=None,
               fhandle=None, dlen=None, path=None):
    """Return a packed representation of a kXR_stat request. The default 
    request values can be individually modified by the optional keyword args."""
    request_struct = get_struct('ClientStatRequest')   
    if not path: path = "/tmp"  
    params = \
    {'streamid'  : streamid   if streamid   else self.context['streamid'],
     'requestid' : requestid  if requestid  else get_requestid('kXR_stat'),
     'options'   : options    if options    else '0',
     'reserved'  : reserved   if reserved   else (11 * "\0"),
     'fhandle'   : fhandle    if fhandle    else (4 * "\0"),
     'dlen'      : dlen       if dlen       else len(path),
     'path'      : path}    
    return self.mh.build_message(request_struct, params)
  
  def kXR_statx(self):
    """Return a packed representation of a kXR_statx request."""
    request_struct = get_struct('ClientStatxRequest')
    
  def kXR_sync(self):
    """Return a packed representation of a kXR_sync request."""
    request_struct = get_struct('ClientSyncRequest')
    
  def kXR_truncate(self):
    """Return a packed representation of a kXR_truncate request."""
    request_struct = get_struct('ClientTruncateRequest')
  
  def kXR_verifyw(self):
    """Return a packed representation of a kXR_verifyw request."""
    request_struct = get_struct('ClientVerifywRequest')
    
  def kXR_write(self):
    """Return a packed representation of a kXR_write request."""
    request_struct = get_struct('ClientWriteRequest')


          
          
