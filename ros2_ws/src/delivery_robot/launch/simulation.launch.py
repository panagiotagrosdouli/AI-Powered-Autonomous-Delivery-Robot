from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument,IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command,LaunchConfiguration,PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    share=get_package_share_directory('delivery_robot')
    world=PathJoinSubstitution([share,'worlds',LaunchConfiguration('world')])
    description=ParameterValue(Command(['xacro ',os.path.join(share,'description','delivery.urdf.xacro')]),value_type=str)
    return LaunchDescription([
      DeclareLaunchArgument('world',default_value='indoor.sdf'),
      IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(
        get_package_share_directory('ros_gz_sim'),'launch','gz_sim.launch.py')),
        launch_arguments={'gz_args':['-r -s --headless-rendering ',world]}.items()),
      Node(package='robot_state_publisher',executable='robot_state_publisher',parameters=[{'use_sim_time':True,'robot_description':description}]),
      Node(package='ros_gz_sim',executable='create',arguments=['-name','delivery','-topic','robot_description','-z','0.18']),
      Node(package='ros_gz_bridge',executable='parameter_bridge',parameters=[{'config_file':os.path.join(share,'config','bridge.yaml'),'use_sim_time':True}]),
    ])
