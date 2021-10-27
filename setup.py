from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='pybfbc2stats',
    version='0.1.2',
    description='Simple Python library for retrieving statistics of Battlefield: Bad Company 2 players',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/cetteup/pybfbc2stats',
    project_urls={
        'Bug Tracker': 'https://github.com/cetteup/pybfbc2stats/issues',
    },
    author='cetteup',
    author_email='me@cetteup.com',
    license='MIT',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3'
    ],
    packages=['pybfbc2stats'],
    python_requires='>=3.6'
)
