from setuptools import setup

with open('README.md', 'r') as readme:
    long_description = readme.read()

setup(
    name='sLinDA',
    version='0.1.0',
    description='A swarm learning implementation of LinDA',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/sLinDA/',
    author='Leon Fehse',
    author_email='leon.fehse@hhu.de',
    license='BSD 3-clause',
    packages=['sLinDA'],
    install_requires=[],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10'
    ],
)