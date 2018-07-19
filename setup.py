import setuptools

with open("README.md", 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='machineio',
    version='0.0.2',
    author='Michael Elliott',
    author_email='robotzapa@gmail.com',
    description='Machine IO using functors to abstract hardware io',
    long_description=long_description,
    url='https://github.com/RobotZapa/machineio',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha',
        'Framework :: Robot Framework',
    ],
)

