# -*- coding: utf-8 -*-

# DO NOT EDIT THIS FILE!
# This file has been autogenerated by dephell <3
# https://github.com/dephell/dephell

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import os.path

readme = ''
here = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(here, 'README.rst')
if os.path.exists(readme_path):
    with open(readme_path, 'rb') as stream:
        readme = stream.read().decode('utf8')

setup(
    long_description=readme,
    name='vcfstats',
    version='0.1.0',
    description='Powerful statistics for VCF files',
    python_requires='==3.*,>=3.6.0',
    project_urls={
        "homepage": "https://github.com/pwwang/vcfstats",
        "repository": "https://github.com/pwwang/vcfstats"
    },
    author='pwwang',
    author_email='pwwang@pwwang.com',
    license='MIT',
    entry_points={"console_scripts": ["vcfstats = vcfstats.cli:main"]},
    packages=['vcfstats'],
    package_dir={"": "."},
    package_data={"vcfstats": ["*.bak", "*.toml"]},
    install_requires=[
        'cmdy', 'cyvcf2==0.*', 'lark-parser==0.*,>=0.9.0', 'pyparam',
        'rich==6.*', 'toml==0.*'
    ],
    extras_require={"dev": ["pytest", "pytest-cov"]},
)
