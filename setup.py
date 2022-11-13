# coding=utf-8
"""Python ACDSee Helper setup script."""
from setuptools import setup


def readme():
    with open('README.md') as desc:
        return desc.read()


setup(

    name='acdsee_helper',
    version='0.1a1',
    packages=['acdsee_helper'],

    python_requires='>=3.8',
    install_requires=[
        'argparse',
        'colorama',
        'exiv2',
        'pyexiv2',
        'pyyaml',
        'watchdog',
        'xmltodict',
    ],

    author='Steve Herrell',
    author_email='steve.herrell@gmail.com',
    description='acdsee_helper is a scipt that massages exif information between ACDSee and DXO Photolab.',
    long_description=readme(),
    long_description_content_type='text/markdown',
    license='LGPLv3+',
    keywords=[
        'acdsee',
        'dxo photolab',
        'exif',
        'keywords',
        'lightroom',
        'python',
    ],
    url='https://github.com/twrecked/acdsee-helper',
    project_urls={
        "Bug Tracker": 'https://github.com/twrecked/acdsee-helper/issues',
        "Documentation": 'https://github.com/twrecked/acdsee-helper/blob/main/README.md',
        "Source Code": 'https://github.com/twrecked/acdsee-helper',

    },
    classifiers=[
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    scripts={
        'scripts': [
            'bin/acdsee-helper',
        ],
    },
    test_suite='tests',
)
