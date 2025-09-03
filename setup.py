from setuptools import setup, find_packages

setup(
    name='gisl-data-library',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        requests>=2.25.1
    ],
    author='Imran Bin Gifary (System Delta or Imran Delta Online)',
    author_email='imran.sdelta@gmail.com',
    description='A simple Python library for retrieving Genshin Impact character and material data from a JSON file. This is a work in progress.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Imran-Delta/GI-Static-Data-Library',
)
