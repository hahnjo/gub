import re
import os
#
from gub import misc
from gub import mirrors
from gub import sources
from gub import targetbuild
from gub import repository
from gub import loggedos

class Guile (targetbuild.TargetBuild):
    source = 'git://git.sv.gnu.org/guile.git&branch=branch_release-1-8&revision=release_1-8-4'
    
    def __init__ (self, settings, source):
        targetbuild.TargetBuild.__init__ (self, settings, source)
        if isinstance (source, repository.Repository):
            source.version = lambda: '1.8.2'
        self.so_version = '17'

    def autogen_sh (self):
        self.file_sub ([(r'AC_CONFIG_SUBDIRS\(guile-readline\)', '')],
                       '%(srcdir)s/configure.in')
        self.file_sub ([(r'guile-readline', '')],
                       '%(srcdir)s/Makefile.am')
        self.dump ('', '%(srcdir)s/doc/ref/version.texi')
        self.dump ('', '%(srcdir)s/doc/tutorial/version.texi')

    def get_subpackage_names (self):
        return ['doc', 'devel', 'runtime', '']

    def get_dependency_dict (self):
        return {
            '' : ['guile-runtime'],
            'runtime': ['gmp', 'gettext', 'libtool-runtime'],
            'devel': ['guile-runtime'],
            'doc': ['texinfo'],
            }

    def get_build_dependencies (self):
        return ['gettext-devel', 'gmp-devel', 'libtool', 'tools::guile']
        
    # FIXME: C&P.
    def guile_version (self):
        return '.'.join (self.ball_version.split ('.')[0:2])

    def patch (self):
        ## Don't apply patch twice.
        self.apply_patch ('guile-reloc.patch')
        self.apply_patch ('guile-cexp.patch')
        self.dump ('''#!/bin/sh
exec %(tools_prefix)s/bin/guile "$@"
''', "%(srcdir)s/pre-inst-guile.in")
            
        self.autogen_sh ()
        targetbuild.TargetBuild.patch (self)
        self.autoupdate ()

    def configure_flags (self):
        return misc.join_lines ('''
--without-threads
--with-gnu-ld
--enable-deprecated
--enable-discouraged
--disable-error-on-warning
--enable-relocation
--disable-rpath
''')
        
    def configure_command (self):
        return ('GUILE_FOR_BUILD=%(tools_prefix)s/bin/guile '
                + targetbuild.TargetBuild.configure_command (self)
                + self.configure_flags ())

    def compile_command (self):
        return ('preinstguile=%(tools_prefix)s/bin/guile ' +
                targetbuild.TargetBuild.compile_command (self))
    
    def compile (self):

        ## Ugh : broken dependencies barf with make -jX
        self.system ('cd %(builddir)s/libguile && make scmconfig.h')
        # No -L %(system_root)s in `guile-config link'
        self.system ('cd %(builddir)s/libguile && make libpath.h')
        self.file_sub ([('''-L *%(system_root)s''', '-L')],
                       '%(builddir)s/libguile/libpath.h')
        targetbuild.TargetBuild.compile (self)

    def configure (self):
        targetbuild.TargetBuild.configure (self)
        self.update_libtool ()

    def install (self):
        targetbuild.TargetBuild.install (self)
        majmin_version = '.'.join (self.expand ('%(version)s').split ('.')[0:2])
        
        self.dump ("prependdir GUILE_LOAD_PATH=$INSTALLER_PREFIX/share/guile/%(majmin_version)s\n",
                   '%(install_prefix)s/etc/relocate/guile.reloc',
                   env=locals ())
 
        version = self.expand ('%(version)s')
	#FIXME: c&p linux.py
        self.dump ('''\
#! /bin/sh
test "$1" = "--version" && echo "%(target_architecture)s-guile-config - Guile version %(version)s"
#test "$1" = "compile" && echo "-I $%(system_prefix)s/include"
#test "$1" = "link" && echo "-L%(system_prefix)s/lib -lguile -lgmp"
#prefix=$(dirname $(dirname $0))
prefix=%(system_prefix)s
test "$1" = "compile" && echo "-I$prefix/include"
test "$1" = "link" && echo "-L$prefix/lib -lguile -lgmp"
exit 0
''',
             '%(install_prefix)s/cross/bin/%(target_architecture)s-guile-config')
        self.chmod ('%(install_prefix)s/cross/bin/%(target_architecture)s-guile-config', 0755)

