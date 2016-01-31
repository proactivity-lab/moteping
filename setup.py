from setuptools import setup

setup(name='moteping',
      version='0.1.0',
      description='Python application for pinging smart-dust motes',
      url='http://github.com/proactivity-lab/python-moteping',
      author='Raido Pahtma',
      author_email='raido.pahtma@ttu.ee',
      license='MIT',
      install_requires=[
        "moteconnection",
        "argconfparse",
        "serdepa",
      ],
      packages=['moteping'],
      zip_safe=False)
