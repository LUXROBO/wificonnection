import setuptools
from os import path
from io import open

def get_requirements():
    here = path.dirname(__file__)
    with open(path.join(here, 'requirements.txt'),encoding='utf=8') as requirements_file:
        requirements = requirements_file.read().splitlines()
        return requirements

setuptools.setup(
    name="wificonnection",
    version='0.1.0',
    url="https://github.com/funkywoong/wificonnection",
    author="Jiwoong Yeon",
    description="Jupyter extension to enable connecting wifi in raspberry pi",
    packages=setuptools.find_packages(),
    install_requires=get_requirements(),
    package_data={'wificonnection': ['static/*']},
)
