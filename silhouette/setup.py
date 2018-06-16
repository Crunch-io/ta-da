# pragma: no cover
from distutils.command.build_ext import build_ext

from setuptools import setup, find_packages, Extension

ext_modules = [
    Extension(
        name='silhouette.profit',
        sources=['silhouette/profit.pyx'],
        ),
    ]


class deferring_build_ext(build_ext):
    """Defers Cython and numpy related imports until extension-building time.
    """
    def build_extension(self, ext):
        from Cython.Build import cythonize
        import Cython.Compiler.Options
        Cython.Compiler.Options.annotate = True
        import numpy
        numpy_include = numpy.get_include()
        ext.include_dirs.append(numpy_include)
        ext = cythonize([ext])[0]
        build_ext.build_extension(self, ext)


setup(
    name='silhouette',
    version='0.3.2',
    author="Robert Brewer, JJ Del Carpio, Charles G Waldman",
    author_email="dev@crunch.io",
    packages=find_packages('.'),
    package_dir={'silhouette': 'silhouette'},
    install_requires=[
    ],
    ext_modules=ext_modules,
    cmdclass={'build_ext': deferring_build_ext},
    entry_points={
    }
)
