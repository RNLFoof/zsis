from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
   name='zsis',
   python_requires='>=3.10',
   version='1.0',
   description='Beware',
   license="MIT",
   long_description=long_description,
   author='Zoe Zablotsky',
   url="https://github.com/RNLFoof/zsis",
   packages=['zsis'],
   install_requires=[]
)