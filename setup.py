from setuptools import setup, find_packages

setup(
    name='genshin-impact',
    version='0.1.1',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'genshin_impact': ['gisl_data.json'],
    },
    install_requires=[
      'packaging',
      ],
    author='Imran Bin Gifary (System Delta or Imran Delta Online)',
    author_email='imran.sdelta@gmail.com',
    description='A static library of Genshin item/char info. (WIP)',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Imran-Delta/GI-Static-Data-Library',
)
