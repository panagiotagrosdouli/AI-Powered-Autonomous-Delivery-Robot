from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('demo_people', default_value='false'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        Node(package='delivery_robot', executable='predictor', output='screen', parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}]),
        Node(package='delivery_robot', executable='supervisor', output='screen', parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}]),
        Node(package='delivery_robot', executable='demo_people', output='screen', parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
             condition=IfCondition(LaunchConfiguration('demo_people'))),
    ])
