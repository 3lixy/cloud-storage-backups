# setuptools in python2 does not like unicode_literals
import io
import sys

from setuptools import setup, find_packages

with io.open('README.rst', encoding='utf-8') as readme:
    long_description = readme.read()

# Populates __version__ without importing the package
__version__ = None
version_file_path = 'cloud_storage_backups/_version.py'
with io.open(version_file_path, encoding='utf-8')as ver_file:
    exec (ver_file.read())  # pylint: disable=W0122
if not __version__:
    print(f'Could not find __version__ from {version_file_path}')
    sys.exit(1)


def load_requirements(filename):
    with io.open(filename, encoding='utf-8') as reqfile:
        return [line.strip() for line in reqfile if not line.startswith('#')]

# https://stackoverflow.com/questions/7522250/how-to-include-package-data-with-setuptools-distribute
setup(
    name='cloud_storage_backups',
    version=__version__,
    description='Python app to push backups to the cloud',
    long_description=long_description,
    author='3lixy',
    license='MIT',
    url='',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=load_requirements('requirements.txt'),
    entry_points={
        'console_scripts': ['csb = cloud_storage_backups:main'],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6"
    ]
)