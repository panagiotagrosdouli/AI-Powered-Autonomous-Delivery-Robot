from setuptools import setup, find_packages
from glob import glob
import os

name = 'delivery_robot'
setup(name=name, version='0.1.0', packages=find_packages(exclude=['test']),
      data_files=[
          ('share/ament_index/resource_index/packages', ['resource/' + name]),
          ('share/' + name, ['package.xml']),
          (os.path.join('share', name, 'launch'), glob('launch/*.launch.py')),
      ],
      install_requires=['setuptools'], zip_safe=True,
      maintainer='Project Maintainer', maintainer_email='maintainer@example.com',
      description='Predictive pedestrian-aware navigation prototype', license='MIT',
      entry_points={'console_scripts': [
          'predictor = delivery_robot.nodes:predictor_main',
          'supervisor = delivery_robot.nodes:supervisor_main',
          'demo_people = delivery_robot.nodes:demo_main',
      ]})
