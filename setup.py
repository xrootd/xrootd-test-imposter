from distutils.core import setup, Extension

setup(name="authbind", version="1.0",
      ext_modules=[Extension(
                            "authbind", ["bind/authbind.cc"],
                            extra_objects=["-lXrdUtils"],
                            include_dirs=["/usr/include/xrootd"]
                            )])
