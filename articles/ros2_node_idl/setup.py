TDB

import glob
import os

from setuptools import setup

package_name = "foo_py"

setup(
    name=package_name,
    data_files=[
        ('share/' + package_name, ['package.xml']),
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name + '/xml_cache', glob.glob('xml_cache/**')),
    ],
    ...
)
