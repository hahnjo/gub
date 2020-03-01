import os
#
from gub import build
from gub import context
from gub import gub_log
from gub import misc
from gub import octal
from gub import target
from gub import tools

class Fontconfig (target.AutoBuild):
    '''Generic font configuration library 
Fontconfig is a font configuration and customization library, which
does not depend on the X Window System.  It is designed to locate
fonts within the system and select them according to requirements
specified by applications.'''

    source = 'http://fontconfig.org/release/fontconfig-2.12.6.tar.bz2'
    patches = [
        'fontconfig-2.11.1-conf-relative-symlink.patch',
    ]
    dependencies = [
        'libtool',
        'expat-devel',
        'freetype-devel',
        'tools::freetype',
        'tools::pkg-config',
        'tools::bzip2',
        'tools::gperf'
    ]
        # FIXME: system dir vs packaging install
        ## UGH  - this breaks  on Darwin!
        ## UGH2 - the added /cross/ breaks Cygwin; possibly need
        ## Freetype_config package (see Guile_config, Python_config)
        # FIXME: this is broken.  for a sane target development package,
        # we want /usr/bin/fontconfig-config must survive.
        # While cross building, we create an  <toolprefix>-fontconfig-config
        # and prefer that.
    configure_flags = (target.AutoBuild.configure_flags
                + misc.join_lines ('''
--with-arch=%(target_architecture)s
--with-freetype-config="%(system_prefix)s%(cross_dir)s/bin/freetype-config
--prefix=%(system_prefix)s
"'''))
    def __init__ (self, settings, source):
        target.AutoBuild.__init__ (self, settings, source)
        if 'stat' in misc.librestrict ():
            build.add_dict (self, {'LIBRESTRICT_IGNORE': '%(tools_prefix)s/bin/bash:%(tools_prefix)s/bin/make'})
            # build.add_dict (self, {'LIBRESTRICT_VERBOSE': '1'})
    def patch (self):
        self.dump ('\nAC_SUBST(LT_AGE)', '%(srcdir)s/configure.in', mode='a', permissions=octal.o755)
        target.AutoBuild.patch (self)
        # https://bugs.freedesktop.org/show_bug.cgi?id=101280
        self.system('rm -f %(srcdir)s/src/fcobjshash.h')
    @context.subst_method
    def freetype_cflags (self):
        # this is shady: we're using the flags from the tools version
        # of freetype.
        base_config_cmd = self.settings.expand ('%(tools_prefix)s/bin/freetype-config')
        cmd =  base_config_cmd + ' --cflags'
        gub_log.command ('pipe %s\n' % cmd)
        # ugh, this is utterly broken.  we're reading from the
        # filesystem init time, when freetype-config does not exist
        # yet.
        # return misc.read_pipe (cmd).strip ()
        return '-I%(system_prefix)s/include/freetype2'
    @context.subst_method
    def freetype_libs (self):
        base_config_cmd = self.settings.expand ('%(tools_prefix)s/bin/freetype-config')
        cmd =  base_config_cmd + ' --libs'
        gub_log.command ('pipe %s\n' % cmd)
        # return misc.read_pipe (cmd).strip ()
        return '-lfreetype -lz'
    def configure (self):
        self.system ('''
rm -f %(srcdir)s/builds/unix/{unix-def.mk,unix-cc.mk,ftconfig.h,freetype-config,freetype2.pc,config.status,config.log}
''')
        target.AutoBuild.configure (self)
        self.file_sub ([('DOCSRC *=.*', 'DOCSRC=')],
                       '%(builddir)s/Makefile')
    make_flags = ('man_MANS=' # either this, or add something like tools::docbook-utils
                # librestrict: stuff in fc-case, fc-lang is FOR-BUILD and has
                # dependencies .deps/*.Po /usr/include/stdio.h: 
                + ''' 'SUBDIRS=fontconfig src fc-cache fc-cat fc-list fc-match conf.d' ''')
    def compile (self):
        # help fontconfig cross compiling a bit, all CC/LD
        # flags are wrong, set to the target's root
        ## we want native freetype-config flags here. 
        cflags = '-I%(srcdir)s -I%(srcdir)s/src %(freetype_cflags)s' 
        libs = '%(freetype_libs)s'
        relax = ''
        if 'stat' in misc.librestrict ():
            relax = 'LIBRESTRICT_IGNORE=%(tools_prefix)s/bin/bash:%(tools_prefix)s/bin/make '
        for i in ('fc-case', 'fc-lang'):
            self.system ('''
cd %(builddir)s/%(i)s && %(relax)s make "CFLAGS=%(cflags)s" "LIBS=%(libs)s" CPPFLAGS= LD_LIBRARY_PATH=%(tools_prefix)s/lib LDFLAGS=-L%(tools_prefix)s/lib INCLUDES=
''', locals ())
        target.AutoBuild.compile (self)
    def install (self):
        target.AutoBuild.install (self)
        self.dump ('''\
set? FONTCONFIG_FILE=$INSTALLER_PREFIX/etc/fonts/fonts.conf
set? FONTCONFIG_PATH=$INSTALLER_PREFIX/etc/fonts
''',
             '%(install_prefix)s/etc/relocate/fontconfig.reloc')
        # Stuff for using fontconfig within gub.  We simply make fontconfig
        # load the configuration from `tools' and add another font
        # directory.  Note that fontconfig's cache files are platform
        # dependent and can't be shared across architectures.
        self.system ('''
mkdir -p %(install_prefix)s/etc/fonts-gub \
&& mkdir -p %(install_prefix)s/var/cache/fontconfig-gub
''')
        self.dump ('''\
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <include>%(tools_prefix)s/etc/fonts-gub/fonts.conf</include>

  <!-- GUB's internal font directory -->
  <dir>%(system_prefix)s/share/fonts</dir>

  <cachedir>%(system_prefix)s/var/cache/fontconfig-gub</cachedir>

</fontconfig>
''',
            '%(install_prefix)s/etc/fonts-gub/fonts.conf')

