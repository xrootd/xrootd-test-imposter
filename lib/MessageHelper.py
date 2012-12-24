import sys
import struct
import socket

import XProtocol
from Utils import *


class MessageHelper:
  
  def __init__(self, context):
    self.sock = context['socket']

  def build_message(self, message_struct, params):
    """Return a packed representation of the given params mapped onto
    the given message struct."""    
    if not len(params) == len(message_struct):
      print "[!] Error building message: wrong number of parameters"
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
    return struct.pack(format, *message)
    
  def send_message(self, message):
    """Send a packed binary message."""
    try:
      self.sock.send(message)
    except socket.error, e:
      print 'Error sending message: %s' % e
      sys.exit(1)
  
  def receive_message(self):
    try:  
      message = self.sock.recv(4096)
    except socket.error, e:
      print 'Error receiving message: %s' % e
      sys.exit(1)
    return message   
  
  def unpack_response(self, response_raw, request_raw):
    """Return an unpacked dict representation of a server response."""    
    request = self.unpack_request(request_raw)
    requestid = get_requestid(request[1])
    
    header_struct = get_struct('ServerResponseHeader')
    format = '>'
     
    for member in header_struct:
      format += member['type']
    
    header = struct.unpack(format + (str(len(response_raw) - 8) + 's'), 
                           response_raw)
    streamid = header[0]
    status = header[1]
    dlen = header[2]

    # Check if this is a handshake response
    if request[1] == XProtocol.XRequestTypes.handshake:
      body_struct = get_struct('ServerInitHandShake')
    # Check if this is amore than a simple kXR_ok response
    elif status != XProtocol.XResponseType.kXR_ok:
      body_struct = get_struct('ServerResponseBody_' \
                               + get_responseid(status)[4:].title())
    else:
      body_struct = get_struct('ServerResponseBody_' \
                               + requestid[4:].title())

    if not body_struct: body_struct = list()
     
    for member in body_struct:
      if member.has_key('size'):
        if member['size'] == 'dlen':
          if member.has_key('offset'):
            format += str(dlen - member['offset']) \
                      + member['type']
          else:       
            format += str(dlen) + member['type']
        else:
          format += str(member['size']) + member['type']
      else: 
        format += member['type']
         
    if len(body_struct) == 0:
      format += (str(dlen) + 's')
         
    response = struct.unpack(format, response_raw)
    return get_responseid(response[1]), response
  
  def unpack_request(self, request_raw):
    """"""
    if not len(request_raw): return
    
    format = '>HH' + (str(len(request_raw) - 4) + 's')
    header = struct.unpack(format, request_raw)
    
    streamid = header[0]
    requestid = header[1]
    
    # Check if this is a handshake request
    if requestid == XProtocol.XRequestTypes.handshake:
      request_struct = get_struct('ClientInitHandShake')
    else:
      request_type = XProtocol.XRequestTypes.reverse_mapping[requestid]
      request_struct = get_struct('Client' + request_type[4:].title() 
                                     + 'Request')
      
    # Check if another request is being piggybacked
    if len(request_raw) > format_length(struct_format(request_struct)):
      format = struct_format(request_struct) + 'HH'
      requestid_2 = struct.unpack(format + str(len(request_raw) 
                                               - format_length(format)) + 's', 
                                  request_raw)[-2]
      request_type_2 = XProtocol.XRequestTypes.reverse_mapping[requestid_2]
      request_struct += get_struct('Client' + request_type_2[4:].title()  
                                   + 'Request')
    
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
        
    request_tuple = struct.unpack(format, request_raw)
    
    # Convert back to dict
    request_dict = dict()
    
    for i, param in enumerate(request_tuple):
      request_dict.update({request_struct[i]['name']: param})
    
    # Insert request type
    request_dict.update({'type': get_requestid(request_dict['requestid'])})
    
    return request_dict
    
    
      
