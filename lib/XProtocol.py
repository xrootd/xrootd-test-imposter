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
  enums['reverseMapping'] = reverse
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

ClientRequestHdr = [
  {'name': 'streamid',  'type': 'H', 'fuzzable': True},
  {'name': 'requestid', 'type': 'H', 'fuzzable': False},
]

ClientAdminRequest = [
  {'name': 'reserved', 'type': 's', 'size': 16, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
]

ClientAuthRequest = [
  {'name': 'reserved', 'type': 's', 'size': 12, 'fuzzable': True},
  {'name': 'credtype', 'type': 's', 'size': 4, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
  {'name': 'cred', 'type': 's', 'size': 'dlen', 'fuzzable': True},
]

ClientBindRequest = [
  {'name': 'sessid', 'type': 's', 'size': 16, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
]

ClientChmodRequest = [
  {'name': 'reserved', 'type': 's', 'size': 14, 'fuzzable': True},
  {'name': 'mode', 'type': 'H', 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
  {'name': 'path', 'type': 's', 'size': 'dlen', 'fuzzable': True},
]

ClientCloseRequest = [
  {'name': 'fhandle', 'type': 's', 'size': 4, 'fuzzable': True},
  {'name': 'fsize', 'type': 'q', 'fuzzable': True},
  {'name': 'reserved', 'type': 's', 'size': 4, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
]

ClientDirlistRequest = [
  {'name': 'reserved', 'type': 's', 'size': 15, 'fuzzable': True},
  {'name': 'options', 'type': 'c', 'size': 1, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
  {'name': 'path', 'type': 's', 'size': 'dlen', 'fuzzable': True},
]

ClientEndsessRequest = [
  {'name': 'sessid', 'type': 's', 'size': 16, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
]

ClientGetfileRequest = [
  {'name': 'options', 'type': 'l', 'fuzzable': True},
  {'name': 'reserved', 'type': 's', 'size': 8, 'fuzzable': True},
  {'name': 'buffsz', 'type': 'l', 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
]

ClientLocateRequest = [
  {'name': 'options', 'type': 'H', 'fuzzable': True},
  {'name': 'reserved', 'type': 's', 'size': 14, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
  {'name': 'path', 'type': 's', 'size': 'dlen', 'fuzzable': True},
]

ClientLoginRequest = [
  {'name': 'pid', 'type': 'l', 'fuzzable': True},
  {'name': 'username', 'type': 's', 'size': 8, 'fuzzable': True},
  {'name': 'reserved', 'type': 's', 'size': 1, 'fuzzable': True},
  {'name': 'zone', 'type': 's', 'size': 1, 'fuzzable': True},
  {'name': 'capver', 'type': 'c', 'size': 1, 'fuzzable': True},
  {'name': 'role', 'type': 'c', 'size': 1, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
  {'name': 'token', 'type': 's', 'size': 'dlen', 'fuzzable': True},
]

ClientMkdirRequest = [
  {'name': 'options', 'type': 'c', 'size': 1, 'fuzzable': True},
  {'name': 'reserved', 'type': 's', 'size': 13, 'fuzzable': True},
  {'name': 'mode', 'type': 'H', 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
  {'name': 'path', 'type': 's', 'size': 'dlen', 'fuzzable': True},
]

ClientMvRequest = [
  {'name': 'reserved', 'type': 's', 'size': 16, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
  {'name': 'path', 'type': 's', 'size': 'dlen', 'fuzzable': True},
]

ClientOpenRequest = [
  {'name': 'mode', 'type': 'H', 'fuzzable': True},
  {'name': 'options', 'type': 'H', 'fuzzable': True},
  {'name': 'reserved', 'type': 's', 'size': 12, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
  {'name': 'path', 'type': 's', 'size': 'dlen', 'fuzzable': True},
]

ClientPingRequest = [
  {'name': 'reserved', 'type': 's', 'size': 16, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
]

ClientProtocolRequest = [
  {'name': 'clientpv', 'type': 'l', 'fuzzable': True}, # 2.9.7 or higher
  {'name': 'reserved', 'type': 's', 'size': 12, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
]

ClientPrepareRequest = [
  {'name': 'options', 'type': 'c', 'fuzzable': True},
  {'name': 'prty', 'type': 'c', 'fuzzable': True},
  {'name': 'port', 'type': 'H', 'fuzzable': True}, # 2.9.9 or higher
  {'name': 'reserved', 'type': 's', 'size': 12, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
  {'name': 'plist', 'type': 's', 'size': 'dlen', 'fuzzable': True},
]

ClientPutfileRequest = [
  {'name': 'options', 'type': 'l', 'fuzzable': True},
  {'name': 'reserved', 'type': 's', 'size': 8, 'fuzzable': True},
  {'name': 'buffsz', 'type': 'l', 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
]

ClientQueryRequest = [
  {'name': 'reqcode', 'type': 'H', 'fuzzable': True},
  {'name': 'reserved1', 'type': 's', 'size': 2, 'fuzzable': True},
  {'name': 'fhandle', 'type': 's', 'size': 4, 'fuzzable': True},
  {'name': 'reserved2', 'type': 's', 'size': 8, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
  {'name': 'args', 'type': 's', 'size': 'dlen', 'fuzzable': True},
]

ClientReadRequest = [
  {'name': 'fhandle', 'type': 's', 'size': 4, 'fuzzable': False},
  {'name': 'offset', 'type': 'q', 'fuzzable': True},
  {'name': 'rlen', 'type': 'l', 'fuzzable': False},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
]

ClientReadvRequest = [
  {'name': 'reserved', 'type': 's', 'size': 15, 'fuzzable': True},
  {'name': 'pathid', 'type': 'c', 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
  {'name': 'data', 'type': 's', 'size': 'dlen', 'fuzzable': False},
]

ClientRmRequest = [
  {'name': 'reserved', 'type': 's', 'size': 16, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
  {'name': 'path', 'type': 's', 'size': 'dlen', 'fuzzable': True},
]

ClientRmdirRequest = [
  {'name': 'reserved', 'type': 's', 'size': 16, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
  {'name': 'path', 'type': 's', 'size': 'dlen', 'fuzzable': True},
]

ClientSetRequest = [
  {'name': 'reserved', 'type': 's', 'size': 16, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
  {'name': 'data', 'type': 's', 'size': 'dlen', 'fuzzable': True},
]

ClientStatRequest = [
  {'name': 'options', 'type': 'B', 'fuzzable': True},
  {'name': 'reserved', 'type': 's', 'size': 11, 'fuzzable': True},
  {'name': 'fhandle', 'type': 's', 'size': 4, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
  {'name': 'path', 'type': 's', 'size': 'dlen', 'fuzzable': True},
]

ClientSyncRequest = [
  {'name': 'fhandle', 'type': 's', 'size': 4, 'fuzzable': True},
  {'name': 'reserved', 'type': 's', 'size': 12, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
]

ClientTruncateRequest = [
  {'name': 'fhandle', 'type': 's', 'size': 4, 'fuzzable': True},
  {'name': 'size', 'type': 'q', 'fuzzable': True},
  {'name': 'reserved', 'type': 's', 'size': 4, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
  {'name': 'path', 'type': 's', 'size': 'dlen', 'fuzzable': True},
]

ClientWriteRequest = [
  {'name': 'fhandle', 'type': 's', 'size': 4, 'fuzzable': True},
  {'name': 'offset', 'type': 'q', 'fuzzable': True},
  {'name': 'pathid', 'type': 'c', 'fuzzable': True},
  {'name': 'reserved', 'type': 's', 'size': 3, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False}, # Includes crc length
  {'name': 'data', 'type': 's', 'size': 'dlen', 'fuzzable': True},
]

ClientVerifywRequest = [
  {'name': 'fhandle', 'type': 's', 'size': 4, 'fuzzable': True},
  {'name': 'offset', 'type': 'q', 'fuzzable': True},
  {'name': 'pathid', 'type': 'c', 'fuzzable': True},
  {'name': 'vertype', 'type': 'c', 'fuzzable': True}, # One of XVerifyType
  {'name': 'reserved', 'type': 's', 'size': 2, 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False}, # Includes crc length
  {'name': 'data', 'type': 's', 'size': 'dlen', 'fuzzable': True},
]

readahead_list = [
  {'name': 'fhandle2', 'type': 's', 'size': 4, 'fuzzable': True},
  {'name': 'rlen2', 'type': 'l', 'fuzzable': True},
  {'name': 'roffset2', 'type': 'q', 'fuzzable': True},
]

read_list = [
  {'name': 'fhandle', 'type': 's', 'size': 4, 'fuzzable': True},
  {'name': 'len', 'type': 'l', 'fuzzable': True},
  {'name': 'offset', 'type': 'q', 'fuzzable': True},
]

read_args = [
  {'name': 'pathid', 'type': 's', 'fuzzable': False},
  {'name': 'reserved', 'type': 's', 'size': 7, 'fuzzable': True},
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
  {'name': 'streamid', 'type': 'H', 'fuzzable': True},
  {'name': 'status', 'type': 'H', 'fuzzable': True},
  {'name': 'dlen', 'type': 'l', 'fuzzable': False},
]

ServerResponseBody_Bind = [
  {'name': 'pathid', 'type': 'c', 'fuzzable': True},
]

ServerResponseBody_Open = [
  {'name': 'fhandle', 'type': 's', 'size': 4, 'fuzzable': True},
  {'name': 'cpsize', 'type': 'l'}, # cpsize & cptype returned if kXR_compress *or*
  {'name': 'cptype', 'type': 's', 'size': 4}, # kXR_retstat is specified
  {'name': 'data', 'type': 's', 'size': 'dlen', 'offset': 12, 'fuzzable': False},
] # info will follow if kXR_retstat is specified

ServerResponseBody_Protocol = [
  {'name': 'pval', 'type': 'l', 'fuzzable': True},
  {'name': 'flags', 'type': 'l', 'fuzzable': False},
]

ServerResponseBody_Login = [
  {'name': 'sessid', 'type': 's', 'size': 16, 'fuzzable': True},
  {'name': 'sec', 'type': 's', 'size': 'dlen', 'offset': 16, 'fuzzable': False},
]

ServerResponseBody_Redirect = [
  {'name': 'port', 'type': 'l', 'fuzzable': True},
  {'name': 'host', 'type': 's', 'size': 'dlen', 'offset': 4, 'fuzzable': False},
]

ServerResponseBody_Error = [
  {'name': 'errnum', 'type': 'l', 'fuzzable': True},
  {'name': 'errmsg', 'type': 's', 'size': 'dlen', 'offset': 4, 'fuzzable': False},
]

ServerResponseBody_Wait = [
  {'name': 'seconds', 'type': 'l', 'fuzzable': True},
  {'name': 'infomsg', 'type': 's', 'size': 'dlen', 'offset': 4, 'fuzzable': False},
]

ServerResponseBody_Waitresp = [
  {'name': 'seconds', 'type': 'l', 'fuzzable': True},
]

ServerResponseBody_Attn = [
  {'name': 'actnum', 'type': 'l', 'fuzzable': True},
  {'name': 'parms', 'type': 's', 'size': 'dlen', 'offset': 4, 'fuzzable': False},
]

ServerResponseBody_Attn_asyncrd = [
  {'name': 'actnum', 'type': 'l', 'fuzzable': True},
  {'name': 'port', 'type': 'l', 'fuzzable': True},
  {'name': 'host', 'type': 's', 'size': 'dlen', 'offset': 8, 'fuzzable': False},
]

ServerResponseBody_Attn_asynresp = [
  {'name': 'actnum', 'type': 'l', 'fuzzable': True},
  {'name': 'reserved', 'type': 's', 'size': 4, 'fuzzable': True},
  {'name': 'rsid', 'type': 'H', 'fuzzable': True},
  {'name': 'rstatus', 'type': 'H', 'fuzzable': True},
  {'name': 'rlen', 'type': 'l', 'fuzzable': True},
  {'name': 'rdata', 'type': 's', 'size': 'dlen', 'offset': 16, 'fuzzable': False},
]

ServerResponseBody_Attn_asyncwt = [
  {'name': 'actnum', 'type': 'l', 'fuzzable': True},
  {'name': 'wsec', 'type': 'l', 'fuzzable': True},
]

ServerResponseBody_Attn_asyncdi = [
  {'name': 'actnum', 'type': 'l', 'fuzzable': True},
  {'name': 'wsec', 'type': 'l', 'fuzzable': True},
  {'name': 'msec', 'type': 'l', 'fuzzable': True},
]

ServerResponseBody_Authmore = [
  {'name': 'data', 'type': 's', 'size': 'dlen', 'fuzzable': False},
]

ServerResponseBody_Buffer = [
  {'name': 'data', 'type': 's', 'size': 'dlen', 'fuzzable': False},
]

ServerResponseBody_Dirlist = [
  {'name': 'data', 'type': 's', 'size': 'dlen', 'fuzzable': False},
]

ServerResponseBody_Locate = [
  {'name': 'data', 'type': 's', 'size': 'dlen', 'fuzzable': False},
]

ServerResponseBody_Prepare = [
  {'name': 'data', 'type': 's', 'size': 'dlen', 'fuzzable': False},
]

ServerResponseBody_Query = [
  {'name': 'data', 'type': 's', 'size': 'dlen', 'fuzzable': False},
]

ServerResponseBody_Read = [
  {'name': 'data', 'type': 's', 'size': 'dlen', 'fuzzable': False},
]

ServerResponseBody_Readv = [
  {'name': 'data', 'type': 's', 'size': 'dlen', 'fuzzable': False},
]

ServerResponseBody_Set = [
  {'name': 'data', 'type': 's', 'size': 'dlen', 'fuzzable': False},
]

ServerResponseBody_Stat = [
  {'name': 'data', 'type': 's', 'size': 'dlen', 'fuzzable': False},
]

ServerResponseBody_Statx = [
  {'name': 'data', 'type': 's', 'size': 'dlen', 'fuzzable': False},
]

# The fields to be sent as initial handshake
ClientInitHandShake = [
  {'name': 'first', 'type': 'l', 'fuzzable': False},
  {'name': 'second', 'type': 'l', 'fuzzable': False},
  {'name': 'third', 'type': 'l', 'fuzzable': False},
  {'name': 'fourth', 'type': 'l', 'fuzzable': False},
  {'name': 'fifth', 'type': 'l', 'fuzzable': True},
]

# The body received after the first handshake's header
ServerInitHandShake = [
  {'name': 'protover', 'type': 'l', 'fuzzable': True},
  {'name': 'msgval', 'type': 'l', 'fuzzable': True},
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
