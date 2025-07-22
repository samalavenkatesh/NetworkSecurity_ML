'''
The setup.py file is an essential part of packaging and
distributing Python Projects. It is used by setup tools to 
define the configuration of your project. such as metadata, 
dependices, and more.
'''

from setuptools import find_packages,setup
from typing import List
# find_packages  : function which scans all the folders and check
# for __init__.py considered as package


def get_requirements()->List[str]:
    '''
    This function will return list of requirements
    '''

    requirement_lst:List[str]=[]

    try: 
        with open('requirements.txt','r') as file:
            # Read lines from the file
            lines= file.readlines()
            # Process each line
            for line in lines:
                requirement = line.strip()
                ## Ignore empty lines and -e.
                if requirement and requirement != '-e .':
                    requirement_lst.append(requirement)
    except FileNotFoundError:
        print('requirements.txt file not found')

    return requirement_lst

# print(get_requirements())


setup(
    name="NetworkSecurity",
    version="0.0.1",
    author="Venkatesh",
    author_email="venkatesh.samala58@gmail.com",
    packages=find_packages(),
    install_requires = get_requirements()
)