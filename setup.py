#!/usr/bin/env python
import os
import shutil
import platform
import setuptools
from setuptools.command.build_ext import build_ext

#######
# This forces wheels to be platform specific
from setuptools.dist import Distribution
from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

class bdist_wheel(_bdist_wheel):
    def finalize_options(self):
        _bdist_wheel.finalize_options(self)
        self.root_is_pure = False

class BinaryDistribution(Distribution):
    """Distribution which always forces a binary package with platform name"""
    def has_ext_modules(foo):
        return True
#######
this_dir = os.path.abspath(os.path.dirname(__file__))
staging_dir = os.path.join(this_dir, "meson_build")
build_dir = os.path.join(this_dir, "build")

def copy_shared_libraries():
    build_path = os.path.join(staging_dir, "ccblade")
    for root, _dirs, files in os.walk(build_path):
        for f in files:
            if f.endswith((".so", ".lib", ".pyd", ".pdb", ".dylib", ".dll")):
                file_path = os.path.join(root, f)
                new_path = str(file_path).replace(staging_dir + os.sep, "")
                print(f"Copying build file {file_path} -> {new_path}")
                build_target = os.path.join(build_dir, f"lib.{platform.system().lower()}-{platform.machine()}-{platform.python_implementation().lower()}-{platform.python_version_tuple()[0]}{platform.python_version_tuple()[1]}", "ccblade", ext_name)

                shutil.copy(file_path, new_path)
                shutil.copy2(file_path, build_target)
                
                ext_name = os.path.basename(file_path)
                wheel_dir = os.path.join(build_dir, f"bdist.{platform.system().lower()}-{platform.machine()}", "wheel", "ccblade")
                if os.path.exists(os.path.dirname(wheel_dir)):
                    os.makedirs(wheel_dir, exist_ok=True)
                    wheel_target = os.path.join(wheel_dir, ext_name)
                    shutil.copy2(file_path, wheel_target)

#######
class MesonExtension(setuptools.Extension):

    def __init__(self, name, sourcedir="", **kwa):
        setuptools.Extension.__init__(self, name, sources=[], **kwa)
        self.sourcedir = os.path.abspath(sourcedir)

class MesonBuildExt(build_ext):
    
    def copy_extensions_to_source(self):
        newext = []
        for ext in self.extensions:
            if isinstance(ext, MesonExtension): continue
            newext.append( ext )
        self.extensions = newext
        super().copy_extensions_to_source()
    
    def build_extension(self, ext):
        
        if not isinstance(ext, MesonExtension):
            super().build_extension(ext)
            return

        else:

            # Ensure that Meson is present and working
            try:
                self.spawn(["meson", "--version"])
            except OSError:
                raise RuntimeError("Cannot find meson executable")
            
            # check if meson extra args are specified
            meson_args = ""
            if "MESON_ARGS" in os.environ:
                meson_args = os.environ["MESON_ARGS"]

            if platform.system() == "Windows":
                if "FC" not in os.environ:
                    os.environ["FC"] = "gfortran"
                if "CC" not in os.environ:
                    os.environ["CC"] = "gcc"

            purelibdir = "."
            purelibdir = os.path.dirname(self.get_ext_fullpath(ext.name))
            configure_call = ["meson", "setup", staging_dir, "--wipe",
                          f"-Dpython.purelibdir={purelibdir}", f"--prefix={build_dir}", 
                          f"-Dpython.platlibdir={purelibdir}"] + meson_args.split()
            configure_call = [m for m in configure_call if m.strip() != ""]
            print(configure_call)

            build_call = ["meson", "compile", "-vC", staging_dir]
            print(build_call)
            install_call = ["meson", "install", "-C", staging_dir]
            print(install_call)

            self.build_temp = build_dir

            self.spawn(configure_call)
            self.spawn(build_call)
            self.spawn(install_call)
            copy_shared_libraries()

            
if __name__ == "__main__":
    setuptools.setup(cmdclass={"bdist_wheel": bdist_wheel, "build_ext": MesonBuildExt},
                     distclass=BinaryDistribution,
                     ext_modules=[ MesonExtension("ccblade", this_dir) ],
                     )