from setuptools import setup, find_packages

#https://www.youtube.com/watch?v=kNke39OZ2k0
setup(
    name='autoup',
    version='0.1',
    py_modules=['core'],
    packages=find_packages(),
    entry_points='''
        [console_scripts]
        autoup=core.cli:cli
    '''


)

#print find_packages()