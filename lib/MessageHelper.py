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
import socket
import logging

from struct import error
from collections import namedtuple
from Utils import flatten, struct_format, formatLength, getRequestId, \
                  getResponseId, getMessageStruct, get_attncode
import Utils

import XProtocol

#-------------------------------------------------------------------------------
class MessageException( Exception ):
  def __init__( self, value ):
    self.value = value

  def __str__( self ):
    return repr( self.value )

#-------------------------------------------------------------------------------
class MessageHelper:

  #-----------------------------------------------------------------------------
  def __init__(self, context):
    self.sock   = context['socket']
    self.logger = Utils.setupLogger( __name__ )

  #-----------------------------------------------------------------------------
  def getMessageFormat( self, messageStruct ):
    format = '>'

    for member in messageStruct:
      if member.has_key('size'):
        format += str( member['size'] )
      format += member['type']
    self.logger.debug( 'Pack format is %s' % (format) )
    return format

  #-----------------------------------------------------------------------------
  def buildMessageFormat( self, messageStruct, params ):
    """
    Builds message format, calculates the total size of the resulting
    message and sorts the parameters for packing.

    returns a 3-tuple with message format, parameter tuple, and size of the
    resulting message
    """

    if not len(params) == len(messageStruct):
      self.logger.error( "Build Message: wrong number of parameters" )
      self.logger.error( "messageStruct (%d): %s" % (len(messageStruct), messageStruct) )
      self.logger.error( "params (%d):        %s" % (len(params), params) )
      raise MessageException( "Wrong number of parameters" )

    messageData = []
    format = '>'

    for member in messageStruct:
      messageData += (params[member['name']],)
      if member.has_key('size'):
        format += str( member['size'] )
      format += member['type']

    msgSize = struct.calcsize( format )
    self.logger.debug( 'Pack format is %s, params are: %s, size: %d' %
                       (format, str(messageData), msgSize) )
    return (format, messageData, msgSize)

  #-----------------------------------------------------------------------------
  # to be removed
  def buildMessage( self, messageStruct, params ):
    """Return a packed representation of the given params mapped onto
    the given message struct."""

    #---------------------------------------------------------------------------
    if not len(params) == len(messageStruct):
      self.logger.error( "Build Message: wrong number of parameters" )
      self.logger.error( "messageStruct (%d): %s" % (len(messageStruct), messageStruct) )
      self.logger.error( "params (%d):        %s" % (len(params), params) )
      raise MessageException( "Wrong number of parameters" )

    messageData = []
    format = '>'

    for member in messageStruct:
      messageData += (params[member['name']],)
      if member.has_key('size'):
        format += str( member['size'] )
      format += member['type']

    messageData = tuple(messageData)
    self.logger.debug( 'Pack format is %s, params are: %s' % (format, str(messageData)) )
    return self.pack(format, messageData)

  #-----------------------------------------------------------------------------
  def setFieldAttribute( self, messageStruct, fieldName, attrName, attrVal ):
    attrSet = False
    for f in messageStruct:
      if f['name'] != fieldName:
        continue
      f[attrName] = attrVal
      attrSet = True
    if not attrSet:
      msg = 'Attribute: ' + attrName + ' of field: ' + fieldName + ' not found'
      raise MessageException( msg )

  #-----------------------------------------------------------------------------
  def removeFields( self, messageStruct, toBeRemoved ):
    return [f for f in messageStruct if f['name'] not in toBeRemoved]

  #-----------------------------------------------------------------------------
  def sendMessage(self, message):
    """Send a packed binary message."""
    try:
      self.logger.debug( "Message size: %s" % (len(message)) )
      self.sock.send(message)
    except socket.error, e:
      raise MessageException( str(e) )

  #-----------------------------------------------------------------------------
  def isHandShake( self, message ):
    """Check if the message is a handshake"""
    if len( message ) != 20:
      return false
    decodedMsg = struct.unpack( ">iiiii", message )
    return decodedMsg == ( 0, 0, 0, 4, 2012 )

  #-----------------------------------------------------------------------------
  def readBytes( self, numBytes ):
    """Get bytes from the socket"""
    message   = str()
    bytesLeft = numBytes
    while bytesLeft:
      msg       = self.sock.recv( bytesLeft )
      # python's way of saying a connection is broken
      if msg == '':
        raise MessageException( 'Connection closed by peer' )
      message   += msg
      bytesLeft -= len( msg )
    return message

  #-----------------------------------------------------------------------------
  def receiveMessage( self ):
    """Receive a client message from the connection socket"""
    try:
      message = self.readBytes( 20 )
      if self.isHandShake( message ):
        self.logger.debug( 'Received XRootD client handshake' )
        return message
      payloadLenMsg = self.readBytes( 4 )
      message += payloadLenMsg
      payloadLen = struct.unpack( ">i", payloadLenMsg )

      self.logger.debug( 'Received message header, payload size: %d' %
                         (payloadLen) )

      message += self.readBytes( payloadLen[0] )
      self.logger.debug( 'Received message message of size: %d' %
                         (len(message)) )

    except socket.error, e:
      self.logger.error( 'Error receiving message: %s' % e )
      raise MessageException( str(e) )

    return message

  #-----------------------------------------------------------------------------
  def unpack_response(self, response_raw, request_raw):
    """Return an unpacked named tuple representation of a server response."""
    if not len(response_raw):
      return ''

    # Unpack the request that generated this response for reference
    request = self.unpack_request(request_raw)[0]
    requestid = get_requestid(request.type)

    # Unpack the response header to find the status and data length
    header_struct = getMessageStruct('ServerResponseHeader')
    format = '>'
    for member in header_struct:
      format += member['type']
    header = self.unpack(format + (str(len(response_raw) - 8) + 's'),
                         response_raw)
    streamid = header[0]
    status = header[1]
    dlen = header[2]
    body = header[-1]

    # Check if this is a handshake response
    if requestid == XProtocol.XRequestTypes.handshake:
      body_struct = getMessageStruct('ServerInitHandShake')
    # Check if this is an asynchronous response
    elif status == XProtocol.XResponseType.kXR_attn:
      # Extract the attn code
      attncode = self.unpack('>H', body[:2])[0]
      body_struct = getMessageStruct('ServerResponseBody_Attn_' \
                               + get_attncode(attncode)[4:])
      if not body_struct:
        body_struct = body_struct = getMessageStruct('ServerResponseBody_Attn')
    # Check if this is more than a simple kXR_ok response
    elif status != XProtocol.XResponseType.kXR_ok:
      body_struct = getMessageStruct('ServerResponseBody_' \
                               + get_responseid(status)[4:].title())
    else:
      body_struct = getMessageStruct('ServerResponseBody_' \
                               + request.type[4:].title())

    if not body_struct: body_struct = list()
    response_struct = header_struct + body_struct

    # The number of params in a kXR_open response depends on the options that
    # were passed in the request.
    if requestid == XProtocol.XRequestTypes.kXR_open:
      # Remove members from the response struct if the option was not given in
      # the request.
      response_struct[:] = [m for m in response_struct
                            if self.option_included(m, request, response_raw)]

    # Build complete format string
    format = '>'
    for member in response_struct:
      if member.has_key('size'):
        if member['size'] == 'dlen':
          if member.has_key('offset'):
            format += str(dlen - member['offset']) + member['type']
          else:
            format += str(dlen) + member['type']
        else:
          format += str(member['size']) + member['type']
      else:
        format += member['type']

    if len(body_struct) == 0 and dlen > 0:
      format += (str(dlen) + 's')

    # Unpack to regular tuple
    response_tuple = self.unpack(format, response_raw)
    # Convert to named tuple
    response_struct.insert(0, {'name': 'type'})
    type = get_responseid(status)
    response = namedtuple('response',
                          ' '.join([m['name'] for m in response_struct]))
    return response(type, *response_tuple)

  #-----------------------------------------------------------------------------
  def unpackRequest( self, requestRaw ):
    """Return an unpacked named tuple representation of a client request."""
    if len( requestRaw ) < 20:
      return None

    #---------------------------------------------------------------------------
    # Figure out the request type and build the map of fields
    #---------------------------------------------------------------------------
    requestId = self.unpack('>H', requestRaw[2:4])[0]
    self.logger.debug( 'Received request with id %d' % (requestId) )

    if requestId == XProtocol.XRequestTypes.handshake:
      requestStruct = getMessageStruct('ClientInitHandShake')
      self.logger.debug( 'Mapped request type: handshake' )
    else:
      requestType = XProtocol.XRequestTypes.reverseMapping[requestId]
      requestTypeName = requestType[4:].title()
      self.logger.debug( 'Mapped request type: %s %s' % (requestType, requestTypeName) )
      requestStruct  = getMessageStruct( 'ClientRequestHdr' )
      requestStruct += getMessageStruct( 'Client' + requestTypeName + 'Request' )

    if requestId == XProtocol.XRequestTypes.kXR_read:
        requestStruct += getMessageStruct( 'read_args' )

    #---------------------------------------------------------------------------
    # Build unpacking format string for this message
    #---------------------------------------------------------------------------
    format = '>'
    for member in requestStruct:
      if member.has_key('size'):
        if member['size'] == 'dlen':
          format += str(len(requestRaw) - formatLength(format)) \
                    + member['type']
        else:
          format += str(member['size']) + member['type']
      else:
        format += member['type']
    self.logger.debug( 'Unpack format is: %s' % (format) )

    #---------------------------------------------------------------------------
    # Convert the binary message to a named tupple
    #---------------------------------------------------------------------------
    requestTuple = self.unpack(format, requestRaw)

    # Convert to named tuple
    requestStruct.insert( 0, {'name': 'type'} )
    if requestId == XProtocol.XRequestTypes.handshake:
      type = 'handshake'
    else:
      type = getRequestId( requestId )

    #---------------------------------------------------------------------------
    extra = []
    if requestId == XProtocol.XRequestTypes.kXR_readv:
      extra = self.unpackReadVRequest( requestTuple )

    extraData   = []
    extraFields = []
    for e in extra:
      extraData.append( e[1] )
      extraFields.append( e[0] )
    requestTuple += tuple( extraData )
    extraFields  = ' ' + ' '.join( extraFields )

    request = namedtuple('request',
                         ' '.join([m['name'] for m in requestStruct]) +
                         extraFields)
    return request(type, *requestTuple)

  #-----------------------------------------------------------------------------
  def pack(self, format, values):
    """Try to pack the given values into a binary blob according to the given format string"""
    try:
      return struct.pack( format, *values )
    except (error, TypeError), e:
      raise MessageException( str( e ) );

  #-----------------------------------------------------------------------------
  def unpack(self, format, blob):
    """Try to unpack the given binary blob according to the given format string"""
    try:
      return struct.unpack(format, blob)
    except (error, TypeError), e:
      raise MessageException( str( e ) )

  #-----------------------------------------------------------------------------
  def unpackReadVRequest( self, request ):
    """Unpack the chunks received in the readv request"""
    data = request[-1]
    self.logger.debug( 'Unpacking %s worth of readv chunks' % (len(data)) )
    if not len(data):
      return []
    readFormat = self.getMessageFormat( getMessageStruct( 'read_list' ) )
    readLength = struct.calcsize( readFormat )
    chunksRaw  = [data[x:x+readLength] for x in range(0, len(data), readLength)]
    chunkType  = namedtuple( 'chunk_request', 'fhandle length offset' )
    chunks     = []

    for chunk in chunksRaw:
      c = chunkType( *self.unpack( readFormat, chunk ) )
      chunks.append( c )

    self.logger.debug( 'Unpacked %d chunks: %s' % (len(chunksRaw), str(chunks)) )

    return [('chunks', chunks)]

  def option_included(self, member, request, response_raw):
    """Return whether or not the given member will be in the given packed
    response, based upon the options bitmask in the request, and the size of
    the response."""
    if request.options & XProtocol.XOpenRequestOption.kXR_retstat:
      if member['name'] in ('cpsize', 'cptype', 'data'):
        return True

    if request.options & XProtocol.XOpenRequestOption.kXR_compress:
      if member['name'] in ('cpsize', 'cptype'):
        if len(response_raw) > 12:
          return True
        else: return False
      elif member['name'] == 'data':
        return False

    if member['name'] in ('cpsize', 'cptype', 'data'):
      return False
    else: return True
