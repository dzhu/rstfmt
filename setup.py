import os

from setuptools import setup

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "README.rst")) as f:
    long_description = f.read()

version = {}
with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "rstfmt/_version.py")) as f:
    exec(f.read(), version)

setup(
    name="rstfmt",
    version=version["__version__"],
    author="Danny Zhu",
    author_email="dzhu@dzhu.us",
    url="https://github.com/dzhu/rstfmt",
    description="A formatter for reStructuredText",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Documentation",
        "Topic :: Documentation :: Sphinx",
        "Topic :: Software Development :: Documentation",
    ],
    packages=["rstfmt"],
    python_requires=">=3.7",
    install_requires=["black>=19.10b0", "docutils<0.18", "sphinx>=2.4.0"],
    extras_require={"d": ["aiohttp>=3.3.2"]},
    entry_points={
        "console_scripts": ["rstfmt = rstfmt.__main__:main", "rstfmtd = rstfmt.server:main [d]"]
    },
)
