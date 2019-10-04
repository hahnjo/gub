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
        # Make setup.py work with tools::python3 as PYTHON_FOR_BUILD.
        self.file_sub ([('srcdir = sysconfig.*', 'srcdir = \'%(srcdir)s\'')],
                       '%(srcdir)s/setup.py')
        target.AutoBuild.patch (self)

class Python3__tools (tools.AutoBuild, Python3):
    dependencies = ['autoconf', 'automake', 'libtool']
    configure_flags = (tools.AutoBuild.configure_flags + Python3.python_configure_flags)
