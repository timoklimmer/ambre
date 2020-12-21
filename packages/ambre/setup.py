"""Install script for the ambre package."""

from setuptools import setup, find_packages

setup(
    name="ambre",
    version="0.1",
    description="A module to find out why things are how they are.",
    url="",
    author="",
    author_email="",
    license="MIT",
    packages=find_packages(include=["ambre"]),
    install_requires=["tqdm", "pandas"],
    zip_safe=False,
)