class Guile__mingw (Guile):
    def __init__ (self, settings, source):
        Guile.__init__ (self, settings, source)
        # Configure (compile) without -mwindows for console
        self.target_gcc_flags = '-mms-bitfields'

    def get_build_dependencies (self):
        return Guile.get_build_dependencies (self) +  ['regex-devel']
        
    def get_dependency_dict (self):
        d = Guile.get_dependency_dict (self)
        d['runtime'].append ('regex')
        return d

# FIXME: ugh, C&P to Guile__freebsd, put in cross-Guile?
    def configure_command (self):
        # watch out for whitespace
        builddir = self.builddir ()
        srcdir = self.srcdir ()


# don't set PATH_SEPARATOR; it will fuckup tools searching for the
# build platform.

        return (Guile.configure_command (self)
           + misc.join_lines ('''
LDFLAGS=-L%(system_prefix)s/lib
CC_FOR_BUILD="
C_INCLUDE_PATH=
CPPFLAGS=
LIBRARY_PATH=
LDFLAGS=
PATH_SEPARATOR=\\;
cc
-I%(builddir)s
-I%(srcdir)s
-I%(builddir)s/libguile
-I.
-I%(srcdir)s/libguile"
'''))

    def config_cache_overrides (self, str):
        return str + '''
guile_cv_func_usleep_declared=${guile_cv_func_usleep_declared=yes}
guile_cv_exeext=${guile_cv_exeext=}
libltdl_cv_sys_search_path=${libltdl_cv_sys_search_path="%(system_prefix)s/lib"}
'''

    def configure (self):
        if 0: # using patch
            targetbuild.TargetBuild.autoupdate (self)

        if 1:
            self.file_sub ([('''^#(LIBOBJS=".*fileblocks.*)''',
                    '\\1')],
                   '%(srcdir)s/configure')

        Guile.configure (self)
        self.file_sub ([
            #('^(allow_undefined_flag=.*)unsupported', '\\1'),
            ('-mwindows', ''),
            ],
               '%(builddir)s/libtool')

        if 0:
            # we have patched out readline.
            self.file_sub ([
                #('^(allow_undefined_flag=.*)unsupported', '\\1'),
                ('-mwindows', ''),
                ],
                           '%(builddir)s/guile-readline/libtool')

    def install (self):
        Guile.install (self)
        # dlopen-able .la files go in BIN dir, BIN OR LIB package
        self.system ('''mv %(install_prefix)s/lib/lib*[0-9].la %(install_prefix)s/bin''')

class Guile__linux (Guile):
    def compile_command (self):
        # FIXME: when not x-building, guile runs guile without
        # setting the proper LD_LIBRARY_PATH.
        return ('export LD_LIBRARY_PATH=%(builddir)s/libguile/.libs:$LD_LIBRARY_PATH;'
                + Guile.compile_command (self))

class Guile__linux__ppc (Guile__linux):
    def config_cache_overrides (self, str):
        return str + "\nguile_cv_have_libc_stack_end=no\n"

class Guile__freebsd (Guile):
    def config_cache_settings (self):
        return Guile.config_cache_settings (self) + '\nac_cv_type_socklen_t=yes'
    def configure_command (self):
        # watch out for whitespace
        builddir = self.builddir ()
        srcdir = self.srcdir ()
        return (
            ''' guile_cv_use_csqrt="no" '''
           + Guile.configure_command (self)
           + misc.join_lines ('''\
CC_FOR_BUILD="
C_INCLUDE_PATH=
CPPFLAGS=
LIBRARY_PATH=
cc
-I%(builddir)s
-I%(srcdir)s
-I%(builddir)s/libguile
-I.
-I%(srcdir)s/libguile"
'''))

class Guile__darwin (Guile):
    def install (self):
        Guile.install (self)

        def dylib_link (logger, fname):
            directory = os.path.split (fname)[0]
            src = os.path.basename (fname)
            dst = os.path.splitext (os.path.basename (fname))[0] + '.so'
            loggedos.symlink (logger, src, os.path.join (directory, dst))
                              
        self.map_locate (dylib_link,
                         self.expand ('%(install_prefix)s/lib/'),
                         'libguile-srfi*.dylib')
 
class Guile__darwin__x86 (Guile__darwin):
    def configure (self):
        Guile__darwin.configure (self)
        self.file_sub ([('guile-readline', '')],
                       '%(builddir)s/Makefile')
        
