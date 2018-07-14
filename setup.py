import setuptools

with open("README.md", 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='machineio',
    version='0.0.1',
    author='Michael Elliott',
    author_email='robotzapa@gmail.com',
    description='Machine IO using functors to abstract hardware io',
    long_description=long_description,
    url='https://github.com/RobotZapa/machineio',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Licence :: OSI Approved :: MIT Licence',
        'Operating System :: OS Independent',
        'Development Status :: Alpha',
        'Framework :: Robot Framework',
    ],
)

