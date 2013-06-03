from XrdImposter.ImposterClient import ImposterClient
from XrdImposter.Fuzzer import Fuzzer
from XrdImposter.MessageHelper import MessageHelper


class XRootDFuzzingClient:
    @classmethod
    def getDescription(cls):
        config = """
                 xrootd.seclib /usr/lib64/libXrdSec.so
                 """

        return {'type': 'Active', 'hostname': 'localhost', 'port': 1094,
                'clients': 1, 'config': config}

    def __call__(self, context):
        client = ImposterClient(context)
        mh = MessageHelper(context)
        fuzzer = Fuzzer(context)

        handshake_request = client.handshake()
        print mh.unpack_request(handshake_request)

        # Fuzz a read request
        for m in fuzzer.fuzz(handshake_request):
            print mh.unpack_request(m)[0]
            client.send(m)
            response_raw = client.receive()
            response = client.unpack(response_raw, m)
            print response

        # # Log in and authenticate
        # client.do_full_handshake()
        #
        # # Open a file
        # open_request = client.kXR_open(path='/tmp/spam')
        # print mh.unpack_request(open_request)[0]
        # client.send(open_request)
        # response_raw = client.receive()
        # response = client.unpack(response_raw, open_request)
        # print response
        #
        # read_request = client.kXR_read(rlen=1024)
        # print mh.unpack_request(read_request)
        #
        # # Fuzz a read request
        # for m in fuzzer.fuzz(read_request):
        #     print mh.unpack_request(m)[0]
        #     client.send(m)
        #     response_raw = client.receive()
        #     response = client.unpack(response_raw, m)
        #     print response


