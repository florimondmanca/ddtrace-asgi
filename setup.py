import re
import typing
from pathlib import Path

from setuptools import setup


def get_version(package: str) -> str:
    version = Path(package, "__version__.py").read_text()
    match = re.search("__version__ = ['\"]([^'\"]+)['\"]", version)
    assert match is not None
    return match.group(1)


def get_long_description() -> str:
    with open("README.md", encoding="utf8") as readme:
        with open("CHANGELOG.md", encoding="utf8") as changelog:
            return readme.read() + "\n\n" + changelog.read()


def get_packages(package: str) -> typing.List[str]:
    return [str(path.parent) for path in Path(package).glob("**/__init__.py")]


setup(
    name="ddtrace-asgi",
    version=get_version("ddtrace_asgi"),
    description="Unofficial ddtrace integration for ASGI apps and frameworks",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="http://github.com/florimondmanca/ddtrace-asgi",
    author="Florimond Manca",
    author_email="florimond.manca@gmail.com",
    packages=get_packages("ddtrace_asgi"),
    include_package_data=True,
    package_data={"ddtrace_asgi": ["py.typed"]},
    zip_safe=False,
    install_requires=["ddtrace", "starlette==0.*"],
    python_requires=">=3.6",
    license="BSD",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
