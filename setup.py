from setuptools import setup, find_packages

setup(
    name="twd",
    version="1.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "twd=twd.twd:main",
        ]
    },
    install_requires=[],
    author="m4sc0",
    description="A tool to temporarily save and go to a working directory"
)