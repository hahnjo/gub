from gub import build
from gub import misc
from gub import target
from gub import tools

PYTHON_VERSION_MAJOR = '3.7'
PYTHON_VERSION_PATCH = '4'
PYTHON_VERSION = '%s.%s' % (PYTHON_VERSION_MAJOR, PYTHON_VERSION_PATCH)
PYTHON_SRC = 'https://www.python.org/ftp/python/%(ver)s/Python-%(ver)s.tar.xz' % {'ver': PYTHON_VERSION}
PYTHON_WIN = 'https://www.python.org/ftp/python/%(ver)s/python-%(ver)s-embed-win32.zip' % {'ver': PYTHON_VERSION}

class Python3 (target.AutoBuild):
    source = PYTHON_SRC
    dependencies = ['tools::python3']

    python_configure_flags = misc.join_lines('''
--disable-shared
--enable-static
--without-ensurepip
''')
    configure_flags = (target.AutoBuild.configure_flags + python_configure_flags
        + misc.join_lines('''
--disable-ipv6
PYTHON_FOR_BUILD=%(tools_prefix)s/bin/python3
'''))
# Adding --disable-ipv6 is a simple "fix" for Python 3.7.4 complaining:
#    checking getaddrinfo bug... yes
#    Fatal: You must get working getaddrinfo() function.
#           or you can specify "--disable-ipv6".
# This might be because our glibc is too old. As we don't do network, this
# shouldn't be too bad...

    def patch (self):
        # Make setup.py work with tools::python3 as PYTHON_FOR_BUILD.
        self.file_sub ([('srcdir = sysconfig.*', 'srcdir = \'%(srcdir)s\'')],
                       '%(srcdir)s/setup.py')
        target.AutoBuild.patch (self)

class Python3__darwin (Python3):
    patches = Python3.patches + [
        'python-3.7.4-configure.ac-darwin.patch'
    ]
    force_autoupdate = True
    configure_flags = Python3.configure_flags + misc.join_lines('''
READELF=/usr/bin/readelf
MACOSX_DEPLOYMENT_TARGET=10.3
''')

class Python3__mingw (build.BinaryBuild):
    source = PYTHON_WIN

    python_zip = 'python%s.zip' % PYTHON_VERSION_MAJOR.replace ('.', '')
    def install (self):
        self.system ('''
mkdir -p %(install_prefix)s/bin
cp %(srcdir)s/*.exe %(install_prefix)s/bin/
cp %(srcdir)s/*.dll %(install_prefix)s/bin/
cp %(srcdir)s/*.pyd %(install_prefix)s/bin/
cp %(srcdir)s/%(python_zip)s -d %(install_prefix)s/bin/
''')

class Python3__tools (tools.AutoBuild, Python3):
    configure_flags = (tools.AutoBuild.configure_flags + Python3.python_configure_flags)
