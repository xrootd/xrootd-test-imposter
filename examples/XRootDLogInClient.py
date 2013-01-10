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

from XrdImposter.ImposterClient import ImposterClient
from XrdImposter.XProtocol import XResponseType

class XRootDLogInClient:
  @classmethod
  def getDescription(cls):
    return { 'type': 'Active', 'hostname': 'localhost', 'port': 1094, 
             'clients': 1, 'seclib': 'libXrdSec.so' }

  def __call__(self, context):
    client = ImposterClient(context)

    # The following line will to the equivalent of the rest of this method,
    # using sensible default values.
    #
    # sess_id = client.do_full_handshake()
    handshake_request = client.handshake()
    client.send(handshake_request)
    response_raw = client.receive()
    response = client.unpack(response_raw, handshake_request)
    print response

    protocol_request = client.kXR_protocol()
    client.send(protocol_request)
    response_raw = client.receive()
    response = client.unpack(response_raw, protocol_request)
    print response

    login_request = client.kXR_login(username='imposter')
    client.send(login_request)
    response_raw = client.receive()
    response = client.unpack(response_raw, login_request)
    sessid = response.sessid
    print response

    # Check if we need to auth
    if len(response.sec):
      auth_request = client.kXR_auth(authtoken=response.sec)
      client.send(auth_request)
      response_raw = client.receive()
      response = client.unpack(response_raw, auth_request)
      print response

      # Check if we need to authmore
      while response.status == XResponseType.kXR_authmore:
        print "More authentication needed, continuing"
        auth_request = client.kXR_auth(contcred=response.data)
        client.send(auth_request)
        response_raw = client.receive()
        response = client.unpack(response_raw, auth_request)
        print response

    if response.status == XResponseType.kXR_ok:
      print "Logged in successfully"
    else:
      print "Login failed (%s): %s" % (response.status, response.errmsg)
