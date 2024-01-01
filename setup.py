from setuptools import find_packages, setup

setup(
    name="mdb",
    version="0.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Click",
        "Pexpect",
        "Matplotlib",
        "Numpy",
    ],
    extras_require={
        "develop": [
            "Mypy",
        ]
    },
    entry_points={
        "console_scripts": [
            "mdb = mdb.mdb:main",
        ],
    },
)
