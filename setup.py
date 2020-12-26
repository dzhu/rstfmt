import os

from setuptools import setup

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "README.rst")) as f:
    long_description = f.read()

setup(
    name="docstrfmt",
    version="0.0.1",
    author="Joel Payne",
    author_email="lilspazjoekp@gmail.com",
    url="https://github.com/LilSpazJoekp/docstrfmt",
    description="A formatter for reStructuredText doc strings",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    license="MIT",
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
    packages=["docstrfmt"],
    python_requires=">=3.6",
    install_requires=[
        "black>=19.10b0",
        "sphinx>=2.4.0",
        "tabulate",
        "docutils",
        "click",
    ],
    extras_require={
        "d": ["aiohttp>=3.3.2"],
        "test": ["pytest", "pytest-aiohttp"],
        "lint": ["black", "flake8", "flynt"],
    },
    entry_points={
        "console_scripts": [
            "docstrfmt = docstrfmt.main:main",
            "docstrfmtd = docstrfmt.server:main [d]",
        ]
    },
)
