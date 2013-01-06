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
import re
import random
import copy

import XProtocol

def flatten(*args):
  """Return a flat list or tuple from a nested one."""
  for x in args:
    if hasattr(x, '__iter__'):
      for y in flatten(*x):
        yield y
    else:
      yield x
      
def format_length(format):
  """Return the length in bytes of the given struct format string."""
  mapping = {'c': 1, 's': 1, 'B': 1, 'H': 2, 'l': 4, 'q': 8}
  groups = re.findall('\d*[csBHlq]', format)
  length = 0
  
  for g in groups:
    if len(g) > 1:
      length += int(g[:-1]) * mapping[g[-1]]
    else:
      length += mapping[g[-1]]
  return length 
    
def struct_format(struct):
  """Return the complete format string for the given struct."""
  format = '>'

  for member in struct:
    if member.has_key('size'):
      if member['size'] == 'dlen':
        format += str(4096) + member['type']
      else:
        format += (str(member['size']) + member['type'])
    else:
      format += member['type']
  
  return format

def gen_sessid():
  """Return a random session ID of length 16"""
  return str(random.randrange(9999999999999999)).zfill(16)

def get_struct(name):
  """Return a representation of a struct as a list of dicts."""
  if hasattr(XProtocol, name):
    struct = getattr(XProtocol, name)
    return copy.copy(struct)
  
def get_requestid(requestid):
  """Return the integer request ID associated with the given string request ID, 
  or the other way around.""" 
  try:
    if hasattr(XProtocol.XRequestTypes, requestid):
      return getattr(XProtocol.XRequestTypes, requestid)
  except: pass
  
  try:
    return XProtocol.XRequestTypes.reverse_mapping[requestid]
  except: pass
  
  print "[!] Unknown request ID:", requestid
  sys.exit(1)
  
def get_responseid(responseid):
  """Return the string response ID associated with the given integer response 
  ID, or the other way around."""
  try:
    if hasattr(XProtocol.XResponseType, responseid):
      return getattr(XProtocol.XResponseType, responseid)
  except: pass
  
  try:
    return XProtocol.XResponseType.reverse_mapping[responseid]
  except: pass
  
  print "[!] Unknown response ID:", responseid
  sys.exit(1)

def get_attncode(attncode):
  """Return the string attn code associated with the given integer attn code, 
  or the other way around."""
  try:
    if hasattr(XProtocol.XActionCode, attncode):
      return getattr(XProtocol.XActionCode, attncode)
  except: pass
  
  try:
    return XProtocol.XActionCode.reverse_mapping[attncode]
  except: pass
  
  print "[!] Unknown attn code:", attncode
  sys.exit(1)
  