class Guile__cygwin (Guile):
    def category_dict (self):
        return {'': 'Interpreters'}

    def patch (self):
        pass

    # Using gub dependencies only would be nice, but
    # we need to a lot of gup.gub_to_distro_deps ().
    def GUB_get_dependency_dict (self):
        d = Guile.get_dependency_dict (self)
        d['runtime'].append ('cygwin')
        return d

    # Using gub dependencies only would be nice, but
    # we need to a lot of gup.gub_to_distro_deps ().
    def GUB_get_build_dependencies (self):
        return Guile.get_build_dependencies (self) + ['libiconv-devel']

    # FIXME: uses mixed gub/distro dependencies
    def get_dependency_dict (self):
        d = Guile.get_dependency_dict (self)
        d[''] += ['cygwin']
        d['devel'] += ['cygwin'] + ['bash']
        d['runtime'] += ['cygwin', 'crypt', 'libreadline6']
        return d
 
    # FIXME: uses mixed gub/distro dependencies
    def get_build_dependencies (self):
        return ['crypt', 'libgmp-devel', 'gettext-devel', 'libiconv', 'libtool', 'readline']

    def config_cache_overrides (self, str):
        return str + '''
guile_cv_func_usleep_declared=${guile_cv_func_usleep_declared=yes}
guile_cv_exeext=${guile_cv_exeext=}
libltdl_cv_sys_search_path=${libltdl_cv_sys_search_path="%(system_prefix)s/lib"}
'''
    def configure (self):
        if 1:
            self.file_sub ([('''^#(LIBOBJS=".*fileblocks.*)''', '\\1')],
                           '%(srcdir)s/configure')
        Guile.configure (self)

        self.file_sub ([
            ('^(allow_undefined_flag=.*)unsupported', '\\1'),
            ],
               '%(builddir)s/libtool')
        self.file_sub ([
            ('^(allow_undefined_flag=.*)unsupported', '\\1'),
            ],
               '%(builddir)s/guile-readline/libtool')

    def description_dict (self):
        return {
            '': """The GNU extension language and Scheme interpreter - executables
Guile, the GNU Ubiquitous Intelligent Language for Extension, is a scheme
implementation designed for real world programming, supporting a
rich Unix interface, a module system, and undergoing rapid development.

`guile' is a scheme interpreter that can execute scheme scripts (with a
#! line at the top of the file), or run as an inferior scheme
process inside Emacs.
""",
            'runtime': '''The GNU extension language and Scheme interpreter - runtime
Guile shared object libraries and the ice-9 scheme module.  Guile is
the GNU Ubiquitous Intelligent Language for Extension.
''',
            'devel': """The GNU extension language and Scheme interpreter - development
`libguile.h' etc. C headers, aclocal macros, the `guile-snarf' and
`guile-config' utilities, and static `libguile.a' libraries for Guile,
the GNU Ubiquitous Intelligent Language for Extension.
""",
            'doc': """The GNU extension language and Scheme interpreter - documentation
This package contains the documentation for guile, including both
a reference manual (via `info guile'), and a tutorial (via `info
guile-tut').
""",
    }

from gub import toolsbuild
from gub import build
class Guile__tools (toolsbuild.ToolsBuild, Guile):
    source = Guile.source
    def get_build_dependencies (self):
        return (toolsbuild.ToolsBuild.get_build_dependencies (self)
                + Guile.get_build_dependencies (self)
                + ['autoconf', 'automake', 'gettext', 'libtool'])

    def patch (self):
        self.autogen_sh ()
        self.autoupdate ()

    def configure_command (self):
        return (toolsbuild.ToolsBuild.configure_command (self)
                + self.configure_flags ())

    def configure (self):
        toolsbuild.ToolsBuild.configure (self)
#        self.update_libtool ()

    def install (self):
        ## guile runs fine without wrapper (if it doesn't, use the
        ## relocation patch), while a sh wrapper breaks executable
        ## scripts toolsbuild.ToolsBuild.install (self)
        build.UnixBuild.install (self)

        ## don't want tools GUILE headers to interfere with compile.
        self.system ("rm -rf %(install_root)s%(packaging_suffix_dir)s%(prefix_dir)s/include/ %(install_root)s%(packaging_suffix_dir)s%(prefix_dir)s/bin/guile-config ")
