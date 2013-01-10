from distutils.core import setup, Extension
from os import getenv

xrdlibdir = getenv( 'XRD_LIBDIR' ) or '/usr/lib'
xrdincdir = getenv( 'XRD_INCDIR' ) or '/usr/include/xrootd'

print 'XRootD library dir:', xrdlibdir
print 'XRootD include dir:', xrdincdir

setup( name             = 'XrdImposter',
       version          = '0.1',
       author           = 'Justin Salmon, Lukasz Janyst',
       author_email     = 'jsalmon@cern.ch, ljanyst@cern.ch',
       url              = 'http://xrootd.org',
       license          = 'LGPL',
       scripts          = ['imposter.py'],
       packages         = ['XrdImposter'],
       package_dir      = {'XrdImposter': 'lib'},
       data_files       = [('share/XrdImposter/examples',
                            ['examples/XRootDLogInClient.py',
                             'examples/XRootDLogInServer.py'])],
       description      = "Implementation of the XRootD protocol",
       long_description = "Implementation of the XRootD protocol",
       ext_modules      = [
           Extension(
               'XrdImposter.XrdAuthBind',
               ['auth/XrdAuthBind.cc'],
               libraries    = ['XrdUtils', 'dl'],
               extra_compile_args = ['-g'],
               include_dirs = [xrdincdir],
               library_dirs = [xrdlibdir]
               )
           ]
       )
