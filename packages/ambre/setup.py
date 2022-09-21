"""Install script for the ambre package."""

from setuptools import setup, find_packages
from ambre.versions import AMBRE_PACKAGE_VERSION

setup(
    name="ambre",
    version=AMBRE_PACKAGE_VERSION,
    description="An Association Mining-Based Rules Extraction engine. Find the needle in the haystack.",
    url="https://github.com/timoklimmer/ambre",
    author="Timo Klimmer",
    author_email="",
    license="MIT",
    packages=find_packages(include=["ambre"]),
    install_requires=["tqdm", "pandas", "openpyxl", "numpy", "recordclass", "joblib", "lz4"],
    zip_safe=False,
)
