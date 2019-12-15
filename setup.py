#!/usr/bin/env python3

from marathon.version import title, description, url, author, author_email, license, version
from setuptools import setup, find_packages


def install_deps():
    with open('requirements.txt', 'r') as f:
        packages = f.readlines()
        new_pkgs = []
        links = []
        for resource in packages:
            if 'git+https' in resource:
                pkg = resource.split('#')[-1]
                links.append(resource.strip() + '-9876543210')
                new_pkgs.append(pkg.replace('egg=', '').rstrip())
            else:
                new_pkgs.append(resource.strip())
        return new_pkgs, links


pkgs, new_links = install_deps()

setup(
    name=title,
    description=description,
    long_description=url,
    url=url,
    author=author,
    author_email=author_email,
    license=license,
    version=version,

    classifiers=[
        'Development Status :: 4 - Beta',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Topic :: System :: Distributed Computing',

        'License :: OSI Approved :: Apache Software License',

        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],

    keywords='cloud run build deploy containers kubernetes knative',
    py_modules=["marathon"],
    python_requires=">=3.6",
    packages=find_packages(),
    include_package_data=True,
    dependency_links=new_links,
    install_requires=pkgs,
    entry_points={
        'console_scripts': [
            'run=marathon.cli:main',
            'run-marathon=marathon.cli:main',
        ],
    },
)
