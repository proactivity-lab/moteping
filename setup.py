"""
moteping: moteping application.

Python application for pinging smart-dust motes.
"""

from setuptools import setup, find_packages
from os.path import join as pjoin

import moteping

doclines = __doc__.split("\n")

setup(name='moteping',
      version=moteping.version,
      description='Python application for pinging smart-dust motes',
      long_description='\n'.join(doclines[2:]),
      url='http://github.com/proactivity-lab/python-moteping',
      author='Raido Pahtma',
      author_email='raido.pahtma@ttu.ee',
      license='MIT',
      platforms=["any"],
      packages=find_packages(),
      install_requires=['moteconnection', 'argconfparse', 'serdepa'],
      scripts=[pjoin('bin', 'moteping')],
      zip_safe=False)
