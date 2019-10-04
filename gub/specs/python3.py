from gub import misc
from gub import target
from gub import tools

class Python3 (target.AutoBuild):
    source = 'https://www.python.org/ftp/python/3.7.4/Python-3.7.4.tar.xz'
    dependencies = ['tools::python3']

    force_autoupdate = True
    python_configure_flags = misc.join_lines('''
--disable-shared
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
        # Patch out error messages about untested cross build configurations.
        self.file_sub ([
            ('(AC_MSG_ERROR\(\[cross build not supported.*\]\))', '#\\1'),
            ('(AC_MSG_ERROR\(\[readelf for the host is required for cross builds\]\))', '#\\1')
        ], '%(srcdir)s/configure.ac')
        # Make setup.py work with tools::python3 as PYTHON_FOR_BUILD.
        self.file_sub ([('srcdir = sysconfig.*', 'srcdir = \'%(srcdir)s\'')],
                       '%(srcdir)s/setup.py')
        target.AutoBuild.patch (self)

disable_implicit_function_declaration_error = '''
ac_cv_enable_implicit_function_declaration_error=no
'''

class Python3__darwin (Python3):
    config_cache_overrides = (Python3.config_cache_overrides
        + disable_implicit_function_declaration_error)

class Python3__mingw (Python3):
    # Python/pylifecycle.c:460:5: error: implicit declaration of function 'setenv'
    config_cache_overrides = (Python3.config_cache_overrides
        + disable_implicit_function_declaration_error)
    def patch (self):
        # mingw only has the old definition of wcstok, replace by wcstok_s with
        # the correct signature.
        self.file_sub ([('wcstok', 'wcstok_s')], '%(srcdir)s/Python/pathconfig.c')
        # Use implementations for Windows.
        self.copy ('%(srcdir)s/PC/dl_nt.c', '%(srcdir)s/Python/dl_nt.c')
        self.file_sub ([
                ('Modules/getpath\\.c', 'PC/getpathp.c'),
                ('(Modules/_io/_iomodule\\.o)', '\\1 Modules/_io/winconsoleio.o'),
                ('(Python/importdl\\.o )', '\\1Python/dynload_win.o Python/dl_nt.o'),
            ], '%(srcdir)s/Makefile.pre.in')
        # Don't build some modules.
        self.file_sub ([
                ('^(pwd )', '# \\1'),
                ('(_io/_iomodule\\.c)', '\\1 _io/winconsoleio.c'),
            ], '%(srcdir)s/Modules/Setup.dist')
        # Fix build of posixmodule.c on Windows.
        self.file_sub ([
                ('_MSC_VER', 'MS_WINDOWS'),
                ('(#include "winreparse.h")', '\\1\n#define ALL_PROCESSOR_GROUPS 0xffff'),
            ], '%(srcdir)s/Modules/posixmodule.c')
        Python3.patch (self)
    def configure (self):
        Python3.configure (self)
        self.copy ('%(srcdir)s/PC/pyconfig.h', '%(builddir)s/pyconfig.h')
        self.copy ('%(srcdir)s/PC/errmap.h', '%(builddir)s/errmap.h')

class Python3__tools (tools.AutoBuild, Python3):
    dependencies = ['autoconf', 'automake', 'libtool']
    configure_flags = (tools.AutoBuild.configure_flags + Python3.python_configure_flags)
