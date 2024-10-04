#!/usr/bin/env python

import toml


with open('pyproject.toml', 'r') as file:
    pyproject_data = toml.load(file)

version = pyproject_data['tool']['poetry']['version']
print(version)
