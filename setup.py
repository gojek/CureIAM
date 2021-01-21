"""Setup script."""

import setuptools

import IAMRecommending

_description = IAMRecommending.__doc__.splitlines()[0]
_long_description = open('README.md').read()
_version = IAMRecommending.__version__
_requires = open('pkg-requirements.txt').read().splitlines()

setuptools.setup(

    name='IAMRecommending',
    version=_version,
    author='IAMRecommending Authors and Contributors',
    description=_description,
    long_description=_long_description,
    url='https://github.com/IAMRecommending/IAMRecommending',

    install_requires=_requires,

    packages=setuptools.find_packages(exclude=['IAMRecommending.test']),

    entry_points={
        'console_scripts': {
            'IAMRecommending = IAMRecommending.manager:main'
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
