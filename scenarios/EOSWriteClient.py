from XrdImposter.ImposterClient import ImposterClient
from XrdImposter.XProtocol import XOpenRequestOption, XResponseType


class EOSWriteClient:
  @classmethod
  def getDescription(cls):
    config = """
    xrootd.seclib /usr/lib64/libXrdSec.so
    """

    return { 'type': 'Active', 'hostname': 'eosams.cern.ch', 'port': 1094,
             'clients': 1, 'config': config }

  def __call__(self, context):
    client = ImposterClient(context)
    client.do_full_handshake()
    options = XOpenRequestOption.kXR_open_updt | XOpenRequestOption.kXR_delete

    open_request = client.kXR_open(path='/eos/opstest/jsalmon/file1', options=options)
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
        print '%r' % response_raw
        response = client.unpack(response_raw, write_request)
        print response

