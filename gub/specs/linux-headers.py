from gub import gubb
from gub import mirrors

class Linux_headers (gubb.BinarySpec, gubb.SdkBuildSpec):
    def __init__ (self, settings):
        gubb.BinarySpec.__init__ (self, settings)
        self.with_tarball (mirror=mirrors.linux_2_4,
                           version='2.4.34', format='bz2')
    def get_subpackage_names (self):
        return ['']
    def patch (self):
        self.system ('''
cd %(srcdir)s && yes yes | make ARCH=%(package_arch)s oldconfig symlinks include/linux/version.h
#cd %(srcdir)s && yes yes | make ARCH=i386 oldconfig
#cd %(srcdir)s && make ARCH=%(package_arch)s symlinks include/linux/version.h
cd %(srcdir)s && mv include .include
cd %(srcdir)s && rm -rf *
cd %(srcdir)s && mkdir usr
cd %(srcdir)s && mv .include usr/include
cd %(srcdir)s && rm -f\
 usr/include/scsi/sg.h\
 usr/include/scsi/scsi.h\
 usr/include/scsi/scsi_ioctl.h\
 usr/include/net/route.h
''')

from gub import misc
linux_kernel_headers = misc.load_spec ('debian/linux-kernel-headers')

class Linux_headers__debian (linux_kernel_headers.Linux_kernel_headers):
    def __init__ (self, settings):
        linux_kernel_headers.Linux_kernel_headers.__init__ (self, settings)
        from gub import debian
#        debian.init_dependency_resolver (settings)
        self.with (
            name='linux-kernel-headers',
# FIXME: we do not mirror all 12 debian arch's,
#           version=debian.get_packages ()['linux-kernel-headers'].version (),
#           mirror=mirrors.lilypondorg_deb,
            version='2.5.999-test7-bk-17',
            mirror=mirrors.lkh_deb,
            strip_components=0,
            format='deb')

Linux_headers__linux__ppc = Linux_headers__debian
#Linux_headers__linux__64 = Linux_headers__debian
Linux_headers__linux__arm__softfloat = Linux_headers__debian
Linux_headers__linux__arm__vfp = Linux_headers__debian

class Linux_headers__linux__64 (Linux_headers__debian):
    def __init__ (self, settings):
        Linux_headers__debian.__init__ (self, settings)
        self.with (version='2.6.18-7', name='linux-kernel-headers')