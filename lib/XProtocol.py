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
# kXR_char8     unsigned    8           8               unsigned char       c
# kXR_unt16     unsigned    16          16              unsigned short      H
# kXR_int32     signed      32          32              long                l
# kXR_int64     signed      64          64              long long           q

def enum(**enums):
  """Build the equivalent of a C++ enum"""
  reverse = dict((value, key) for key, value in enums.iteritems())
  enums['reverse_mapping'] = reverse
  return type('Enum', (), enums)


# The following is the binary representation of the protocol version here.
# Protocol version is repesented as three base10 digits x.y.z with x having no
# upper limit (i.e. n.9.9 + 1 -> n+1.0.0).
kXR_PROTOCOLVERSION = 0x00000297
kXR_PROTOCOLVSTRING = "2.9.7"

# Kinds of servers
kXR_DataServer = 1
kXR_LBalServer = 0

# The below are defined for protocol version 2.9.7 or higher
kXR_isManager = 0x00000002
kXR_isServer  = 0x00000001
kXR_attrMeta  = 0x00000100
kXR_attrProxy = 0x00000200
kXR_attrSuper = 0x00000400

kXR_maxReqRetry = 10

XReqErrorType = enum(
   kGENERICERR       = 0,  # Generic error
   kREAD             = 1,  # Error while reading from stream
   kWRITE            = 2,  # Error while writing to stream
   kREDIRCONNECT     = 3,  # Error redirecting to a given host
   kOK               = 4,  # Everything seems ok
   kNOMORESTREAMS    = 5   # No more available stream IDs for async processing
)

#-------------------------------------------------------------------------------
# PROTOCOL DEFINITION: CLIENT'S REQUESTS TYPES
#-------------------------------------------------------------------------------
XRequestTypes = enum(
   handshake    = 0,
   kXR_auth     = 3000,
   kXR_query    = 3001,
   kXR_chmod    = 3002,
   kXR_close    = 3003,
   kXR_dirlist  = 3004,
   kXR_getfile  = 3005,
   kXR_protocol = 3006,
   kXR_login    = 3007,
   kXR_mkdir    = 3008,
   kXR_mv       = 3009,
   kXR_open     = 3010,
   kXR_ping     = 3011,
   kXR_putfile  = 3012,
   kXR_read     = 3013,
   kXR_rm       = 3014,
   kXR_rmdir    = 3015,
   kXR_sync     = 3016,
   kXR_stat     = 3017,
   kXR_set      = 3018,
   kXR_write    = 3019,
   kXR_admin    = 3020,
   kXR_prepare  = 3021,
   kXR_statx    = 3022,
   kXR_endsess  = 3023,
   kXR_bind     = 3024,
   kXR_readv    = 3025,
   kXR_verifyw  = 3026,
   kXR_locate   = 3027,
   kXR_truncate = 3028
)

# OPEN MODE FOR A REMOTE FILE
XOpenRequestMode = enum(
   kXR_ur = 0x100,
   kXR_uw = 0x080,
   kXR_ux = 0x040,
   kXR_gr = 0x020,
   kXR_gw = 0x010,
   kXR_gx = 0x008,
   kXR_or = 0x004,
   kXR_ow = 0x002,
   kXR_ox = 0x001
)

XMkdirOptions = enum(
   kXR_mknone    = 0,
   kXR_mkdirpath = 1
)

# this is a bitmask
XLoginCapVer = enum(
   kXR_lcvnone = 0,
   kXR_vermask = 63,
   kXR_asyncap = 128
)

# this is a single number that goes into capver as the version
XLoginVersion = enum(
   kXR_ver000 = 0,  # Old clients predating history
   kXR_ver001 = 1,  # Generally implemented 2005 protocol
   kXR_ver002 = 2,  # Same as 1 but adds asyncresp recognition
   kXR_ver003 = 3   # The 2011-2012 rewritten client
)

XStatRequestOption = enum(
   kXR_vfs    = 1
)

XStatRespFlags = enum(
   kXR_file      = 0,
   kXR_xset      = 1,
   kXR_isDir     = 2,
   kXR_other     = 4,
   kXR_offline   = 8,
   kXR_readable  =16,
   kXR_writable  =32,
   kXR_poscpend  =64
)

