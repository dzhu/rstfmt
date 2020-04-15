import os

from setuptools import setup

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "README.rst")) as f:
    long_description = f.read()

setup(
    name="rstfmt",
    version="0.0.1",
    author="Danny Zhu",
    url="https://github.com/dzhu/rstfmt",
    description="A formatter for reStructuredText",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    license="MIT",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Documentation",
        "Topic :: Documentation :: Sphinx",
        "Topic :: Software Development :: Documentation",
    ],
    packages=["rstfmt"],
    python_requires=">=3.6",
    install_requires=["sphinx>=2.4.0",],
    extras_require={"d": ["aiohttp>=3.3.2"]},
    entry_points={
        "console_scripts": ["rstfmt = rstfmt.main:main", "rstfmtd = rstfmt.server:main [d]"]
    },
)
