import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setup_requires = ["munch>=2.5.0", "pydash>=4.8.0"]
excluded = ["tests/", "maps/"]

setuptools.setup(
    name="pystyx",
    version="0.3.2",
    scripts=[],
    author="Mark Keaton",
    author_email="mkeaton@gmail.com",
    description="Python Styx bindings for ETL/ELT declarative mapping syntax using TOML.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/styx-dev/pystyx",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