XDirlistRequestOption = enum(
   kXR_online = 1
)

XOpenRequestOption = enum(
   kXR_compress  = 1,
   kXR_delete    = 2,
   kXR_force     = 4,
   kXR_new       = 8,
   kXR_open_read = 16,
   kXR_open_updt = 32,
   kXR_async     = 64,
   kXR_refresh   = 128,
   kXR_mkpath    = 256,
   kXR_open_apnd = 512,
   kXR_retstat   = 1024,
   kXR_replica   = 2048,
   kXR_posc      = 4096,
   kXR_nowait    = 8192,
   kXR_seqio     = 16384
)

XQueryType = enum(
   kXR_QStats  = 1,
   kXR_QPrep   = 2,
   kXR_Qcksum  = 3,
   kXR_Qxattr  = 4,
   kXR_Qspace  = 5,
   kXR_Qckscan = 6,
   kXR_Qconfig = 7,
   kXR_Qvisa   = 8,
   kXR_Qopaque = 16,
   kXR_Qopaquf = 32
)

XVerifyType = enum(
   kXR_nocrc  = 0,
   kXR_crc32  = 1
)

XLogonType = enum(
   kXR_useruser  = 0,
   kXR_useradmin = 1
)

# Andy's request for async/unsolicited
XPrepRequestOption = enum(
   kXR_cancel = 1,
   kXR_notify = 2,
   kXR_noerrs = 4,
   kXR_stage  = 8,
   kXR_wmode  = 16,
   kXR_coloc  = 32,
   kXR_fresh  = 64
)


#-------------------------------------------------------------------------------
# PROTOCOL DEFINITION: SERVER'S RESPONSES TYPES
#-------------------------------------------------------------------------------
XResponseType = enum(
   kXR_ok             = 0,
   kXR_oksofar        = 4000,
   kXR_attn           = 4001,
   kXR_authmore       = 4002,
   kXR_error          = 4003,
   kXR_redirect       = 4004,
   kXR_wait           = 4005,
   kXR_waitresp       = 4006,
   kXR_noResponsesYet = 10000
)

#-------------------------------------------------------------------------------
# PROTOCOL DEFINITION: SERVER'S ATTN CODES
#-------------------------------------------------------------------------------
XActionCode = enum(
   kXR_asyncab  = 5000,
   kXR_asyncdi  = 5001,
   kXR_asyncms  = 5002,
   kXR_asyncrd  = 5003,
   kXR_asyncwt  = 5004,
   kXR_asyncav  = 5005,
   kXR_asynunav = 5006,
   kXR_asyncgo  = 5007,
   kXR_asynresp = 5008
)

#-------------------------------------------------------------------------------
# PROTOCOL DEFINITION: SERVER'S ERROR CODES
#-------------------------------------------------------------------------------
XErrorCode = enum(
   kXR_ArgInvalid     = 3000,
   kXR_ArgMissing     = 3001,
   kXR_ArgTooLong     = 3002,
   kXR_FileLocked     = 3003,
   kXR_FileNotOpen    = 3004,
   kXR_FSError        = 3005,
   kXR_InvalidRequest = 3006,
   kXR_IOError        = 3007,
   kXR_NoMemory       = 3008,
   kXR_NoSpace        = 3009,
   kXR_NotAuthorized  = 3010,
   kXR_NotFound       = 3011,
   kXR_ServerError    = 3012,
   kXR_Unsupported    = 3013,
   kXR_noserver       = 3014,
   kXR_NotFile        = 3015,
   kXR_isDirectory    = 3016,
   kXR_Cancelled      = 3017,
   kXR_ChkLenErr      = 3018,
   kXR_ChkSumErr      = 3019,
   kXR_inProgress     = 3020,
   kXR_noErrorYet     = 10000
)

#-------------------------------------------------------------------------------
# PROTOCOL DEFINITION: CLIENT'S REQUESTS STRUCTS
#-------------------------------------------------------------------------------
# 
# Note that the protocol specifies these values to be in network
# byte order when sent

ClientAdminRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'reserved', 'type': 's', 'size': 16},
  {'name': 'dlen', 'type': 'l'}
]

ClientAuthRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'reserved', 'type': 's', 'size': 12},
  {'name': 'credtype', 'type': 's', 'size': 4},
  {'name': 'dlen', 'type': 'l'},
  {'name': 'cred', 'type': 's', 'size': 'dlen'}
]

ClientBindRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'sessid', 'type': 's', 'size': 16},
  {'name': 'dlen', 'type': 'l'}
]

ClientChmodRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'reserved', 'type': 's', 'size': 14},
  {'name': 'mode', 'type': 'H'},
  {'name': 'dlen', 'type': 'l'},
  {'name': 'path', 'type': 's', 'size': 'dlen'}
]

ClientCloseRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'fhandle', 'type': 's', 'size': 4},
  {'name': 'fsize', 'type': 'q'},
  {'name': 'reserved', 'type': 's', 'size': 4},
  {'name': 'dlen', 'type': 'l'}
]

ClientDirlistRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'reserved', 'type': 's', 'size': 15},
  {'name': 'options', 'type': 'c', 'size': 1},
  {'name': 'dlen', 'type': 'l'},
  {'name': 'path', 'type': 's', 'size': 'dlen'}
]

ClientEndsessRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'sessid', 'type': 's', 'size': 16},
  {'name': 'dlen', 'type': 'l'}
]

ClientGetfileRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'options', 'type': 'l'},
  {'name': 'reserved', 'type': 's', 'size': 8},
  {'name': 'buffsz', 'type': 'l'},
  {'name': 'dlen', 'type': 'l'}
]

ClientLocateRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'options', 'type': 'H'},
  {'name': 'reserved', 'type': 's', 'size': 14},
  {'name': 'dlen', 'type': 'l'},
  {'name': 'path', 'type': 's', 'size': 'dlen'}
]

ClientLoginRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'pid', 'type': 'l'},
  {'name': 'username', 'type': 's', 'size': 8},
  {'name': 'reserved', 'type': 's', 'size': 1},
  {'name': 'zone', 'type': 's', 'size': 1},
  {'name': 'capver', 'type': 'c', 'size': 1},
  {'name': 'role', 'type': 'c', 'size': 1},
  {'name': 'dlen', 'type': 'l'}
]

ClientMkdirRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'options', 'type': 'c', 'size': 1},
  {'name': 'reserved', 'type': 's', 'size': 13},
  {'name': 'mode', 'type': 'H'},
  {'name': 'dlen', 'type': 'l'},
  {'name': 'path', 'type': 's', 'size': 'dlen'}
]

ClientMvRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'reserved', 'type': 's', 'size': 16},
  {'name': 'dlen', 'type': 'l'},
  {'name': 'path', 'type': 's', 'size': 'dlen'}
]

ClientOpenRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'mode', 'type': 'H'},
  {'name': 'options', 'type': 'H'},
  {'name': 'reserved', 'type': 's', 'size': 12},
  {'name': 'dlen', 'type': 'l'},
  {'name': 'path', 'type': 's', 'size': 'dlen'}
]

ClientPingRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'reserved', 'type': 's', 'size': 16},
  {'name': 'dlen', 'type': 'l'}
]

ClientProtocolRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'clientpv', 'type': 'l'}, # 2.9.7 or higher
  {'name': 'reserved', 'type': 's', 'size': 12},
  {'name': 'dlen', 'type': 'l'}
]

ClientPrepareRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'options', 'type': 'c'},
  {'name': 'prty', 'type': 'c'},
  {'name': 'port', 'type': 'H'}, # 2.9.9 or higher
  {'name': 'reserved', 'type': 's', 'size': 12},
  {'name': 'dlen', 'type': 'l'},
  {'name': 'plist', 'type': 's', 'size': 'dlen'}
]

ClientPutfileRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'options', 'type': 'l'},
  {'name': 'reserved', 'type': 's', 'size': 8},
  {'name': 'buffsz', 'type': 'l'},
  {'name': 'dlen', 'type': 'l'}
]

ClientQueryRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'reqcode', 'type': 'H'},
  {'name': 'reserved1', 'type': 's', 'size': 2},
  {'name': 'fhandle', 'type': 's', 'size': 4},
  {'name': 'reserved2', 'type': 's', 'size': 8},
  {'name': 'dlen', 'type': 'l'},
  {'name': 'args', 'type': 's', 'size': 'dlen'}
]

ClientReadRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'fhandle', 'type': 's', 'size': 4},
  {'name': 'offset', 'type': 'q'},
  {'name': 'rlen', 'type': 'l'},
  {'name': 'dlen', 'type': 'l'}
]

ClientReadVRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'reserved', 'type': 's', 'size': 15},
  {'name': 'pathid', 'type': 'c'},
  {'name': 'dlen', 'type': 'l'}
]

ClientRmRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'reserved', 'type': 's', 'size': 16},
  {'name': 'dlen', 'type': 'l'},
  {'name': 'path', 'type': 's', 'size': 'dlen'}
]

ClientRmdirRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'reserved', 'type': 's', 'size': 16},
  {'name': 'dlen', 'type': 'l'},
  {'name': 'path', 'type': 's', 'size': 'dlen'}
]

ClientSetRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'reserved', 'type': 's', 'size': 16},
  {'name': 'dlen', 'type': 'l'}
]

ClientStatRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'options', 'type': 'c'},
  {'name': 'reserved', 'type': 's', 'size': 11},
  {'name': 'fhandle', 'type': 's', 'size': 4},
  {'name': 'dlen', 'type': 'l'},
  {'name': 'path', 'type': 's', 'size': 'dlen'}
]

ClientSyncRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'fhandle', 'type': 's', 'size': 4},
  {'name': 'reserved', 'type': 's', 'size': 12},
  {'name': 'dlen', 'type': 'l'}
]

ClientTruncateRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'fhandle', 'type': 's', 'size': 4},
  {'name': 'offset', 'type': 'q'},
  {'name': 'reserved', 'type': 's', 'size': 4},
  {'name': 'dlen', 'type': 'l'}
]

ClientWriteRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'fhandle', 'type': 's', 'size': 4},
  {'name': 'offset', 'type': 'q'},
  {'name': 'pathid', 'type': 'c'},
  {'name': 'reserved', 'type': 's', 'size': 3},
  {'name': 'dlen', 'type': 'l'}
]

ClientVerifywRequest = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'fhandle', 'type': 's', 'size': 4},
  {'name': 'offset', 'type': 'q'},
  {'name': 'pathid', 'type': 'c'},
  {'name': 'vertype', 'type': 'c'}, # One of XVerifyType
  {'name': 'reserved', 'type': 's', 'size': 2},
  {'name': 'dlen', 'type': 'l'} # Includes crc length
]

ClientRequestHdr = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'requestid', 'type': 'H'},
  {'name': 'body', 'type': 's', 'size': 16},
  {'name': 'streamid', 'type': 'H'},
]


readahead_list = [
  {'name': 'fhandle2', 'type': 's', 'size': 4},
  {'name': 'rlen2', 'type': 'l'},
  {'name': 'roffset2', 'type': 'q'}
]

read_args = [
  {'name': 'pathid', 'type': 's'},
  {'name': 'reserved', 'type': 's', 'size': 7}
]

#-------------------------------------------------------------------------------
#   PROTOCOL DEFINITION: SERVER'S RESPONSE
#-------------------------------------------------------------------------------
#
# Note that the protocol specifies these values to be in network
# byte order when sent
#
# G.Ganis: The following structures never need padding bytes:
#          no need of packing options

ServerResponseHeader = [
  {'name': 'streamid', 'type': 'H'},
  {'name': 'status', 'type': 'H'},
  {'name': 'dlen', 'type': 'l'}
]

ServerResponseBody_Bind = [
  {'name': 'substreamid', 'type': 'c'},
]

ServerResponseBody_Open = [
  {'name': 'fhandle', 'type': 's', 'size': 4},
  {'name': 'cpsize', 'type': 'l'}, # cpsize & cptype returned if kXR_compress *or*
  {'name': 'cptype', 'type': 's', 'size': 4}, # kXR_retstat is specified
  {'name': 'data', 'type': 's', 'size': 'dlen', 'offset': 12}
] # info will follow if kXR_retstat is specified

