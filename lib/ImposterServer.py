#-------------------------------------------------------------------------------
# Copyright (c) 2011-2012 by European Organization for Nuclear Research (CERN)
# Author: Justin Salmon <jsalmon@cern.ch>
# Refactored by Lukasz Janyst <ljanyst@cern.ch> (30.09.2013)
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

from Utils import getMessageStruct, genSessId, getResponseId, getAttnCode
from Utils import setupLogger

#-------------------------------------------------------------------------------
class ImposterServer:
  """Class to aid sending/receiving xrootd server messages."""

  #-----------------------------------------------------------------------------
  def __init__(self, context):
    self.context = context    
    self.mh = MessageHelper.MessageHelper(context)
    self.pending_request = None
    self.logger = setupLogger( __name__ )

  #-----------------------------------------------------------------------------
  def send(self, response):
    """Send a packed xrootd response."""
    self.mh.sendMessage(response)

  #-----------------------------------------------------------------------------
  def receive( self ):
    """Receive a request"""
    while True:
      request = self.mh.unpackRequest( self.mh.receiveMessage() )
      self.logger.info( 'Received request: %s' % (str(request)) )
      if request:
        yield request
      else:
        break

  #-----------------------------------------------------------------------------
  def close(self):
    """Close this server socket"""
    self.context['socket'].close()

  #-----------------------------------------------------------------------------
  def doFullHandshake( self, verifyAuth=False, handshakeFlag=None,
                       protocolFlags=None):
    """Perform handshake/protocol/login/auth/authmore sequence with default 
    values.

    If verify_auth is true, the credentials supplied by the client in the
    kXR_auth request will be properly authenticated, otherwise they will not
    be checked."""    
    for request in self.receive():
      #-------------------------------------------------------------------------
      # Send handshake + protocol at the same time
      #-------------------------------------------------------------------------
      if request.type == 'handshake':
        self.send( self.handshake(flag = handshakeFlag) +
                   self.kXR_protocol(flags = protocolFlags))

      #-------------------------------------------------------------------------
      # Handle login - if we don't need to handle authentication - that's it
      #-------------------------------------------------------------------------
      elif request.type == 'kXR_login':
        self.send(self.kXR_login(streamid=request.streamid))
        if not verifyAuth:
          break

      #-------------------------------------------------------------------------
      # Authenticate this request's credentials and potentially get
      # continuation (authmore) parameters
      #-------------------------------------------------------------------------
      elif request.type == 'kXR_auth':
        if verifyAuth:
          contparams = self.authenticate( request.cred )
          if contparams:
            response = self.kXR_authmore( streamid=request.streamid,
                                          data=contparams )
          else:
            response = self.kXR_ok(streamid=request.streamid)
        else:
          response = self.kXR_ok(streamid=request.streamid)

        self.send(response)
        #-----------------------------------------------------------------------
        # If we have contparams, there will be more auth-related requests 
        # to receive at this stage. Otherwise, break here and let the 
        # scenario deal with the next request.
        #-----------------------------------------------------------------------
        if not contparams: break

  #-----------------------------------------------------------------------------
  def authenticate(self, cred):
    """Authenticate the given credentials.""" 
    authHelper = AuthHelper.AuthHelper( self.context )
    return authHelper.auth(cred)

  #-----------------------------------------------------------------------------
  def handshake( self, streamid=None, status=None, dlen=None, pval=None,
                 flag=None ):
    """Return a packed representation of a server handshake response."""
    responseStruct = getMessageStruct('ServerResponseHeader') \
                   + getMessageStruct('ServerInitHandShake')
    params = {
      'streamid': streamid  if streamid else 0,
      'status'  : status    if status   else 0,
      'dlen'    : dlen      if dlen     else 8,
      'pval'    : pval      if pval is not None else XProtocol.kXR_PROTOCOLVERSION,
      'flag'    : flag      if flag is not None else XProtocol.kXR_DataServer }
    return self.mh.buildMessage(responseStruct, params)

  #-----------------------------------------------------------------------------
  def kXR_bind( self, streamid=None, status=None, dlen=None, pathid=None ):
    """Return a packed representation of a kXR_bind response.""" 
    responseStruct = getMessageStruct('ServerResponseHeader') + \
                     getMessageStruct('ServerResponseBody_Bind')
    params = {
      'streamid': streamid  if streamid else 0,
      'status'  : status    if status   else getResponseId('kXR_ok'),
      'dlen'    : dlen      if dlen     else 1,
      'pathid'  : pathid    if pathid   else '\0'}
    return self.mh.buildMessage(responseStruct, params)

  #-----------------------------------------------------------------------------
  def kXR_dirlist( self, streamid=None, status=None, dlen=None, data=None,
                   entries=None):
    """Return a packed representation of a kXR_dirlist response.""" 
    if entries != None:
      data = '\n'.join( entries )
    return self.kXR_ok(streamid, status, dlen, data)

  #-----------------------------------------------------------------------------
  def kXR_locate( self, streamid=None, status=None, dlen=None, data=None,
                  locations=None):
    """Return a packed representation of a kXR_locate response.""" 
    if locations != None:
      data = ' '.join( locations )
    return self.kXR_ok( streamid, status, dlen, data )

  #-----------------------------------------------------------------------------
  def kXR_login(self, streamid=None, status=None, dlen=None, sessid=None,
            sec=None, verifyAuth=False):
    """Return a packed representation of a kXR_login response.
       
       Pass verify_auth=True to enable authentication."""
    responseStruct = getMessageStruct('ServerResponseHeader') + \
                     getMessageStruct('ServerResponseBody_Login')
    # Check if client needs to authenticate
    if verifyAuth and not sec:
      auth = AuthHelper.AuthHelper(self.context) 
      sec = auth.getsectoken()

    params = {
      'streamid': streamid  if streamid else 0,
      'status'  : status    if status   else getResponseId('kXR_ok'),
      'dlen'    : dlen      if dlen     else 0,
      'sessid'  : sessid    if sessid   else genSessId() }

    toBeRemoved = []

    if sec != None:
      params['sec'] = sec
      self.mh.setFieldAttribute( responseStruct, 'sec', 'size', len( sec ) )
    else:
      responseStruct = self.mh.removeFields( responseStruct, ['sec'] )

    msg = self.mh.buildMessageFormat( responseStruct, params )
    msg[1][2] = msg[2] - 8

    return self.mh.pack( msg[0], msg[1] )

  #-----------------------------------------------------------------------------
  def kXR_open(self, streamid=None, status=None, dlen=None, fhandle=None,
               cpsize=None , cptype=None, data=None):
    """Return a packed representation of a kXR_open response."""

    responseStruct = getMessageStruct('ServerResponseHeader') + \
                     getMessageStruct('ServerResponseBody_Open')
    params = {
        'streamid': streamid  if streamid else 0,
        'status':   status    if status   else getResponseId('kXR_ok'),
        'dlen':     0,
        'fhandle':  fhandle   if fhandle  else (4 * '\0') }

    toBeRemoved = []

    if cpsize != None: params['cpsize'] = cpsize
    else: toBeRemoved.append('cpsize')

    if cptype != None: params['cptype'] = cptype
    else: toBeRemoved.append('cptype')

    if data != None:
        params['data'] = data
        self.mh.setFieldAttribute( responseStruct, 'data', 'size', len( data ) )
    else: toBeRemoved.append('data')

    responseStruct = self.mh.removeFields( responseStruct, toBeRemoved )

    msg = self.mh.buildMessageFormat( responseStruct, params )
    msg[1][2] = msg[2] - 8

    return self.mh.pack( msg[0], msg[1] )

  #-----------------------------------------------------------------------------
  def kXR_protocol(self, streamid=None, status=None, dlen=None, pval=None, 
               flags=None):
    """Return a packed representation of a kXR_protocol response.""" 

    responseStruct = getMessageStruct('ServerResponseHeader') + \
                    getMessageStruct('ServerResponseBody_Protocol')
    params = {
      'streamid': streamid  if streamid else 0,
      'status'  : status    if status   else getResponseId('kXR_ok'),
      'dlen'    : dlen      if dlen     else 8,
      'pval'    : pval      if pval     else XProtocol.kXR_PROTOCOLVERSION,
      'flags'   : flags     if flags    else XProtocol.kXR_isServer}
    return self.mh.buildMessage(responseStruct, params)

  #-----------------------------------------------------------------------------
  def kXR_query(self, streamid=None, status=None, dlen=None, data=None):
    """Return a packed representation of a kXR_query response.""" 
    return self.kXR_ok(streamid, status, dlen, data)

  #-----------------------------------------------------------------------------
  def kXR_read( self, streamid=None, status=None, dlen=None, data=None ):
    """Return a packed representation of a kXR_read response."""
    return self.kXR_ok(streamid, status, dlen, data)

  #-----------------------------------------------------------------------------
  def kXR_readv( self, streamid=None, status=None, dlen=None, data=None,
                 chunks = None ):
    """
    Return a packed representation of a kXR_readv response.

    chunks is a list of 4-tuples of the following format:
    (fhandle, length, offset, data)
    """

    if chunks != None:
      headerFormat = self.mh.getMessageFormat( getMessageStruct( 'read_list' ) )
      data = ''
      for chunk in chunks:
        data += self.mh.pack( headerFormat, (chunk[0], chunk[1], chunk[2]) )
        data += chunk[3]

    return self.kXR_ok( streamid, status, dlen, data )

  #-----------------------------------------------------------------------------
  def kXR_set(self, streamid=None, status=None, dlen=None, data=None):
    """Return a packed representation of a kXR_set response.""" 
    return self.kXR_ok(streamid, status, dlen, data)

  #-----------------------------------------------------------------------------
  def kXR_stat(self, streamid=None, status=None, dlen=None, data=None):
    """Return a packed representation of a kXR_stat response."""
    return self.kXR_ok(streamid, status, dlen, data)

  #=============================================================================
  # Generic server responses
  #=============================================================================
  def kXR_attn_asyncab(self, streamid=None, status=None, dlen=None, actnum=None, 
                       msg=None):
    """Return a packed representation of a kXR_attn_asyncab response."""
    responseStruct = getMessageStruct('ServerResponseHeader') + \
                     getMessageStruct('ServerResponseBody_Attn')
    if not msg: msg = ''
    params = {
      'streamid': streamid  if streamid else 0,
      'status'  : status    if status   else getResponseId('kXR_attn'),
      'dlen'    : dlen      if dlen     else len(msg) + 4,
      'actnum'  : actnum    if actnum   else get_attncode('kXR_asyncab'),
      'parms'   : msg}
    return self.mh.buildMessage(responseStruct, params)

  def kXR_attn_asyncdi(self, streamid=None, status=None, dlen=None, actnum=None, 
                       wsec=None, msec=None):
    """Return a packed representation of a kXR_attn_asyncdi response."""
    response_struct = getMessageStruct('ServerResponseHeader') + \
                      getMessageStruct('ServerResponseBody_Attn_asyncdi')
    params = {
      'streamid': streamid  if streamid else 0,
      'status'  : status    if status   else getResponseId('kXR_attn'),
      'dlen'    : dlen      if dlen     else 12,
      'actnum'  : actnum    if actnum   else get_attncode('kXR_asyncdi'),
      'wsec'    : wsec      if wsec     else 0,
      'msec'    : msec      if msec     else 0}
    return self.mh.buildMessage(responseStruct, params)

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
    responseStruct = getMessageStruct('ServerResponseHeader') + \
                      getMessageStruct('ServerResponseBody_Attn_asyncrd')
    if not host: host = ''
    else: host += (token if token else '')
    params = {
      'streamid': streamid  if streamid else 0,
      'status'  : status    if status   else getResponseId('kXR_attn'),
      'dlen'    : dlen      if dlen     else len(host),
      'actnum'  : actnum    if actnum   else get_attncode('kXR_asyncrd'),
      'port'    : port      if port     else 0,
      'host'    : host}
    return self.mh.buildMessage(responseStruct, params)

  #-----------------------------------------------------------------------------
  def kXR_attn_asynresp(self, payloadLength):
    """Return a packed representation of a kXR_attn_asynresp response."""

    responseStruct = getMessageStruct('ServerResponseHeader') + \
                     getMessageStruct('ServerResponseBody_Attn') + \
                     getMessageStruct('ServerResponseBody_Attn_asynresp')
    params = {
      'streamid': 0,
      'status'  : getResponseId('kXR_attn'),
      'dlen'    : payloadLength + 8,
      'actnum'  : getAttnCode('kXR_asynresp'),
      'reserved': 4 * '\0' }
    return self.mh.buildMessage(responseStruct, params)

  def kXR_attn_asyncwt(self, streamid=None, status=None, dlen=None, actnum=None, 
                       wsec=None):
    """Return a packed representation of a kXR_attn_asyncwt response."""
    responseStruct = getMessageStruct('ServerResponseHeader') + \
                      getMessageStruct('ServerResponseBody_Attn_asyncwt')
    params = {
      'streamid': streamid  if streamid else 0,
      'status'  : status    if status   else getResponseId('kXR_attn'),
      'dlen'    : dlen      if dlen     else 8,
      'actnum'  : actnum    if actnum   else get_attncode('kXR_asyncwt'),
      'wsec'    : wsec      if wsec     else 0}
    return self.mh.buildMessage(responseStruct, params)

  def kXR_authmore(self, streamid=None, status=None, dlen=None, data=None):
    """Return a packed representation of a kXR_authmore response."""
    if not status: status = getResponseId('kXR_authmore')
    return self.kXR_ok(streamid, status, dlen, data)

  def kXR_error(self, streamid=None, status=None, dlen=None, errnum=None,
                errmsg=None):
    """Return a packed representation of a kXR_error response."""
    responseStruct = getMessageStruct('ServerResponseHeader') + \
                     getMessageStruct('ServerResponseBody_Error')
    if not errmsg: errmsg = ''
    if not errnum: errnum = XProtocol.XErrorCode.kXR_ArgInvalid
    params = {
      'streamid': streamid  if streamid else 0,
      'status'  : status    if status   else getResponseId('kXR_error'),
      'dlen'    : dlen      if dlen     else len(errmsg + str(errnum)),
      'errnum'  : errnum,
      'errmsg'  : errmsg}

    self.mh.setFieldAttribute( responseStruct, 'errmsg', 'size', len(errmsg) )
    return self.mh.buildMessage(responseStruct, params)

  #-----------------------------------------------------------------------------
  def kXR_ok(self, streamid=None, status=None, dlen=None, data=None):
    """Return a packed representation of a kXR_ok response."""
    responseStruct = getMessageStruct('ServerResponseHeader') + \
                     getMessageStruct('ServerResponseBody_Buffer')

    if not data: data = ''

    params = {
      'streamid': streamid  if streamid else 0,
      'status'  : status    if status   else getResponseId('kXR_ok'),
      'dlen'    : dlen      if dlen     else len(data),
      'data'    : data }

    self.mh.setFieldAttribute( responseStruct, 'data', 'size', len( data ) )

    return self.mh.buildMessage(responseStruct, params)

  #-----------------------------------------------------------------------------
  def kXR_oksofar(self, streamid=None, status=None, dlen=None, data=None):
    """Return a packed representation of a kXR_oksofar response."""
    status = getResponseId('kXR_oksofar')
    return self.kXR_ok(streamid, status, dlen, data)

  #-----------------------------------------------------------------------------
  def kXR_redirect(self, streamid=None, status=None, dlen=None, port=None,
                   host=None, opaque=None, token=None):
    """Return a packed representation of a kXR_redirect response."""
    responseStruct = getMessageStruct('ServerResponseHeader') + \
                     getMessageStruct('ServerResponseBody_Redirect')
    if not host: host = ''
    else: host += (opaque if opaque else '') + (token if token else '')
    params = {
      'streamid': streamid  if streamid else 0,
      'status'  : status    if status   else getResponseId('kXR_redirect'),
      'dlen'    : dlen      if dlen     else len(host) + 4,
      'port'    : port      if port     else 0,
      'host'    : host      if host     else r''}

    self.mh.setFieldAttribute( responseStruct, 'host', 'size', len(host) )

    return self.mh.buildMessage(responseStruct, params)

  def kXR_wait(self, streamid=None, status=None, dlen=None, seconds=None,
               infomsg=None):
    """Return a packed representation of a kXR_wait response."""
    responseStruct = getMessageStruct('ServerResponseHeader') + \
                     getMessageStruct('ServerResponseBody_Wait')
    if not infomsg: infomsg = ''
    params = {
      'streamid': streamid  if streamid else 0,
      'status'  : status    if status   else getResponseId('kXR_wait'),
      'dlen'    : dlen      if dlen     else len(infomsg) + 4,
      'seconds' : seconds   if seconds  else 0,
      'infomsg' : infomsg}

    self.mh.setFieldAttribute( responseStruct, 'infomsg', 'size', len( infomsg ) )

    return self.mh.buildMessage(responseStruct, params)

  def kXR_waitresp(self, streamid=None, status=None, dlen=None, seconds=None):
    """Return a packed representation of a kXR_waitresp response."""
    responseStruct = getMessageStruct('ServerResponseHeader') + \
                     getMessageStruct('ServerResponseBody_Waitresp')
    params = {
      'streamid': streamid  if streamid else 0,
      'status'  : status    if status   else getResponseId('kXR_waitresp'),
      'dlen'    : dlen      if dlen     else 4,
      'seconds' : seconds   if seconds  else 0}
    return self.mh.buildMessage(responseStruct, params)

