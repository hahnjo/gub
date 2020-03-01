import sys
#
from gub import tools
from gub import misc

def get_cross_build_dependencies (settings):
    return []

class AutoBuild (tools.AutoBuild):
    def get_substitution_dict (self, env={}):
        dict = {
            'AS': 'as --32',
            'CC': 'gcc -m32',
            'CXX':'g++ -m32',
        }
        dict.update (env)
        d = tools.AutoBuild.get_substitution_dict (self, dict).copy ()
        return d

class MakeBuild (AutoBuild):
    def stages (self):
        return [s.replace ('configure', 'shadow') for s in AutoBuild.stages (self) if s not in ['autoupdate']]

class ShBuild (AutoBuild):
    def stages (self):
        return [s.replace ('configure', 'shadow') for s in AutoBuild.stages (self) if s not in ['autoupdate']]
    compile_command = 'bash build.sh %(make_flags)s %(compile_flags)s'
    install_command = '%%%override-me'

class PythonBuild (AutoBuild):
    def stages (self):
        return [s for s in AutoBuild.stages (self) if s not in ['autoupdate', 'configure']]
    def compile (self):
        self.system ('mkdir -p %(builddir)s')
    install_command = sys.executable + ' %(srcdir)s/setup.py install --prefix=%(tools_prefix)s --root=%(install_root)s'

class SConsBuild (AutoBuild):
    scons_flags = ''
    def stages (self):
        return [s for s in AutoBuild.stages (self) if s not in ['autoupdate', 'configure']]
        # SCons barfs on trailing / on directory names
    compile_command = ('scons PREFIX=%(system_prefix)s'
                ' PREFIX_DEST=%(install_root)s'
                ' %(compile_flags)s'
                ' %(scons_flags)s')
    install_command = compile_command + ' %(install_flags)s'

class NullBuild (AutoBuild):
    def stages (self):
        return ['patch', 'install', 'package', 'clean']
    subpackage_names = ['']
    def install (self):
        self.system ('mkdir -p %(install_prefix)s')

class BinaryBuild (AutoBuild):
    def stages (self):
        return ['untar', 'install', 'package', 'clean']
    def install (self):
        self.system ('mkdir -p %(install_root)s')
        _v = '' #self.os_interface.verbose_flag ()
        self.system ('tar -C %(srcdir)s -cf- . | tar -C %(install_root)s%(_v)s -p -xf-', env=locals ())
        self.libtool_installed_la_fixups ()
    subpackage_names = ['']
        
class CpanBuild (AutoBuild):
    def stages (self):
        return [s for s in AutoBuild.stages (self) if s not in ['autoupdate']]
    def configure (self):
        self.shadow ()
        self.system ('cd %(builddir)s && perl Makefile.PL PREFIX=%(system_prefix)s LINKTYPE=dynamic')
