from setuptools import setup

with open('README.md', 'r') as readme:
    long_description = readme.read()

setup(
    name='gLinDA',
    version='0.3.0',
    description='A gossip learning implementation of LinDA',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/gLinDA/',
    author='Leon Fehse',
    author_email='leon.fehse@hhu.de',
    license='BSD 3-clause',
    packages=['gLinDA'],
    install_requires=[
	"psutil>=5.9.0"
	"pycryptodome>=3.20.0"
    ],
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
