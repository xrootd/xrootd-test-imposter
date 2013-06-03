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

from struct import error
from collections import namedtuple
from Utils import flatten, struct_format, format_length, get_requestid, \
                  get_responseid, get_struct, get_attncode

import XProtocol

class MessageHelper:

  def __init__(self, context):
    self.sock = context['socket']

  def build_message(self, message_struct, params):
    """Return a packed representation of the given params mapped onto
    the given message struct."""
    if not len(params) == len(message_struct):
      print "[!] Error building message: wrong number of parameters"
      print "[!] Dumping values"
      print "[!]     message_struct (%d): %s" % (len(message_struct), message_struct)
      print "[!]     params (%d):         %s" % (len(params), params)
      sys.exit(1)

    message = tuple()
    format = '>'

    for member in message_struct:
      message += (params[member['name']],)
      if member.has_key('size'):
        if member['size'] == 'dlen':
          if member.has_key('offset'):
            format += str(params[member['size']] - member['offset']) \
                      + member['type']
          else:
            format += str(params[member['size']]) + member['type']
        else:
          format += str(member['size']) + member['type']
      else:
        format += member['type']

    message = tuple(flatten(message))
    return self.pack(format, message)

  def send_message(self, message):
    """Send a packed binary message."""
    try:
      self.sock.send(message)
    except socket.error, e:
      print '[!] Error sending message: %s' % e
      sys.exit(1)

  def receive_message(self):
    """"""
    try:
      message = self.sock.recv(4096)
    except socket.error, e:
      print '[!] Error receiving message: %s' % e
      sys.exit(1)
    return message

  def unpack_response(self, response_raw, request_raw):
    """Return an unpacked named tuple representation of a server response."""
    if not len(response_raw):
      return ''

    # Unpack the request that generated this response for reference
    request = self.unpack_request(request_raw)[0]
    requestid = get_requestid(request.type)

    # Unpack the response header to find the status and data length
    header_struct = get_struct('ServerResponseHeader')
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
      body_struct = get_struct('ServerInitHandShake')
    # Check if this is an asynchronous response
    elif status == XProtocol.XResponseType.kXR_attn:
      # Extract the attn code
      attncode = self.unpack('>H', body[:2])[0]
      body_struct = get_struct('ServerResponseBody_Attn_' \
                               + get_attncode(attncode)[4:])
      if not body_struct:
        body_struct = body_struct = get_struct('ServerResponseBody_Attn')
    # Check if this is more than a simple kXR_ok response
    elif status != XProtocol.XResponseType.kXR_ok:
      body_struct = get_struct('ServerResponseBody_' \
                               + get_responseid(status)[4:].title())
    else:
      body_struct = get_struct('ServerResponseBody_' \
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

  def unpack_request(self, request_raw):
    """Return an unpacked named tuple representation of a client request."""
    if not len(request_raw): return

    # Unpack the header to find the request ID
    requestid = self.unpack('>HH' + (str(len(request_raw) - 4) + 's'),
                            request_raw)[1]

    # Check if this is a handshake request
    if requestid == XProtocol.XRequestTypes.handshake:
      request_struct = get_struct('ClientInitHandShake')
    else:
      request_type = XProtocol.XRequestTypes.reverse_mapping[requestid]
      request_struct  = get_struct('ClientRequestHdr')
      request_struct += get_struct('Client' + request_type[4:].title()
                                   + 'Request')

    if requestid == XProtocol.XRequestTypes.kXR_read:
        request_struct += get_struct('read_args')

    # Check if another request is being piggybacked.
    pending_req = None
    if len(request_raw) > format_length(struct_format(request_struct)):
        pending_req = request_raw[format_length(struct_format(request_struct)):]
        request_raw = request_raw[:format_length(struct_format(request_struct))]

    # Build the complete format string
    format = '>'
    for member in request_struct:
      if member.has_key('size'):
        if member['size'] == 'dlen':
          format += str(len(request_raw) - format_length(format)) \
                    + member['type']
        else:
          format += str(member['size']) + member['type']
      else:
        format += member['type']

    # Unpack to a regular tuple
    request_tuple = self.unpack(format, request_raw)

    # Convert to named tuple
    request_struct.insert(0, {'name': 'type'})
    if requestid == XProtocol.XRequestTypes.handshake:
      type = 'handshake'
    else:
      type = get_requestid(requestid)

    request = namedtuple('request',
                         ' '.join([m['name'] for m in request_struct]))
    return request(type, *request_tuple), pending_req

  def pack(self, format, values):
    """Try to pack the given values into a binary blob according to the given format string"""
    try:
      return struct.pack(format, *values)
    except (error, TypeError), e:
      print '[!] Error packing:', e
      print '[!] Dumping values'
      print '[!]     format: ', format
      print '[!]     message: %r' % values
      sys.exit(1)

  def unpack(self, format, blob):
    """Try to unpack the given binary blob according to the given format string"""
    try:
      return struct.unpack(format, blob)
    except (error, TypeError), e:
      print '[!] Error unpacking:', e
      print '[!] Dumping values'
      print '[!]     format:', format
      print '[!]     blob:   %r' % blob
      sys.exit(0)

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
