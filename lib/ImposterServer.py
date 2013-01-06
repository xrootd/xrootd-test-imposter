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

import XProtocol
import MessageHelper
import AuthHelper

from Utils import get_struct, gen_sessid, get_responseid, get_attncode

      
class ImposterServer:
  """Class to aid sending/receiving xrootd server messages."""
  
  def __init__(self, context):
    self.context = context    
    self.mh = MessageHelper.MessageHelper(context)
    
  def send(self, response):
    """Send a packed xrootd response."""
    self.mh.send_message(response)
  
  def receive(self):
    """Receive a packed xrootd request (iterable generator method)"""
    while True:
      request = self.unpack(self.mh.receive_message())
      if request:
        yield request
      else: break
      
  def close(self):
    """Close this server socket"""
    self.context['socket'].close()
    
  def unpack(self, request_raw):
    """Return an unpacked named tuple representation of a client request."""
    return self.mh.unpack_request(request_raw)
    
  def do_full_handshake(self, verify_auth=False):
    """Perform handshake/protocol/login/auth/authmore sequence with default 
    values.
    
    If verify_auth is true, the credentials supplied by the client in the
    kXR_auth request will be properly authenticated, otherwise they will not
    be checked."""    
    for request in self.receive():
      
      if request.type == 'handshake':
        print request
        # Send handshake + protocol at the same time
        self.send(self.handshake() 
                  + self.kXR_protocol(streamid=request.streamid))
      
      elif request.type == 'kXR_login':
        print request
        self.send(self.kXR_login(streamid=request.streamid))
        
      elif request.type == 'kXR_auth':
        
        if verify_auth:
          # Authenticate this request's credentials and potentially get
          # continuation (authmore) parameters
          contparams = self.authenticate(request.cred)
          if contparams:
            # Send an authmore if necessary
            response = self.kXR_authmore(streamid=request.streamid, 
                                         data=contparams)
          else:
            # We are done authenticating
            response = self.kXR_ok(streamid=request.streamid)
        
        else:
          # Not checking the credentials
          response = self.kXR_ok(streamid=request.streamid)
        
        self.send(response)
        # If we have contparams, there will be more auth-related requests 
        # to receive at this stage. Otherwise, break here and let the 
        # scenario deal with the next request.
        if not contparams: break
        
  def authenticate(self, cred):
    """Authenticate the given credentials.""" 
    auth_helper = AuthHelper.AuthHelper(self.context)
    return auth_helper.auth(cred)
  
  #=============================================================================
  # Specific server responses
  #=============================================================================
  
  def handshake(self, streamid=None, status=None, dlen=None, protover=None,
                msgval=None):
    """Return a packed representation of a server handshake response."""
    response_struct = get_struct('ServerResponseHeader') \
                    + get_struct('ServerInitHandShake')
    params = \
    {'streamid': streamid  if streamid else 0,
     'status'  : status    if status   else 0,
     'dlen'    : dlen      if dlen     else 8,
     'protover': protover  if protover else 663,
     'msgval'  : msgval    if msgval   else 1}
    return self.mh.build_message(response_struct, params)
  
  def kXR_admin(self):
    raise NotImplementedError()
  
  def kXR_bind(self, streamid=None, status=None, dlen=None, pathid=None):
    """Return a packed representation of a kXR_bind response.""" 
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Bind')
    params = \
    {'streamid': streamid  if streamid else 0,
     'status'  : status    if status   else get_responseid('kXR_ok'),
     'dlen'    : dlen      if dlen     else 1,
     'pathid'  : pathid    if pathid   else '\0'}
    return self.mh.build_message(response_struct, params)
  
  def kXR_dirlist(self, streamid=None, status=None, dlen=None, data=None):
    """Return a packed representation of a kXR_dirlist response.""" 
    return self.kXR_ok(streamid, status, dlen, data)
  
  def kXR_getfile(self):
    raise NotImplementedError()
  
  def kXR_locate(self, streamid=None, status=None, dlen=None, data=None):
    """Return a packed representation of a kXR_locate response.""" 
    return self.kXR_ok(streamid, status, dlen, data)
  
  def kXR_login(self, streamid=None, status=None, dlen=None, sessid=None,
            sec=None):
    """Return a packed representation of a kXR_login response."""
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Login')              
    # Check if client needs to authenticate
    auth = AuthHelper.AuthHelper(self.context) 
    if not sec:
      sec = auth.getsectoken()
                      
    params = \
    {'streamid': streamid  if streamid else 0,
     'status'  : status    if status   else get_responseid('kXR_ok'),
     'dlen'    : dlen      if dlen     else len(sec) + 16,
     'sessid'  : sessid    if sessid   else gen_sessid(),
     'sec'     : sec}
    return self.mh.build_message(response_struct, params)
  
  def kXR_open(self, streamid=None, status=None, dlen=None, fhandle=None,
               cpsize=None, cptype=None, info=None):
    """Return a packed representation of a kXR_open response.""" 
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Open')
    params = \
    {'streamid': streamid  if streamid else 0,
     'status'  : status    if status   else get_responseid('kXR_ok'),
     'dlen'    : 0,
     'fhandle' : fhandle   if fhandle  else (4 * '\0'),
     'cpsize'  : cpsize    if cpsize   else 0,
     'cptype'  : cptype    if cptype   else (4 * '\0'),
     'info'    : info      if info     else ''}
    if not cpsize: del response_struct[4]; del params['cpsize']
    if not cptype: del response_struct[4]; del params['cptype']
    if not info:   del response_struct[4]; del params['info']
    if not dlen: 
      dlen = 4 + (len(cpsize) if cpsize else 0) \
               + (len(cptype) if cptype else 0) \
               + (len(info)   if info   else 0)
    params['dlen'] = dlen
    return self.mh.build_message(response_struct, params)
  
  def kXR_prepare(self, streamid=None, status=None, dlen=None, data=None):
    """Return a packed representation of a kXR_prepare response.""" 
    return self.kXR_ok(streamid, status, dlen, data)
    
  def kXR_protocol(self, streamid=None, status=None, dlen=None, pval=None, 
               flags=None):
    """Return a packed representation of a kXR_protocol response.""" 
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Protocol')
    params = \
    {'streamid': streamid  if streamid else 0,
     'status'  : status    if status   else get_responseid('kXR_ok'),
     'dlen'    : dlen      if dlen     else 8,
     'pval'    : pval      if pval     else XProtocol.kXR_PROTOCOLVERSION,
     'flags'   : flags     if flags    else XProtocol.kXR_isServer}
    return self.mh.build_message(response_struct, params)
  
  def kXR_putfile(self):
    raise NotImplementedError()
  
  def kXR_query(self, streamid=None, status=None, dlen=None, data=None):
    """Return a packed representation of a kXR_query response.""" 
    return self.kXR_ok(streamid, status, dlen, data)
  
  def kXR_read(self, streamid=None, status=None, dlen=None, data=None):
    """Return a packed representation of a kXR_read response.""" 
    return self.kXR_ok(streamid, status, dlen, data)
  
  def kXR_readv(self, streamid=None, status=None, dlen=None, data=None):
    """Return a packed representation of a kXR_readv response.""" 
    return self.kXR_ok(streamid, status, dlen, data)
  
  def kXR_set(self, streamid=None, status=None, dlen=None, data=None):
    """Return a packed representation of a kXR_set response.""" 
    return self.kXR_ok(streamid, status, dlen, data)
  
  def kXR_stat(self, streamid=None, status=None, dlen=None, data=None, id=None,
           size=None, flags=None, modtime=None):
    """Return a packed representation of a kXR_stat response."""                       
    if not data:
      data = (x for x in (id, size, flags, modtime) if x is not None)
      data = ' '.join([str(param) for param in data])
    return self.kXR_ok(streamid, status, dlen, data)
  
  def kXR_statx(self, streamid=None, status=None, dlen=None, data=None):
    """Return a packed representation of a kXR_statx response.""" 
    return self.kXR_ok(streamid, status, dlen, data)
  
  #=============================================================================
  # Generic server responses
  #=============================================================================
  
  def kXR_attn_asyncab(self, streamid=None, status=None, dlen=None, actnum=None, 
                       msg=None):
    """Return a packed representation of a kXR_attn_asyncab response."""
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Attn')
    if not msg: msg = ''
    params = \
    {'streamid': streamid  if streamid else 0,
     'status'  : status    if status   else get_responseid('kXR_attn'),
     'dlen'    : dlen      if dlen     else len(msg) + 4,
     'actnum'  : actnum    if actnum   else get_attncode('kXR_asyncab'),
     'parms'   : msg}
    return self.mh.build_message(response_struct, params)
  
  def kXR_attn_asyncdi(self, streamid=None, status=None, dlen=None, actnum=None, 
                       wsec=None, msec=None):
    """Return a packed representation of a kXR_attn_asyncdi response."""
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Attn_asyncdi')
    params = \
    {'streamid': streamid  if streamid else 0,
     'status'  : status    if status   else get_responseid('kXR_attn'),
     'dlen'    : dlen      if dlen     else 12,
     'actnum'  : actnum    if actnum   else get_attncode('kXR_asyncdi'),
     'wsec'    : wsec      if wsec     else 0,
     'msec'    : msec      if msec     else 0}
    return self.mh.build_message(response_struct, params)
  
  def kXR_attn_asyncgo(self, streamid=None, status=None, dlen=None, 
                       actnum=None):
    """Return a packed representation of a kXR_attn_asyncgo response."""
    if not actnum: actnum = get_attncode('kXR_asyncgo')
    return self.kXR_attn_asyncab(streamid, status, dlen, actnum, None)
  
  def kXR_attn_asyncms(self, streamid=None, status=None, dlen=None, actnum=None,
                       msg=None):
    """Return a packed representation of a kXR_attn_asyncms response."""
    if not actnum: actnum = get_attncode('kXR_asyncms')
    return self.kXR_attn_asyncab(streamid, status, dlen, actnum, msg)
  
  def kXR_attn_asyncrd(self, streamid=None, status=None, dlen=None, actnum=None,
                       port=None, host=None, token=None):
    """Return a packed representation of a kXR_attn_asyncrd response."""
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Attn_asyncrd')
    if not host: host = ''
    else: host += (token if token else '')
    params = \
    {'streamid': streamid  if streamid else 0,
     'status'  : status    if status   else get_responseid('kXR_attn'),
     'dlen'    : dlen      if dlen     else len(host),
     'actnum'  : actnum    if actnum   else get_attncode('kXR_asyncrd'),
     'port'    : port      if port     else 0,
     'host'    : host}
    return self.mh.build_message(response_struct, params)
  
  def kXR_attn_asynresp(self, streamid=None, status=None, dlen=None, 
                        actnum=None, reserved=None, rstreamid=None,
                        rstatus=None, rlen=None, rdata=None):
    """Return a packed representation of a kXR_attn_asynresp response."""
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Attn_asynresp')
    if not rdata: rdata = ''
    params = \
    {'streamid': streamid  if streamid  else 0,
     'status'  : status    if status    else get_responseid('kXR_attn'),
     'dlen'    : dlen      if dlen      else len(rdata) + 16,
     'actnum'  : actnum    if actnum    else get_attncode('kXR_asynresp'),
     'reserved': reserved  if reserved  else (4 * '\0'),
     'rsid'    : rstreamid if rstreamid else 0,
     'rstatus' : rstatus   if rstatus   else get_responseid('kXR_ok'),
     'rlen'    : rlen      if rlen      else len(rdata),
     'rdata'   : rdata}
    return self.mh.build_message(response_struct, params)
  
  def kXR_attn_asyncwt(self, streamid=None, status=None, dlen=None, actnum=None, 
                       wsec=None):
    """Return a packed representation of a kXR_attn_asyncwt response."""
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Attn_asyncwt')
    params = \
    {'streamid': streamid  if streamid else 0,
     'status'  : status    if status   else get_responseid('kXR_attn'),
     'dlen'    : dlen      if dlen     else 8,
     'actnum'  : actnum    if actnum   else get_attncode('kXR_asyncwt'),
     'wsec'    : wsec      if wsec     else 0}
    return self.mh.build_message(response_struct, params)
  
  def kXR_authmore(self, streamid=None, status=None, dlen=None, data=None):
    """Return a packed representation of a kXR_authmore response."""
    if not status: status = get_responseid('kXR_authmore')
    return self.kXR_ok(streamid, status, dlen, data)

  def kXR_error(self, streamid=None, status=None, dlen=None, errnum=None,
                errmsg=None):
    """Return a packed representation of a kXR_error response."""
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Error')
    if not errmsg: errmsg = ''
    if not errnum: errnum = XProtocol.XErrorCode.kXR_ArgInvalid
    params = \
    {'streamid': streamid  if streamid else 0,
     'status'  : status    if status   else get_responseid('kXR_error'),
     'dlen'    : dlen      if dlen     else len(errmsg + str(errnum)),
     'errnum'  : errnum,
     'errmsg'  : errmsg}
    return self.mh.build_message(response_struct, params)

  def kXR_ok(self, streamid=None, status=None, dlen=None, data=None):
    """Return a packed representation of a kXR_ok response."""
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Buffer')
    if not data: data = ''
    params = \
    {'streamid': streamid  if streamid else 0,
     'status'  : status    if status   else get_responseid('kXR_ok'),
     'dlen'    : dlen      if dlen     else len(data),
     'data'    : data}
    return self.mh.build_message(response_struct, params)
  
  def KXR_oksofar(self, streamid=None, status=None, dlen=None, data=None):
    """Return a packed representation of a kXR_oksofar response."""
    status = get_responseid('kXR_oksofar')
    return self.kXR_ok(streamid, status, dlen, data)
  
  def kXR_redirect(self, streamid=None, status=None, dlen=None, port=None,
                   host=None, opaque=None, token=None):
    """Return a packed representation of a kXR_redirect response."""
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Redirect')
    if not host: host = ''
    else: host += (opaque if opaque else '') + (token if token else '')
    params = \
    {'streamid': streamid  if streamid else 0,
     'status'  : status    if status   else get_responseid('kXR_redirect'),
     'dlen'    : dlen      if dlen     else len(host) + 4,
     'port'    : port      if port     else 0,
     'host'    : host      if host     else r''}
    return self.mh.build_message(response_struct, params)
  
  def kXR_wait(self, streamid=None, status=None, dlen=None, seconds=None,
               infomsg=None):
    """Return a packed representation of a kXR_wait response."""
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Wait')
    if not infomsg: infomsg = ''
    params = \
    {'streamid': streamid  if streamid else 0,
     'status'  : status    if status   else get_responseid('kXR_wait'),
     'dlen'    : dlen      if dlen     else len(infomsg) + 4,
     'seconds' : seconds   if seconds  else 0,
     'infomsg' : infomsg}
    return self.mh.build_message(response_struct, params)
  
  def kXR_waitresp(self, streamid=None, status=None, dlen=None, seconds=None):
    """Return a packed representation of a kXR_waitresp response."""
    response_struct = get_struct('ServerResponseHeader') + \
                      get_struct('ServerResponseBody_Waitresp')
    params = \
    {'streamid': streamid  if streamid else 0,
     'status'  : status    if status   else get_responseid('kXR_waitresp'),
     'dlen'    : dlen      if dlen     else 4,
     'seconds' : seconds   if seconds  else 0}
    return self.mh.build_message(response_struct, params)
    
  
  