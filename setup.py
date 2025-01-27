#!/usr/bin/env python
import os
import shutil
import platform
import setuptools
from setuptools.command.build_ext import build_ext
from setuptools.command.build_py import build_py
import sys

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
    print("\n=== Debug Information ===")
    print(f"this_dir: {this_dir}")
    print(f"staging_dir: {staging_dir}")
    print(f"build_dir: {build_dir}")
    print(f"build_path: {build_path}")
    print(f"cwd: {os.getcwd()}")
    print(f"Files in build_path: {os.listdir(build_path)}")
    print(f"Files in current dir: {os.listdir('.')}")
    print(f"Files in ccblade dir: {os.listdir('ccblade') if os.path.exists('ccblade') else 'ccblade dir not found'}")

    for root, _dirs, files in os.walk(build_path):
        print(f"\n=== Processing directory: {root} ===")
        print(f"Files in directory: {files}")
        for f in files:
            print(f"\n=== Processing file: {f} ===")
            if f.endswith((".so", ".lib", ".pyd", ".pdb", ".dylib", ".dll")):
                print(f"Found extension module: {f}")
                file_path = os.path.join(root, f)
                # Get the relative path from staging_dir
                rel_path = os.path.relpath(file_path, staging_dir)
                # Copy to package directory
                package_path = os.path.join("ccblade", os.path.basename(file_path))
                os.makedirs(os.path.dirname(package_path), exist_ok=True)
                print(f"Copying from: {file_path}")
                print(f"Copying to: {package_path}")
                print(f"File exists at source: {os.path.exists(file_path)}")
                shutil.copy(file_path, package_path)
                print(f"File exists at destination: {os.path.exists(package_path)}")
                print(f"File size at destination: {os.path.getsize(package_path)}")
                
                # Also copy to build/lib directory
                build_lib_dir = os.path.join("build", "lib")
                if not os.path.exists(build_lib_dir):
                    os.makedirs(build_lib_dir)
                build_lib_path = os.path.join(build_lib_dir, "ccblade", os.path.basename(file_path))
                os.makedirs(os.path.dirname(build_lib_path), exist_ok=True)
                print(f"Copying to build lib: {build_lib_path}")
                shutil.copy(file_path, build_lib_path)

    print("\n=== Additional Debug Information ===")
    print(f"Python executable: {sys.executable}")
    print(f"Platform: {platform.platform()}")
    print(f"Python version: {platform.python_version()}")

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
            print("\n=== Starting Meson Build ===")
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
            print("\n=== Meson Build Complete, Starting Copy ===")
            copy_shared_libraries()
            print("\n=== Copy Complete ===")
            print(f"Final contents of ccblade dir: {os.listdir('ccblade') if os.path.exists('ccblade') else 'ccblade dir not found'}")

class CustomBuildPy(build_py):
    def run(self):
        print("\n=== Starting CustomBuildPy ===")
        build_py.run(self)
        
        # Now copy the extension module
        if hasattr(self, 'build_lib'):
            print(f"\n=== Custom build step to copy extension ===")
            print(f"Build lib directory: {self.build_lib}")
            print(f"Current directory: {os.getcwd()}")
            
            # Try multiple source locations
            possible_sources = [
                os.path.join(staging_dir, "ccblade"),
                "ccblade",
                os.path.join("build", "lib", "ccblade"),
                os.path.join("build", "lib.linux-x86_64-cpython-310", "ccblade"),
            ]
            
            for source_dir in possible_sources:
                print(f"\nChecking source directory: {source_dir}")
                if os.path.exists(source_dir):
                    print(f"Directory exists. Contents: {os.listdir(source_dir)}")
                    for f in os.listdir(source_dir):
                        if f.startswith('_bem') and f.endswith(('.so', '.pyd', '.dylib')):
                            src = os.path.join(source_dir, f)
                            # Copy to multiple destinations to ensure it's included
                            destinations = [
                                os.path.join(self.build_lib, 'ccblade', f),
                                os.path.join('build', 'lib.linux-x86_64-cpython-310', 'ccblade', f),
                                os.path.join('build', 'bdist.linux-x86_64', 'wheel', 'ccblade', f),
                            ]
                            
                            for dst in destinations:
                                try:
                                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                                    print(f"Copying extension from {src} to {dst}")
                                    shutil.copy2(src, dst)
                                    if os.path.exists(dst):
                                        print(f"Success! File exists at {dst} with size {os.path.getsize(dst)}")
                                    else:
                                        print(f"Warning: Copy seemed to succeed but file not found at {dst}")
                                except Exception as e:
                                    print(f"Warning: Failed to copy to {dst}: {e}")
                else:
                    print(f"Directory does not exist: {source_dir}")

            print("\n=== Final build_lib contents ===")
            if os.path.exists(self.build_lib):
                for root, dirs, files in os.walk(self.build_lib):
                    print(f"\nDirectory: {root}")
                    print(f"Files: {files}")
            else:
                print(f"build_lib directory does not exist: {self.build_lib}")

if __name__ == "__main__":
    print("\n=== Starting setup process ===")
    setuptools.setup(
        cmdclass={
            "bdist_wheel": bdist_wheel,
            "build_ext": MesonBuildExt,
            "build_py": CustomBuildPy,
        },
        distclass=BinaryDistribution,
        ext_modules=[MesonExtension("ccblade", this_dir)],
        packages=["ccblade"],
        package_dir={"ccblade": "ccblade"},
        package_data={
            "ccblade": [
                "*_bem*.so",  # Unix/Linux
                "*_bem*.pyd",  # Windows
                "*_bem*.dylib",  # macOS
            ]
        },
        data_files=[
            ('ccblade', ['ccblade/_bem.cpython-310-x86_64-linux-gnu.so']),
        ],
        include_package_data=True,
        zip_safe=False,
    )
    print("\n=== Setup process complete ===")