ServerResponseBody_Protocol = [
  {'name': 'pval', 'type': 'l'},
  {'name': 'flags', 'type': 'l'}
]

ServerResponseBody_Login = [
  {'name': 'sessid', 'type': 's', 'size': 16},
  {'name': 'sec', 'type': 's', 'size': 'dlen', 'offset': 16}
]

ServerResponseBody_Redirect = [
  {'name': 'port', 'type': 'l'},
  {'name': 'host', 'type': 's', 'size': 'dlen'}
]

ServerResponseBody_Error = [
  {'name': 'errnum', 'type': 'l'},
  {'name': 'errmsg', 'type': 's', 'size': 'dlen', 'offset': 4}
]

ServerResponseBody_Wait = [
  {'name': 'seconds', 'type': 'l'},
  {'name': 'infomsg', 'type': 's', 'size': 'dlen'}
]

ServerResponseBody_Waitresp = [
  {'name': 'seconds', 'type': 'l'},
]

ServerResponseBody_Attn = [
  {'name': 'actnum', 'type': 'l'},
  {'name': 'parms', 'type': 's', 'size': 'dlen'}
]

ServerResponseBody_Attn_asyncrd = [
  {'name': 'actnum', 'type': 'l'},
  {'name': 'port', 'type': 'l'},
  {'name': 'host', 'type': 's', 'size': 'dlen'}
]

ServerResponseBody_Attn_asynresp = [
  {'name': 'actnum', 'type': 'l'},
  {'name': 'reserved', 'type': 's', 'size': 4},
  {'name': 'resphdr', 'type': 'ServerResponseHeader'},
  {'name': 'respdata', 'type': 's', 'size': 'dlen'}
]

ServerResponseBody_Attn_asyncwt = [
  {'name': 'actnum', 'type': 'l'},
  {'name': 'wsec', 'type': 'l'},
]

ServerResponseBody_Attn_asyncdi = [
  {'name': 'actnum', 'type': 'l'},
  {'name': 'wsec', 'type': 'l'},
  {'name': 'msec', 'type': 'l'},
]

ServerResponseBody_Authmore = [
  {'name': 'data', 'type': 's', 'size': 'dlen'}
]

ServerResponseBody_Buffer = [
  {'name': 'data', 'type': 's', 'size': 'dlen'}
]

ServerResponseBody_Dirlist = [
  {'name': 'data', 'type': 's', 'size': 'dlen'}
]

ServerResponseBody_Locate = [
  {'name': 'data', 'type': 's', 'size': 'dlen'}
]

ServerResponseBody_Prepare = [
  {'name': 'data', 'type': 's', 'size': 'dlen'}
]

ServerResponseBody_Query = [
  {'name': 'data', 'type': 's', 'size': 'dlen'}
]

ServerResponseBody_Read = [
  {'name': 'data', 'type': 's', 'size': 'dlen'}
]

ServerResponseBody_Readv = [
  {'name': 'data', 'type': 's', 'size': 'dlen'}
]

ServerResponseBody_Stat = [
  {'name': 'data', 'type': 's', 'size': 'dlen'}
]

# The fields to be sent as initial handshake
ClientInitHandShake = [
  {'name': 'first', 'type': 'l'},
  {'name': 'second', 'type': 'l'},
  {'name': 'third', 'type': 'l'},
  {'name': 'fourth', 'type': 'l'},
  {'name': 'fifth', 'type': 'l'},
]

# The body received after the first handshake's header
ServerInitHandShake = [
  {'name': 'protover', 'type': 'l'},
  {'name': 'msgval', 'type': 'l'},
]
          
XActionCode = enum(
   kXR_asyncab  = 5000,
   kXR_asyncdi  = 5001,
   kXR_asyncms  = 5002,
   kXR_asyncrd  = 5003,
   kXR_asyncwt  = 5004,
   kXR_asyncav  = 5005,
   kXR_asynunav = 5006,
   kXR_asyncgo  = 5007,
   kXR_asynresp = 5008
)
