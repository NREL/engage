#!/usr/bin/env python
"""The setup script."""
from version import __version__

from setuptools import setup, find_packages


requirements = ['Click>=7.0',]

test_requirements = []

setup(
    author="NREL",
    author_email='engage@nrel.gov',
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    description="A package for running engage models with CLI commands",
    entry_points={
        'console_scripts': [
            'engage=commands.cli:main',
        ],
    },
    install_requires=requirements,
    include_package_data=True,
    keywords='engage',
    name='nrel-engage',
    packages=find_packages(include=['.', '.*']),
    tests_require=test_requirements,
    url='https://github.com/NREL/engage',
    version=__version__,
    zip_safe=False,
)
