from setuptools import setup, find_packages

setup(
    name="twd_m4sc0",
    version="2.0.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "twd=twd.twd:main",
        ]
    },
    install_requires=[],
    author="m4sc0",
    description="A tool to temporarily save and go to a working directory",
    url="https://github.com/m4sc0/twd",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)
