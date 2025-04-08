from setuptools import setup, find_packages

setup(
    name="iodp",
    version="0.1",
    description="A library for manipulating raw data of instrumentation operated by the International Ocean Discovery Program.",
    author = "V.Percuoco",
    author_email="vpercuoco@tamu.edu",
    url="https://github.com/IODP/SOD-LABORATORY/iodp",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "matplotlib",
        "numpy",
        "colour-science",
        "configparser"],
    classifiers=[
        ""
    ],
    python_requires=">3.12"
)