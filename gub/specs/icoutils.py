from gub import tools

class Icoutils__tools (tools.AutoBuild):
    source = 'http://download.savannah.gnu.org/releases/icoutils/icoutils-0.31.0.tar.bz2'
    dependencies = ['libpng-devel', 'tools::bzip2']
    configure_flags = (tools.AutoBuild.configure_flags
                       + ' --with-libintl-prefix=%(system_prefix)s'
                       + ' --disable-nls')

class Icoutils__darwin (tools.AutoBuild):
    def patch (self):
        for f in 'wrestool', 'icotool':
            self.file_sub ([(r'\$\(LIBS\)', '$(INTLLIBS) $(LIBS)')],
                           '%(srcdir)s/' + f + "/Makefile.in")

Icoutils__darwin__x86 = Icoutils__darwin
