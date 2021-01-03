import re
from codecs import open
from os import path

from setuptools import setup

PACKAGE_NAME = "docstrfmt"
HERE = path.abspath(path.dirname(__file__))
with open(path.join(HERE, "README.rst"), encoding="utf-8") as fp:
    README = fp.read()
with open(path.join(HERE, PACKAGE_NAME, "const.py"), encoding="utf-8") as fp:
    VERSION = re.search('__version__ = "([^"]+)"', fp.read()).group(1)

extras_requires = {
    "d": ["aiohttp>=3.3.2"],
    "test": ["pytest", "pytest-aiohttp"],
    "lint": ["black", "flake8", "flynt", "isort"],
}
extras_requires["dev"] = extras_requires["test"] + extras_requires["lint"]

setup(
    name=PACKAGE_NAME,
    author="Joel Payne",
    author_email="lilspazjoekp@gmail.com",
    python_requires="~=3.6",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python",
        "Topic :: Documentation",
        "Topic :: Documentation :: Sphinx",
        "Topic :: Software Development :: Documentation",
        "Topic :: Utilities",
    ],
    description="A formatter for Sphinx flavored reStructuredText.",
    entry_points={
        "console_scripts": [
            "docstrfmt = docstrfmt.main:main",
            "docstrfmtd = docstrfmt.server:main [d]",
        ]
    },
    extras_require=extras_requires,
    install_requires=[
        "black>=19.10b0",
        "click",
        "docutils",
        "libcst",
        "sphinx>=2.4.0",
        "tabulate",
    ],
    license="MIT",
    long_description=README,
    packages=["docstrfmt"],
    url="https://github.com/LilSpazJoekp/docstrfmt",
    version=VERSION,
)
