from gub import gubb
from gub import misc

from context import subst_method 
class CrossToolSpec (gubb.BuildSpec):
    """Package for cross compilers/linkers etc.
    """

    def configure_command (self):
        return (gubb.BuildSpec.configure_command (self)
            + misc.join_lines ('''
--program-prefix=%(target_architecture)s-
--prefix=%(cross_prefix)s
--with-slibdir=/usr/lib
--target=%(target_architecture)s
--with-sysroot=%(system_root)s
--disable-multilib
'''))

    def compile_command (self):
        return self.native_compile_command ()
        
    def install_command (self):
        return '''make DESTDIR=%(install_root)s prefix=/usr/cross install'''

#    def gub_src_uploads (self):
#        return '%(gub_cross_uploads)s'

    def get_subpackage_names (self):
        return ['doc', '']
    
    def license_file (self):
        return ''

def change_target_package (package):
    pass

def set_cross_dependencies (package_object_dict):
    packs = package_object_dict.values ()
    cross_packs = [p for p in packs if isinstance (p, CrossToolSpec)]
    sdk_packs = [p for p in packs if isinstance (p, gubb.SdkBuildSpec)]
    other_packs = [p for p in packs if (not isinstance (p, CrossToolSpec)
                                        and not isinstance (p, gubb.SdkBuildSpec)
                                        and not isinstance (p, gubb.BinarySpec))]
    
    sdk_names = [s.name() for s in sdk_packs]
    cross_names = [s.name() for s in cross_packs]
    for p in other_packs:
        old_callback = p.get_build_dependencies
        p.get_build_dependencies = misc.MethodOverrider (old_callback,
                                                         lambda x,y: x+y, (cross_names,))

    for p in other_packs + cross_packs:
        old_callback = p.get_build_dependencies
        p.get_build_dependencies = misc.MethodOverrider (old_callback,
                                                         lambda x,y: x+y, (sdk_names,))

    return packs

cross_module_checksums = {}
cross_module_cache = {}
def get_cross_module (settings):
    platform = settings.platform
    if cross_module_cache.has_key (platform):
        return cross_module_cache[platform]

    import re
    base = re.sub ('[-0-9].*', '', platform)
    for name in platform, base:
        file_name = 'gub/%(name)s.py' % locals ()
        import os
        if os.path.exists (file_name):
            break
    settings.os_interface.info ('module-name: ' + file_name + '\n')
    import misc
    module = misc.load_module (file_name, base)

    import md5
    cross_module_checksums[platform] = md5.md5 (open (file_name).read ()).hexdigest ()
    cross_module_cache[platform] = module
    return module

def get_cross_packages (settings):
    mod = get_cross_module (settings)
    return mod.get_cross_packages (settings)

def get_build_dependencies (settings):
    mod = get_cross_module (settings)
    return mod.get_cross_build_dependencies (settings)

def get_cross_checksum (platform):
    try:
        return cross_module_checksums[platform]
    except KeyError:
        print 'No cross module found'
        return '0000'