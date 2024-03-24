from setuptools import find_packages, setup

setup(
    name="mdb",
    version="0.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "matplotlib",
        "numpy",
        "pexpect",
        "rich",
        "typing_extensions",
    ],
    extras_require={
        "termgraph": [
            "termgraph",
        ],
        "develop": [
            "black",
            "flake8",
            "mypy",
            "types-setuptools",
            "pytest",
            "pytest-cov",
        ],
        "docs": [
            "sphinx",
            "sphinx_click",
            "sphinx_rtd_theme",
        ],
    },
    entry_points={
        "console_scripts": [
            "mdb = mdb.mdb:run_main",
        ],
    },
)
