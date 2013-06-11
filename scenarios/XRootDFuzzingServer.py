from XrdImposter.Fuzzer import Fuzzer
from XrdImposter.ImposterServer import ImposterServer
from XrdImposter.MessageHelper import MessageHelper
from XrdImposter.XProtocol import XResponseType, XRequestTypes

class XRootDFuzzingServer:
  @classmethod
  def getDescription( cls ):
    config = """
    xrootd.seclib /usr/lib64/libXrdSec.so
    # sec.protocol gsi
    sec.protocol unix
    """

    return { 'type': 'Passive', 'ip': '0.0.0.0', 'port': 1095, 'clients': 12000,
             'config': config }

  def __call__( self, context ):
    server = ImposterServer(context)
    fuzzer = Fuzzer(context, iterations=1)
    mh     = MessageHelper(context)

    # The following line will to the equivalent of the rest of this method,
    # using sensible default values and optionally fully authenticating.
    #
    # server.do_full_handshake(verify_auth=True)
    for request in server.receive():

      if request.type == 'handshake':
        print request
        server.send(server.handshake())

      if request.type == 'kXR_protocol':
        print request
        server.send(server.kXR_protocol(streamid=request.streamid))

      elif request.type == 'kXR_login':
        print request
        server.send(server.kXR_login(streamid=request.streamid, verify_auth=True))

      elif request.type == 'kXR_auth':
        # Authenticate this request's credentials and potentially get
        # continuation (authmore) parameters
        contparams = server.authenticate(request.cred)
        if contparams:
          # Send an authmore if necessary
          response = server.kXR_authmore(streamid=request.streamid,
                                         data=contparams)
        else:
          # We are done authenticating
          response = server.kXR_ok(streamid=request.streamid)

        server.send(response)
        # If we have contparams, there will be more auth-related requests
        # to receive at this stage. Otherwise, we are done
        if not contparams: continue
        
        #    kXR_query    = 3001,
        #    kXR_chmod    = 3002,
        #    kXR_close    = 3003,
        #    kXR_dirlist  = 3004,
        #    kXR_protocol = 3006,
        #    kXR_mkdir    = 3008,
        #    kXR_mv       = 3009,
        #    kXR_open     = 3010,
        #    kXR_ping     = 3011,
        #    kXR_read     = 3013,
        #    kXR_rm       = 3014,
        #    kXR_rmdir    = 3015,
        #    kXR_sync     = 3016,
        #    kXR_stat     = 3017,
        #    kXR_set      = 3018,
        #    kXR_write    = 3019,
        #    kXR_prepare  = 3021,
        #    kXR_statx    = 3022,
        #    kXR_endsess  = 3023,
        #    kXR_bind     = 3024,
        #    kXR_readv    = 3025,
        #    kXR_verifyw  = 3026,
        #    kXR_locate   = 3027,
        #    kXR_truncate = 3028
        # )

      elif request.type == 'kXR_chmod':
        stat_response = server.kXR_error(errmsg=20*'\0')
        #server.send(stat_response)
        for m in fuzzer.fuzz_response(stat_response, request):
            print mh.unpack_response(m, request)
            fuzzer.send(m)

      elif request.type == 'kXR_stat':
        print request
        stat_response = server.kXR_stat(data='2251804108717312 20480 51 1370444422\0')
        #server.send(stat_response)
        for m in fuzzer.fuzz_response(stat_response, request):
            print mh.unpack_response(m, request)
            fuzzer.send(m)
            # response_raw = fuzzer.receive()
            # response = mh.unpack(response_raw, m)
            # print response

    server.close()
