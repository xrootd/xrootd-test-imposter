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

import re
import random

def flatten(*args):
  """Return a flat list or tuple from a nested one."""
  for x in args:
    if hasattr(x, '__iter__'):
      for y in flatten(*x):
        yield y
    else:
      yield x
      
def format_length(format):
  """Return the length in bytes of the given struct
  format string."""
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
  return str(random.randrange(9999999999999999)).zfill(16)

