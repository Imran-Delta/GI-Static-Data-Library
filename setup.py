from setuptools import setup, find_packages

setup(
    name='gisl-data-library',
    version='0.0.1',
    author='Imran Bin Gifary (System Delta or Imran_Delta Online)',
    author_email='imran.sdelta@gmail.com',
    description='A simple Python library for retrieving Genshin Impact character and material data.',
    long_description='A simple Python library for retrieving Genshin Impact character and material data from a JSON file. This is a work in progress.',
    long_description_content_type='text/plain',
    url='https://github.com/Imran-Delta/GI-Static-Data-Library',
    packages=find_packages(),
    package_data={
        'gisl_data_library': ['gisl_data.json'],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
