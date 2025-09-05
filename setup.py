from setuptools import setup, find_packages

setup(
    name='gisl-data-library',
    version='0.0.8',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'gisl_data_library': ['gisl_data.json'],
    },
    install_requires=[],
    author='Imran Bin Gifary (System Delta or Imran Delta Online)',
    author_email='imran.sdelta@gmail.com',
    description='A static library of Genshin item/char info. (WIP) - Albedo added.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Imran-Delta/GI-Static-Data-Library',
)
