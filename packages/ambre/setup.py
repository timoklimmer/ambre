"""Install script for the ambre package."""

from setuptools import setup, find_packages

setup(
    name="ambre",
    version="0.1",
    description="An Association Mining-Based Rules Extraction engine. Find out why things are how they are.",
    url="https://github.com/timoklimmer/ambre",
    author="Timo Klimmer",
    author_email="",
    license="MIT",
    packages=find_packages(include=["ambre"]),
    install_requires=["tqdm", "pandas"],
    zip_safe=False,
)
