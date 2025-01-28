# NumPy include directory - needed in all submodules
incdir_numpy = get_option('incdir_numpy')
if incdir_numpy == ''
    incdir_numpy = run_command(py3,
      [
        '-c',
        'import os; os.chdir(".."); import numpy; print(numpy.get_include())'
      ],
      check: true
    ).stdout().strip()
endif
# this creates a raw string which is useful for Windows use of '\' for paths
incdir_numpy = '''@0@'''.format(incdir_numpy)

#incdir_f2py = run_command(py3,
#    ['-c', 'import os; os.chdir(".."); import numpy.f2py; print(numpy.f2py.get_include())'],
#    check : true
#).stdout().strip()

incdir_f2py = incdir_numpy / '..' / '..' / 'f2py' / 'src'
inc_f2py = include_directories(incdir_f2py)
fortranobject_c = incdir_f2py / 'fortranobject.c'

inc_np = include_directories(incdir_numpy, incdir_f2py)


#subdir('src')
bem_source = custom_target('bemmodule.c',
                            input : ['src/bem.f90'],
                            output : ['_bemmodule.c'],
                            command: [py3, '-m', 'numpy.f2py',
			    '@INPUT@', '-m', '_bem', '--lower', '--build-dir', '@OUTDIR@']
                            )

# Build the extension module
bem_ext = py3.extension_module('_bem',
                ['src/bem.f90', bem_source, fortranobject_c],
                include_directories: inc_np,
                dependencies : py3_dep,
                link_language: 'fortran',
                install : true,
                install_dir: py3.get_install_dir())

# Create ccblade directory if it doesn't exist
run_command('mkdir', '-p', 'ccblade', check: false)

# Install script to ensure the module is in the right place
meson.add_install_script('python3', '-c', '''
import os
import shutil
import glob

build_dir = os.path.join("@MESON_BUILD_ROOT@", "ccblade")
install_dir = os.path.join("@MESON_INSTALL_PREFIX@", "ccblade")

os.makedirs(install_dir, exist_ok=True)

# Find and copy the extension module
for ext_file in glob.glob(os.path.join(build_dir, "_bem.*")):
    if os.path.isfile(ext_file):
        dst = os.path.join(install_dir, os.path.basename(ext_file))
        print(f"Installing {ext_file} -> {dst}")
        shutil.copy2(ext_file, dst)
''')
