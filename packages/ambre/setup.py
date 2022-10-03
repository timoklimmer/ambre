"""
Install script for the package.

Note: We need to load the versions.py script separately here because we cannot import it without loading the entire
      package. When this script is run, the package is however not available yet. Hence need to import the versions
      module separately.
"""

from importlib import util

from setuptools import find_packages, setup


def load_file_as_module(name, location):
    """Load Python script as module."""
    spec = util.spec_from_file_location(name, location)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


versions = load_file_as_module("versions", "ambre/versions.py")

setup(
    name="ambre",
    version=versions.AMBRE_PACKAGE_VERSION,
    description="An Association Mining-Based Rules Extraction engine. Find the needle in the haystack.",
    url="https://github.com/timoklimmer/ambre",
    author="Timo Klimmer",
    author_email="",
    license="MIT",
    packages=find_packages(include=["ambre"]),
    install_requires=["tqdm", "pandas", "openpyxl", "numpy", "recordclass", "joblib", "lz4"],
    zip_safe=False,
)
