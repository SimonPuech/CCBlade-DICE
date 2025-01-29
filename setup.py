#!/usr/bin/env python
import os
import shutil
import platform
import setuptools
from setuptools.command.build_ext import build_ext
import glob

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

print(f"DEBUG: Current directory: {os.getcwd()}")
print(f"DEBUG: this_dir: {this_dir}")
print(f"DEBUG: staging_dir: {staging_dir}")
print(f"DEBUG: build_dir: {build_dir}")

def copy_shared_libraries(purelibdir):
    build_path = os.path.join(staging_dir, "ccblade")
    
    for root, _dirs, files in os.walk(build_path):
        for f in files:
            if f.endswith((".so", ".lib", ".pyd", ".pdb", ".dylib", ".dll")):
                print(f"DEBUG:[1] file : {f}")
                file_path = os.path.join(root, f)
                new_path = str(file_path).replace(staging_dir + os.sep, "")
                print(f"DEBUG:[1] current work dir: {os.getcwd()}")
                print(f"Copying build file {file_path} -> {new_path}")
                shutil.copy(file_path, new_path)
                
                # For venv
                os.makedirs(os.path.join(this_dir, purelibdir), exist_ok=True)
                os.makedirs(os.path.join(this_dir, purelibdir,"ccblade"), exist_ok=True)
                new_path = os.path.join(this_dir, purelibdir, "ccblade", os.path.basename(f))
                print(f"Copying build file {file_path} -> {new_path}")
                shutil.copy(os.path.join(root, f), new_path)


class MesonExtension(setuptools.Extension):
    def __init__(self, name, sourcedir="", **kwa):
        setuptools.Extension.__init__(self, name, sources=[], **kwa)
        self.sourcedir = os.path.abspath(sourcedir)

class MesonBuildExt(build_ext):
    def build_extension(self, ext):
        
        if not isinstance(ext, MesonExtension):
            super().build_extension(ext)
            return

        try:
            self.spawn(["meson", "--version"])
        except OSError:
            raise RuntimeError("Cannot find meson executable")
        
        meson_args = os.environ.get("MESON_ARGS", "")

        if platform.system() == "Windows":
            if "FC" not in os.environ:
                os.environ["FC"] = "gfortran"
            if "CC" not in os.environ:
                os.environ["CC"] = "gcc"

        purelibdir = os.path.dirname(self.get_ext_fullpath(ext.name))

        configure_call = [
            "meson", "setup", staging_dir, "--wipe",
            f"-Dpython.purelibdir={purelibdir}",
            f"--prefix={build_dir}",
            f"-Dpython.platlibdir={purelibdir}"
        ] + meson_args.split()
        configure_call = [m for m in configure_call if m.strip() != ""]

        build_call = ["meson", "compile", "-vC", staging_dir]

        self.build_temp = build_dir
        
        self.spawn(configure_call)
        self.spawn(build_call)
        copy_shared_libraries(purelibdir)

if __name__ == "__main__":
    setuptools.setup(
        cmdclass={"bdist_wheel": bdist_wheel, "build_ext": MesonBuildExt},
        distclass=BinaryDistribution,
        ext_modules=[MesonExtension("ccblade", this_dir) ],
    )