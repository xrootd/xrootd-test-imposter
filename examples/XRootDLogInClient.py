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

from lib.ImposterClient import ImposterClient
from lib.XProtocol import XOpenRequestMode, XOpenRequestOption, XQueryType

class XRootDLogInClient:
  @classmethod
  def getDescription(cls):
    return { 'type': 'Active', 'hostname': '192.168.56.101', 'port': 1094, 
             'clients': 1, 'seclib': 'libXrdSec.dylib' }

  def __call__(self, context):
    client = ImposterClient(context)
    
    sess_id = client.do_full_handshake()
    
    #request = client.kXR_bind(sessid=sess_id)
    #request = client.kXR_chmod()
    #request = client.kXR_dirlist(path='/tmp')
    #request = client.kXR_endsess()
    #request = client.kXR_locate(path='/tmp/testfile')
    #request = client.kXR_mkdir(path='/tmp/testdir2')
    #request = client.kXR_mv(path='/tmp/testdir2 /tmp/testdir3')
    #request = client.kXR_open(path='/tmp/testfile', options=XOpenRequestOption.kXR_retstat)
    #request = client.kXR_prepare(plist='/tmp/testfile')
    #request = client.kXR_query(reqcode=XQueryType.kXR_Qspace, args='/tmp')
    #request = client.kXR_rm(path='/tmp/testdir')
    #request = client.kXR_rmdir(path='/tmp/testdir3')
    #request = client.kXR_set(data='monitor on')
    #request = client.kXR_stat(path="/tmp/testfile")
    #request = client.kXR_statx(paths="/tmp/testfile")
    request = client.kXR_truncate(size=20000, path="/tmp/testfile")
    
    client.send(request)
    response_raw = client.receive()
    response = client.unpack(response_raw, request)
    print response
    
    #request = client.kXR_close(fhandle=response.fhandle)
    #request = client.kXR_readv(read_list1=(response.fhandle, 1024, 0),
    #                           read_list2=(response.fhandle, 1024, 1024))
    #request = client.kXR_sync(fhandle=response.fhandle)

    
#    client.send(request)
#    response_raw = client.receive()
#    response = client.unpack(response_raw, request)
#    print response
    
    
    
    
    
    
    
