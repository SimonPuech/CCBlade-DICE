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
    print(f"this_dir: {this_dir}")
    print(f"staging_dir: {staging_dir}")
    print(f"build_dir: {build_dir}")
    print(f"build_path: {build_path}")
    print(f"cwd: {os.getcwd()}")
    
    # First, ensure ccblade package directory exists
    os.makedirs("ccblade", exist_ok=True)
    
    for root, _dirs, files in os.walk(build_path):
        print("="*40 +f"Processing {root}")
        for f in files:
            print("="*30 +f"looping through {f}")
            if f.endswith((".so", ".lib", ".pyd", ".pdb", ".dylib", ".dll")):
                print("="*30 +f"Processing {f}")
                file_path = os.path.join(root, f)
                
                # Copy to package directory
                package_path = os.path.join("ccblade", f)
                print(f"Copying to package: {file_path} -> {package_path}")
                shutil.copy(file_path, package_path)
                
                # Copy to build/lib directory
                build_lib_dir = os.path.join("build", f"lib.{platform.system().lower()}-{platform.machine()}-{platform.python_version()}", "ccblade")
                os.makedirs(build_lib_dir, exist_ok=True)
                build_lib_path = os.path.join(build_lib_dir, f)
                print(f"Copying to build: {file_path} -> {build_lib_path}")
                shutil.copy(file_path, build_lib_path)

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
            configure_call = ["meson", "setup", staging_dir, "--wipe",
                          f"-Dpython.purelibdir={purelibdir}", f"--prefix={build_dir}", 
                          f"-Dpython.platlibdir={purelibdir}"] + meson_args.split()
            configure_call = [m for m in configure_call if m.strip() != ""]
            print(configure_call)

            build_call = ["meson", "compile", "-vC", staging_dir]
            print(build_call)

            self.build_temp = build_dir

            self.spawn(configure_call)
            self.spawn(build_call)
            copy_shared_libraries()

            
if __name__ == "__main__":
    setuptools.setup(
        cmdclass={"bdist_wheel": bdist_wheel, "build_ext": MesonBuildExt},
        distclass=BinaryDistribution,
        ext_modules=[MesonExtension("ccblade", this_dir)],
        package_data={
            'ccblade': ['_bem.*'],  # Include the extension module
        },
        include_package_data=True,
    )
