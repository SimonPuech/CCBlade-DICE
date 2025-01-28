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

def copy_shared_libraries():
    build_path = os.path.join(staging_dir, "ccblade")
    install_path = os.path.join(this_dir, "build", "lib*", "ccblade")
    
    print(f"DEBUG: copy_shared_libraries - build_path: {build_path}")
    print(f"DEBUG: copy_shared_libraries - install_path: {install_path}")
    print(f"DEBUG: copy_shared_libraries - current dir: {os.getcwd()}")
    
    # Find all extension files
    ext_files = glob.glob(os.path.join(build_path, "_bem.*"))
    print(f"DEBUG: Found extension files: {ext_files}")
    
    for ext_path in ext_files:
        if os.path.isfile(ext_path):
            # Get the extension file name
            ext_name = os.path.basename(ext_path)
            print(f"DEBUG: Processing extension: {ext_name}")
            
            # Create target directory if it doesn't exist
            os.makedirs("ccblade", exist_ok=True)
            # Copy the extension
            target_path = os.path.join("ccblade", ext_name)
            print(f"DEBUG: Target path: {target_path}")
            print(f"DEBUG: Target path absolute: {os.path.abspath(target_path)}")
            print(f"Copying extension {ext_path} -> {target_path}")
            shutil.copy2(ext_path, target_path)
            print(f"DEBUG: File exists after copy: {os.path.exists(target_path)}")

class MesonExtension(setuptools.Extension):
    def __init__(self, name, sourcedir="", **kwa):
        setuptools.Extension.__init__(self, name, sources=[], **kwa)
        self.sourcedir = os.path.abspath(sourcedir)
        print(f"DEBUG: MesonExtension sourcedir: {self.sourcedir}")

class MesonBuildExt(build_ext):
    def build_extension(self, ext):
        print(f"DEBUG: Building extension: {ext.name}")
        print(f"DEBUG: Current directory: {os.getcwd()}")
        
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

        purelibdir = self.get_ext_fullpath(ext.name)
        purelibdir = os.path.dirname(purelibdir)
        print(f"DEBUG: purelibdir: {purelibdir}")

        configure_call = [
            "meson", "setup", staging_dir, "--wipe",
            f"-Dpython.purelibdir={purelibdir}",
            f"--prefix={build_dir}",
            f"-Dpython.platlibdir={purelibdir}"
        ] + meson_args.split()
        configure_call = [m for m in configure_call if m.strip() != ""]
        print(f"DEBUG: configure_call: {configure_call}")

        build_call = ["meson", "compile", "-vC", staging_dir]
        install_call = ["meson", "install", "-C", staging_dir]

        self.build_temp = build_dir
        print(f"DEBUG: build_temp: {self.build_temp}")
        
        self.spawn(configure_call)
        self.spawn(build_call)
        self.spawn(install_call)
        copy_shared_libraries()

if __name__ == "__main__":
    print("DEBUG: Starting setup")
    setuptools.setup(
        cmdclass={"bdist_wheel": bdist_wheel, "build_ext": MesonBuildExt},
        distclass=BinaryDistribution,
        ext_modules=[MesonExtension("ccblade", this_dir)],
        package_data={'ccblade': ['*.so', '*.pyd', '*.dll']},
        include_package_data=True,
        packages=['ccblade'],
        install_requires=[
            'numpy>=1.19.0',
            'scipy>=1.6.0',
            'openmdao>=3.2.0'
        ],
    )
    print("DEBUG: Setup completed")
