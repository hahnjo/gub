import glob
import re
import os
import context
import download
import framework
import cross

class Odcctools (cross.Cross_package):
	def install_prefix (self):
		return self.settings.tooldir
	
	def configure (self):
		cross.Cross_package.configure (self)

		## remove LD64 support.
		self.file_sub ([('ld64','')],
			       self.builddir () + '/Makefile')

class Gcc (cross.Gcc):
	def patch (self):
		self.file_sub ([('/usr/bin/libtool', '%(crossprefix)s/bin/%(target_architecture)s-libtool')],
			       '%(srcdir)s/gcc/config/darwin.h')


class Rewirer (context.Os_context_wrapper):
	def __init__ (self, settings):
		context.Os_context_wrapper.__init__ (self,settings)
		self.ignore_libs = None

	def get_libaries (self, name):
		lib_str = self.read_pipe ("%(tooldir)s/bin/%(target_architecture)s-otool -L %(name)s", locals(), ignore_error=True)

		libs = []
		for l in lib_str.split ('\n'):
			m = re.search (r"\s+(.*) \(.*\)" % o, l)
			if not m:
				continue
			if self.ignore_libs.has_key (m.group (1)):
				continue

			libs.append (m.group (1))

		return libs

	def rewire_mach_o_object (self, name, substitutions):
		for (o,d) in substitutions:
			changes += (' -change %s %s ' % (o, d))		

		if changes:
			
			self.system ("%(tooldir)s/bin/%(target_architecture)s-install_name_tool %(changes)s %(name)s ",
				     locals())

	def rewire_mach_o_object_executable_path (self, name):
		orig_libs = [self.expand ('%(tooldir)s/lib'),
			     self.expand ('%(tooldir)s/%(target_architecture)s/lib'),
			     '/usr/lib']

		libs = self.get_libaries()
		subs = []
		for l in libs:
			for o in orig_libs:
				if not re.search (o, l):
					continue
				newpath = re.sub (orig, '@executable_path/../lib/', l); 
				subs.append ((l, newpath))

		self.rewire_mach_o_object (name, subs)

	def rewire_binary_dir (self, dir):
		if not os.path.isdir (dir):
			return
		(root, dirs, files) = os.walk (dir).next ()
		files = [os.path.join (root, f) for f in files]
		
		for f in files:
			if os.path.isfile (f):
				self.rewire_mach_o_object(f)
		
	def get_ignore_libs (self):
		str = self.read_pipe ('tar tfz %(gub_uploads)s/darwin-sdk-0.0-1.darwin.gub')
		d = {}
		for l in str.split ('\n'):
			l = l.strip ()
			if re.match (r'^\./usr/lib/', l):
				d[l[1:]] = True
		return d

	def rewire_root (self, root):
		if self.ignore_libs == None:
			self.ignore_libs = self.get_ignore_libs ()
		
		self.rewire_binary_dir (root + '/usr/lib')
		# Ugh.
		self.rewire_binary_dir (root + '/usr/lib/pango/1.4.0/modules/')
		self.rewire_binary_dir (root + '/usr/bin')

class Package_rewirer:
	def __init__ (self, rewirer, package):
		self.rewirer = rewirer
		self.package = package
		
	def rewire (self):
		self.rewirer.rewire_root (self.package.install_root ())
		

def add_rewire_path (settings, packages):
	rewirer = Rewirer (settings)
	for p in packages:
		if p.name () == 'darwin-sdk':
			continue
		
		wr = Package_rewirer (rewirer, p)
		p.postinstall = wr.rewire

		
def get_packages (settings):
	packages = [
		Odcctools (settings).with (version='20051122', mirror=download.opendarwin, format='bz2'),		
		cross.Pkg_config (settings).with (version="0.20",
						      mirror=download.freedesktop),
		Gcc (settings).with (mirror = download.gcc,
##				     version='3.4.5',
				     version='4.0.2', 
				     format='bz2',
				     depends=['odcctools']),
		]

	return packages

def change_target_packages (packages):
	cross.change_target_packages (packages)
	
def get_darwin_sdk ():
	host  = 'maagd'
	version = '0.1'

	l = locals()

	dest =	'darwin-sdk-%(version)s' % l
	os.system ('rm -rf %s' % dest)
	os.mkdir (dest)
	dirs = ["/usr/lib","/usr/include","/System/Library/Frameworks/Python.framework",
		"/System/Library/Frameworks/CoreServices.framework"]
	for d in dirs:
		os.makedirs (dest + d)
		cmd =  ('rsync -a -v %s:%s/ %s%s' %
			(host, d, dest, d))
		print cmd
		s = os.system (cmd)
		if s :
			raise 'bar'

	os.system ('chmod -R +w %s '  % dest)
	os.system ('tar cfz %s.tar.gz %s '  % (dest, dest))
	

if __name__== '__main__':
	get_darwin_sdk ()