class Fontconfig__mingw (Fontconfig):
    def patch (self):
        Fontconfig.patch (self)
        self.file_sub ([('<cachedir>@FC_CACHEDIR@</cachedir>', '')],
                       '%(srcdir)s/fonts.conf.in')

    def configure (self):
        Fontconfig.configure (self)
        self.dump ('''
#define sleep(x) _sleep (x)
''',
                   '%(builddir)s/config.h',
                   mode='a')

class Fontconfig__darwin (Fontconfig):
    configure_flags = (Fontconfig.configure_flags
                         + ' --with-add-fonts=/Library/Fonts,/System/Library/Fonts ')
    def configure (self):
        Fontconfig.configure (self)

class Fontconfig__linux (Fontconfig):
    def configure (self):
        Fontconfig.configure (self)
        self.file_sub ([
            ('^sys_lib_search_path_spec="/lib/* ',
            'sys_lib_search_path_spec="%(system_prefix)s/lib /lib '),
            # FIXME: typo: dl_search (only dlsearch exists).
            # comment-out for now
            #('^sys_lib_dl_search_path_spec="/lib/* ',
            # 'sys_lib_dl_search_path_spec="%(system_prefix)s/lib /lib ')
            ],
               '%(builddir)s/libtool')

class Fontconfig__freebsd (Fontconfig__linux):
    pass

class Fontconfig__tools (tools.AutoBuild):
    # FIXME: use mi to get to source?
    #source = 'git://anongit.freedesktop.org/git/fontconfig?revision=' + version
    source = Fontconfig.source
    patches = Fontconfig.patches
    def patch (self):
        self.dump ('\nAC_SUBST(LT_AGE)', '%(srcdir)s/configure.in', mode='a', permissions=octal.o755)
        tools.AutoBuild.patch (self)
        # https://bugs.freedesktop.org/show_bug.cgi?id=101280
        self.system('rm -f %(srcdir)s/src/fcobjshash.h')
    dependencies = [
        'libtool',
        'freetype',
        'expat',
        'pkg-config',
        'bzip2',
        'gperf'
    ]
    make_flags = ('man_MANS=' # either this, or add something like tools::docbook-utils
                + ' DOCSRC="" ')
    def install (self):
        tools.AutoBuild.install (self)
        # For reproducible builds we must not access files outside of the
        # gub directory tree.  We thus set up a separate configuration in
        # the `tools' tree for fontconfig, to be activated by appropriately
        # adjusting the environment variables FONTCONFIG_FILE and
        # FONTCONFIG_PATH (which are defined with `set?' instead of `set' in
        # the `fontconfig.reloc' file to make this possible).
        self.system ('''\
mkdir -p %(install_prefix)s/etc/fonts-gub \
&& cd %(install_prefix)s/etc/fonts-gub \
&& mkdir -p conf.d \
&& cd conf.d \
&& for f in 10-hinting-slight.conf \
            30-metric-aliases.conf \
            40-nonlatin.conf \
            45-latin.conf \
            49-sansserif.conf \
            60-latin.conf \
            65-fonts-persian.conf \
            65-nonlatin.conf \
            69-unifont.conf \
            70-no-bitmaps.conf \
            80-delicious.conf \
            90-synthetic.conf; do \
     ln -sr %(install_prefix)s/share/fontconfig/conf.avail/$f $f; \
   done
''')
        self.dump ('''\
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">

<fontconfig>
  <match target="pattern">
    <test qual="any" name="family">
      <string>mono</string>
    </test>
    <edit name="family" mode="assign" binding="same">
      <string>monospace</string>
    </edit>
  </match>

  <match target="pattern">
    <test qual="any" name="family">
      <string>sans serif</string>
    </test>
    <edit name="family" mode="assign" binding="same">
      <string>sans-serif</string>
    </edit>
  </match>

  <match target="pattern">
    <test qual="any" name="family">
      <string>sans</string>
    </test>
    <edit name="family" mode="assign" binding="same">
      <string>sans-serif</string>
    </edit>
  </match>

  <include>conf.d</include>

  <config>
    <rescan>
      <int>30</int>
    </rescan>
  </config>
</fontconfig>
''',
            '%(install_prefix)s/etc/fonts-gub/fonts.conf')
        self.dump ('''\
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <!-- GUB's internal font directory -->
  <dir>%(tools_prefix)s/share/fonts</dir>
</fontconfig>
''',
            '%(install_prefix)s/etc/fonts-gub/conf.d/08-gub-fonts-dir.conf')
