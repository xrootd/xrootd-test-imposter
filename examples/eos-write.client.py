from XrdImposter.ImposterClient import ImposterClient
from XrdImposter.XProtocol import XOpenRequestOption, XResponseType


class AndyTest:
  @classmethod
  def getDescription(cls):
    config = """
    xrootd.seclib /usr/lib64/libXrdSec.dylib
    """

    return { 'type': 'Active', 'hostname': 'eosdevsrv1.cern.ch', 'port': 1094,
             'clients': 1, 'config': config }

  def __call__(self, context):
    client = ImposterClient(context)
    sess_id = client.do_full_handshake()

    open_request = client.kXR_open(path='/eos/dev/2rep/test3', options=XOpenRequestOption.kXR_open_updt
                                                                       | XOpenRequestOption.kXR_delete)
    client.send(open_request)
    response_raw = client.receive()
    response = client.unpack(response_raw, open_request)
    print response

    if response.status == XResponseType.kXR_redirect:
        # We got redirected
        print 'Got redirected to %r' % response.host

        write_request = client.kXR_write(data='lol')
        client.send(write_request)
        response_raw = client.receive()
        response = client.unpack(response_raw, write_request)
        print response

    else:
        fhandle = response.fhandle

        try:
            write_request = client.kXR_write(fhandle=fhandle, data='lol')
            client.send(write_request)
            response_raw = client.receive()
            response = client.unpack(response_raw, write_request)
            print response
        except:
            close_request = client.kXR_close(fhandle=fhandle)
            client.send(close_request)
            response_raw = client.receive()
            response = client.unpack(response_raw, close_request)
            print response
