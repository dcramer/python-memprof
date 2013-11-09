#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='memprof',
    version='0.1.0',
    author='David Cramer',
    author_email='dcramer@gmail.com',
    url='http://github.com/tenxer/python-memprof',
    description='',
    packages=find_packages(exclude=["tests"]),
    zip_safe=False,
    install_requires=[
        'psutil',
    ],
    license='Apache License 2.0',
    entry_points={
        'console_scripts': [
            'memprof = memprof.runner:main',
        ],
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
