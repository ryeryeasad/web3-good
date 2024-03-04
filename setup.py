from __future__ import print_function  # 这个import必须放在第一行
import distutils.spawn
import sys

from setuptools import setup, find_packages

# 读取你的README.md文件以便能够在pypi中显示
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    packages=find_packages(),

    package_data={
        '': ['*.txt'],
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'web3 = demo.main:main'
        ]
    },
    long_description=long_description,
    long_description_content_type='text/markdown'
)

