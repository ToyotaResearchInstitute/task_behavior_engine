## ! DO NOT MANUALLY INVOKE THIS setup.py, USE CATKIN INSTEAD

from __future__ import absolute_import
from distutils.core import setup
from catkin_pkg.python_setup import generate_distutils_setup

# fetch values from package.xml
setup_args = generate_distutils_setup(
    packages=['task_behavior_engine',],
    package_dir={'': 'src'},
    classifiers=[
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3'
    ],
    install_requires=[
        'six'
    ],
)

setup(**setup_args)
