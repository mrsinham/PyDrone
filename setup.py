from setuptools import setup, find_packages

setup(
    name='PyDrone',
    version='0.0.1',
    install_requires = ['pyyaml', 'tornado',  'mako'],
    packages=[],
    url='https://github.com/mrsinham/PyDrone',
    license='',
    author='Julien Lefevre',
    author_email='julien.lefevr@gmail.com',
    description='Simple monitoring system for http web servers, based on tornado'
)