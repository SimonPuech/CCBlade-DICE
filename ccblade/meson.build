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
                subdir: 'ccblade',
                link_language: 'fortran',
                install : true)

# Get Python extension suffix using a custom target
suffix = custom_target('get_suffix',
                      output: 'suffix',
                      command: [
                          py3,
                          '-c',
                          'import sysconfig; print(sysconfig.get_config_var("EXT_SUFFIX"), end="")'
                      ],
                      capture: true)

# Install the extension module
meson.add_install_script('python3', '-c', '''
import os
import shutil
import sysconfig

ext_suffix = sysconfig.get_config_var("EXT_SUFFIX")
src = os.path.join("@0@", "ccblade", "_bem" + ext_suffix)
dst = os.path.join("@CURRENT_SOURCE_DIR@", "ccblade")
os.makedirs(dst, exist_ok=True)
if os.path.exists(src):
    shutil.copy2(src, dst)
'''.format(meson.current_build_dir()))
