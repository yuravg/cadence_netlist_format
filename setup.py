"""Setup file"""

from setuptools import setup, find_packages
import cadence_netlist_format

setup(
    name='cadence_netlist_format',
    version=cadence_netlist_format.__version__,
    description='Format Cadence Net-list',
    url='',
    author='Yuriy VG',
    author_email='yuravg@gmail.com',
    license='MIT',
    install_requires=[],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    entry_points={
        'console_scripts': [
            'cnl_format = cadence_netlist_format.main:main'
        ]
    },
    long_description=open('README.md').read(),
    include_package_data=True,
    packages=find_packages(exclude=['tests']),
    test_suite='tests'
)
