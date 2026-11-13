from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
      DeclareLaunchArgument('detector',default_value='hog'),
      DeclareLaunchArgument('registered_rectified_depth',default_value='false'),
      DeclareLaunchArgument('detector_manifest',default_value=''),
      DeclareLaunchArgument('use_sim_time',default_value='true'),
      Node(package='delivery_robot',executable='perception',parameters=[{
        'use_sim_time':LaunchConfiguration('use_sim_time'),'registered_rectified_depth':LaunchConfiguration('registered_rectified_depth'),
        'detector':LaunchConfiguration('detector'),'detector_manifest':LaunchConfiguration('detector_manifest')}]),
      Node(package='delivery_robot',executable='predictor',parameters=[{
        'use_sim_time':LaunchConfiguration('use_sim_time'),'input_mode':'tracked'}])])
