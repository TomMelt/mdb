from setuptools import setup, find_packages

setup(
    name='mdb',
    version='0.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'Pexpect',
    ],
    entry_points={
        'console_scripts': [
            'mdb = mdb.mdb:main',
        ],
    },
)
