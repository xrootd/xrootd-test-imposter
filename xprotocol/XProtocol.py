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

# XRootd Type   Sign        Bit Length  Bit Alignment   Typical Host Type   Struct Type
#
# kXR_char8     unsigned    8           8               unsigned char       B
# kXR_unt16     unsigned    16          16              unsigned short      H
# kXR_int32     signed      32          32              long                l
# kXR_int64     signed      64          64              long long           q

import sys
import lib.CppHeaderParser as CppHeaderParser

class XProtocolError(Exception):
  pass

class XProtocol:
    
  def __init__(self):
    xprotocol_path = '/usr/include/xrootd/XProtocol/XProtocol.hh'
    try:
      self.xprotocol = CppHeaderParser.CppHeader(xprotocol_path)
    except  (CppHeaderParser.CppParseError, IOError), e:
      print "[!] Unable to initialize XProtocol:", e
      sys.exit(1)
        
  def get_enum(self, name):
    """Return a representation of an enum as a list of dicts."""
    enum = {}
    for e in self.xprotocol.enums:
      if e['name'] == name:
        enum = e['values']
        
    if not enum:
      print "[!] XProtocol enum %s not found: %s" % (name, e)
      sys.exit(1)
        
    return enum
    
  def get_struct(self, name):
    """Return a representation of a struct as a list of dicts."""
    try:
      struct = self.xprotocol.classes[name]
    except KeyError, e:
      print "[!] XProtocol struct %s not found: %s" % (name, e)
      sys.exit(1) 
            
    return struct['properties']['public']
    
  def get_requestid(self, requestid):
    """Return the integer request ID associated with the given 
    string request ID.

    For example, passing "kXR_ping" will return 3011.

    """ 
    reqid_int = 0
    reqtypes = self.get_enum('XRequestTypes')
    
    for reqtype in reqtypes:
      if reqtype['name'] == requestid:
        reqid_int = reqtype['value']
        
    if not reqid_int:
      print "[!] Unknown request ID:", requestid
      
    return reqid_int
          
          
          
          
          
