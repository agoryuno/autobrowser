from setuptools import setup, find_packages
import codecs
import os

HERE = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
    with codecs.open(os.path.join(HERE, *parts), 'r') as fp:
        return fp.read()

long_description = read('README.md')

setup(
    name='gpt_tools',
    version='0.1.0',
    description='Tools for working with GPT models',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Alex Goryunov',
    author_email='alex.goryunov@gmail.com',
    url='http://github.com/agoryuno/autobrowser',  # Replace with your own GitHub project link
    license='MIT',
    packages=['gpt_tools'],
    package_dir={'gpt_tools': 'autobrowser/gpt_tools'},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    install_requires=[
        # Add your project's dependencies here
        # 'numpy>=1.20.0,<2',
        # 'pandas>=1.2.0,<2',
    ],
    python_requires='>=3.7',
)
