import os
#
from gub import build
from gub import context
from gub import cross
from gub import loggedos
from gub import misc

class Gcc (cross.AutoBuild):
    source = 'http://ftp.gnu.org/pub/gnu/gcc/gcc-4.9.4/gcc-4.9.4.tar.bz2'
    dependencies = [
        'cross/binutils',
        'system::gcc',
        'system::g++',
        'tools::gmp',
        'tools::mpfr',
        'tools::mpc',
        'tools::gawk',
    ]
    patches = ['gcc-4.8.2-libstdc++-debug-path.patch']
    configure_command = (''' LDFLAGS='-L%(tools_prefix)s/lib %(rpath)s' '''
                         + cross.AutoBuild.configure_command)
    configure_flags = (cross.AutoBuild.configure_flags
                + '%(enable_languages)s'
                + ' --enable-static'
                + ' --enable-shared'
                + ' --with-as=%(cross_prefix)s/bin/%(target_architecture)s-as'
                + ' --with-ld=%(cross_prefix)s/bin/%(target_architecture)s-ld'
                + ' --with-nm=%(cross_prefix)s/bin/%(target_architecture)s-nm'
                )
    make_flags = misc.join_lines ('''
tooldir='%(cross_prefix)s/%(target_architecture)s'
gcc_tooldir='%(prefix_dir)s/%(target_architecture)s'
''')
    def patch (self):
        cross.AutoBuild.patch (self)
        self.file_sub ([('( *gcc_cv_tool_dirs=.*gcc_cv_tool_dirs/usr)', r'#\1')],
                        '%(srcdir)s/configure')
    @context.subst_method
    def NM_FOR_TARGET (self):
         return '%(toolchain_prefix)snm'
        # FIXME: why no -devel package?
    subpackage_names = ['doc', 'c++-runtime', 'runtime', '']
    def get_subpackage_definitions (self):
        d = cross.AutoBuild.get_subpackage_definitions (self)
        prefix_dir = self.settings.prefix_dir
        d['c++-runtime'] = [
            prefix_dir + '/lib/libstdc++.so*',
            prefix_dir + '/lib/libgcc_s.so*',
        ]
        return d
    def languages (self):
        return ['c', 'c++']
    @context.subst_method
    def enable_languages (self):
        flags = ' --enable-languages=' + ','.join (self.languages ()) 
        if 'c++' in self.languages ():
            flags += ' --enable-libstdcxx-debug'
        return flags
    def pre_install (self):
        cross.AutoBuild.pre_install (self)
        # Only id <PREFIX>/<TARGET-ARCH>/bin exists, gcc's install installs
        # the plain gcc drivers without <TOOLCHAIN-PREFIX>gcc
        self.system ('mkdir -p %(install_root)s%(prefix_dir)s/%(target_architecture)s/bin')
    def install (self):
        cross.AutoBuild.install (self)
        move_target_libs (self, '%(install_prefix)s%(cross_dir)s/%(target_architecture)s')
        move_target_libs (self, '%(install_prefix)s%(cross_dir)s/lib')
        self.disable_libtool_la_files ('stdc[+][+]')

def move_target_libs (self, libdir):
    self.system ('mkdir -p %(install_prefix)s/lib || true')
    def move_target_lib (logger, file_name):
        base = os.path.split (self.expand (file_name))[1]
        loggedos.rename (logger, file_name, os.path.join (self.expand ('%(install_prefix)s/lib'), base))
    # .so* because version numbers trail .so extension.
    for suf in ['.a', '.la', '.so*', '.dylib']:
        self.map_find_files (move_target_lib, libdir, 'lib.*%(suf)s' % locals ())

class Gcc__from__source (Gcc):
    dependencies = (Gcc.dependencies
                    + ['cross/gcc-core', 'glibc-core'])
    def __init__ (self, settings, source):
        Gcc.__init__ (self, settings, source)
        if 'i686-linux' in self.settings.build_architecture:
            if 'i686-linux' in self.settings.target_architecture:
                self.configure_flags += ' --build=i686-unknown-linux-gnu '
    #FIXME: merge all configure_command settings with Gcc
    configure_flags = (Gcc.configure_flags
                + misc.join_lines ('''
--with-local-prefix=%(system_prefix)s
--disable-multilib
--disable-nls
--disable-libitm
--disable-libsanitizer
--disable-libcilkrts
--enable-threads=posix
--enable-__cxa_atexit
--enable-symvers=gnu
--enable-c99 
--enable-clocale=gnu 
--enable-long-long
'''))
    def get_conflict_dict (self):
        return {'': ['cross/gcc-core'], 'doc': ['cross/gcc-core'], 'runtime': ['cross/gcc-core']}
    def install (self):
        Gcc.install (self)
        self.system('''
mkdir -p %(install_prefix)s%(cross_dir)s/lib/gcc/%(target_architecture)s/%(full_version)s/include/
ln -s ../include-fixed/limits.h %(install_prefix)s%(cross_dir)s/lib/gcc/%(target_architecture)s/%(full_version)s/include/limits.h
''')

Gcc__linux = Gcc__from__source

class Gcc__linux__ppc (Gcc__linux):
    configure_flags = (Gcc__linux.configure_flags
                + misc.join_lines ('''
--disable-libatomic
--disable-libgomp
'''))

class Gcc__mingw (Gcc):
    dependencies = (Gcc.dependencies
                + ['mingw-w64-runtime']
                + ['tools::libtool'])
    configure_flags = (Gcc.configure_flags
                + misc.join_lines ('''
--enable-threads=posix
'''))
    def get_subpackage_definitions (self):
        d = cross.AutoBuild.get_subpackage_definitions (self)
        prefix_dir = self.settings.prefix_dir
        d['c++-runtime'] = [
            prefix_dir + '/bin/libstdc++-*.dll',
            prefix_dir + '/bin/libgcc_s_*.dll',
        ]
        return d
    def install (self):
        Gcc.install (self)
        self.system('''
mkdir -p %(install_prefix)s/bin/
cp %(install_prefix)s/lib/libgcc_s_*.dll %(install_prefix)s/bin/
cp %(install_prefix)s%(cross_dir)s/%(target_architecture)s/lib/libstdc++-*.dll %(install_prefix)s/bin/
'''
        )
