import re
import os
#
from gub import build
from gub import cross
from gub import loggedos
from gub import misc

class Binutils (cross.AutoBuild):
    source = 'http://ftp.gnu.org/pub/gnu/binutils/binutils-2.25.tar.bz2'
    patches = []
    dependencies = [
        'tools::zlib',
        'tools::texinfo',
            ]
    # Block usage of libz.so during configure, which may not be
    # available in the library path.
    config_cache_overrides = cross.AutoBuild.config_cache_overrides + '''
ac_cv_search_zlibVersion=
'''
    configure_flags = (cross.AutoBuild.configure_flags
                       + ' --disable-werror'
                       + ' --cache-file=%(builddir)s/config.cache'
                       )
    configure_variables = (cross.AutoBuild.configure_variables
                           + misc.join_lines ('''
LDFLAGS='-L%(tools_prefix)s/lib %(rpath)s %(libs)s'
'''))
    # binutils' makefile uses:
    #     MULTIOSDIR = `$(CC) $(LIBCFLAGS) -print-multi-os-directory`
    # which differs on each system.  Setting it avoids inconsistencies.
    make_flags = misc.join_lines ('''
MULTIOSDIR=../../lib
''')

    def install (self):
        cross.AutoBuild.install (self)
        install_missing_plain_binaries (self)
        install_librestrict_stat_helpers (self)

def add_g_file_names (logger, file_name):
    dir_name = os.path.dirname (file_name)
    base_name = os.path.basename (file_name)
    gnu_base_name = 'g' + base_name
    if '-' in base_name:
        gnu_base_name = re.sub ('-([^/g][^/-]*)$', r'-g\1', base_name)
    gnu_file_name = os.path.join (dir_name, gnu_base_name)
    loggedos.link (logger, file_name, gnu_file_name)

def install_librestrict_stat_helpers (self):
    # LIBRESTRICT stats PATH to find gnm and gstrip
    for d in [
        '%(install_prefix)s%(cross_dir)s/bin',
        '%(install_prefix)s%(cross_dir)s/%(target_architecture)s/bin',
        ]:
        self.map_find_files (add_g_file_names, d, '(^|.*/)([^/g][^-/]*|.*-[^/g][^-/]*)$')

def install_missing_plain_binaries (self):
    def copy (logger, full_name):
        base_name = (os.path.basename (self.expand (full_name))
                     .replace (self.expand ('%(toolchain_prefix)s'), ''))
        plain_name = self.expand ('%(install_prefix)s%(cross_dir)s/%(target_architecture)s/bin/%(base_name)s', env=locals ())
        if not os.path.exists (plain_name):
            loggedos.system (logger, 'cp %(full_name)s %(plain_name)s' % locals ())
    self.map_find_files (copy, '%(install_prefix)s%(cross_dir)s/bin', self.expand ('%(toolchain_prefix)s.*'))

class Binutils__mingw (Binutils):
    dependencies = Binutils.dependencies + [
            'tools::libtool',
            'system::iconv',
            ]
    def configure (self):
        Binutils.configure (self)
        # Configure all subpackages, makes
        # w32.libtool_fix_allow_undefined to find all libtool files
        self.system ('cd %(builddir)s && make %(compile_flags)s configure-host configure-target')
        # Must ONLY do target stuff, otherwise cross executables cannot find their libraries
        self.map_locate (lambda logger, file: build.libtool_update (logger, self.expand ('%(tools_prefix)s/bin/libtool'), file), '%(builddir)s/libiberty', 'libtool')
