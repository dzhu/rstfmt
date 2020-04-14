from setuptools import setup

setup(
    name="rstfmt",
    version="0.0.1",
    author="Danny Zhu",
    description="rstfmt",
    long_description="An autoformatter for reStructuredText",
    packages=["rstfmt"],
    python_requires=">=3.6",
    install_requires=["sphinx>=2.4.0",],
    extras_require={"d": ["aiohttp>=3.3.2"]},
    entry_points={
        "console_scripts": ["rstfmt = rstfmt.main:main", "rstfmtd = rstfmt.server:main [d]"]
    },
)
