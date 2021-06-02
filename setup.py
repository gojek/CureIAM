"""Setup script."""

import setuptools

import CureIAM

_description = CureIAM.__doc__.splitlines()[0]
_long_description = open('README.md').read()
_version = CureIAM.__version__
_requires = open('pkg-requirements.txt').read().splitlines()

setuptools.setup(

    name='CureIAM',
    version=_version,
    author='CureIAM Authors and Contributors',
    description=_description,
    long_description=_long_description,
    url='https://github.com/CureIAM/CureIAM',

    install_requires=_requires,

    packages=setuptools.find_packages(exclude=['CureIAM.test']),

    entry_points={
        'console_scripts': {
            'CureIAM = CureIAM.manager:main'
        }
    },

    # Reference for classifiers: https://pypi.org/classifiers/
    classifiers=[
        'Development Status :: 1 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: DevOps',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: System :: Monitoring',
    ],

    keywords='GCP IAM monitoring framework',
)
