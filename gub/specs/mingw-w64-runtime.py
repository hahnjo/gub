from gub import build

class Mingw_w64_runtime (build.BinaryBuild, build.SdkBuild):
    source = 'https://sourceforge.net/projects/mingw-w64/files/Toolchains%%20targetting%%20Win32/Personal%%20Builds/mingw-builds/5.4.0/threads-posix/sjlj/i686-5.4.0-release-posix-sjlj-rt_v5-rev0.7z'
    dependencies = [ 'tools::p7zip' ]
    subpackage_names = ['winpthread-dll', '']
    def get_subpackage_definitions (self):
        d = build.BinaryBuild.get_subpackage_definitions (self)
        prefix_dir = self.settings.prefix_dir
        d['winpthread-dll'] = [
            prefix_dir + '/bin/libwinpthread-*.dll',
        ]
        return d
    def install (self):
        self.system ('''
mkdir -p %(install_prefix)s/include
mkdir -p %(install_prefix)s/lib
mkdir -p %(install_prefix)s/bin
cd %(srcdir)s/mingw32/i686-w64-mingw32/include/ && tar -C %(srcdir)s/mingw32/i686-w64-mingw32/include/ -cf - . | tar -C %(install_prefix)s/include/ -xf -
cd %(srcdir)s/mingw32/i686-w64-mingw32/lib/ && tar -C %(srcdir)s/mingw32/i686-w64-mingw32/lib/ -cf - . | tar -C %(install_prefix)s/lib/ -xf -
cp %(srcdir)s/mingw32/bin/libwinpthread-*.dll %(install_prefix)s/bin/
rm -f %(install_prefix)s/lib/libgcc_s.a # for cross/gcc conflict
rm -f %(install_prefix)s/lib/libquadmath-0.dll # for cross/gcc conflict
rm -f %(install_prefix)s/lib/libssp-0.dll # for cross/gcc conflict
rm -f %(install_prefix)s/lib/libgcc_s_sjlj-1.dll # for cross/gcc conflict
rm -f %(install_prefix)s/include/zlib.h # for zlib conflict
rm -f %(install_prefix)s/include/zconf.h # for zlib conflict
rm -f %(install_prefix)s/lib/libz.a # for zlib conflict
rm -f %(install_prefix)s/include/localcharset.h # for libiconv conflict
rm -f %(install_prefix)s/include/libcharset.h # for libiconv conflict
rm -f %(install_prefix)s/include/error.h # for regex failure
rm -f %(install_prefix)s/include/iconv.h # for fontconfig failure
rm -f %(install_prefix)s/lib/libiconv.a # for ghostscript failure
rm -fr %(srcdir)s/mingw32/
ln -s usr/ %(install_root)s/mingw
''', locals ())
