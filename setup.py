import os
import sys

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand


class Test(TestCommand):
    def run_tests(self):
        import pytest

        errno = pytest.main(["tests"])
        sys.exit(errno)


def get_version(version_tuple):
    """Return the version tuple as a string, e.g. for (0, 10, 7),
    return '0.10.7'.
    """
    return ".".join(map(str, version_tuple))


init = os.path.join(
    os.path.dirname(__file__), "sticky_marshmallow", "__init__.py"
)
version_line = list(filter(lambda l: l.startswith("VERSION"), open(init)))[0]

VERSION = get_version(eval(version_line.split("=")[-1]))


setup(
    name="sticky_marshmallow",
    version=VERSION,
    author="Bas Wind",
    author_email="mailtobwind@gmail.com",
    url="http://github.com/bwind/sticky-marshmallow",
    license="MIT",
    include_package_data=True,
    description="sticky-marshmallow provides RDMS style persistence for marshmallow schemas",  # noqa: E501
    platforms=["any"],
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=["marshmallow"],
    cmdclass={"test": Test},
)
