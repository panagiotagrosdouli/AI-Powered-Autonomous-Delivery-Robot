"""Custom robot AMCL + Nav2. Condition A directly uses smoothed Nav2 commands.
B/C/D put the experimental supervisor after the smoother; no parallel bypass.
"""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument,OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def setup(context):
    mode=LaunchConfiguration('condition').perform(context)
    if mode not in 'ABCD' or len(mode)!=1:raise ValueError('condition must be A/B/C/D')
    checkpoint=LaunchConfiguration('checkpoint').perform(context)
    if mode=='D' and not checkpoint:raise ValueError('D requires a verified trained checkpoint')
    mapfile=LaunchConfiguration('map').perform(context)
    if not os.path.isfile(mapfile):raise ValueError('A saved generated map is required')
    config=os.path.join(get_package_share_directory('delivery_robot'),'config','navigation.yaml')
    nodes=[]
    for package,executable,name in [
      ('nav2_map_server','map_server','map_server'),('nav2_amcl','amcl','amcl'),
      ('nav2_controller','controller_server','controller_server'),('nav2_planner','planner_server','planner_server'),
      ('nav2_bt_navigator','bt_navigator','bt_navigator'),('nav2_behaviors','behavior_server','behavior_server'),
      ('nav2_waypoint_follower','waypoint_follower','waypoint_follower')]:
        nodes.append(Node(package=package,executable=executable,name=name,output='screen',
          parameters=[config,{'use_sim_time':True,'yaml_filename':mapfile}],remappings=[('cmd_vel','/cmd_vel_raw')]))
    nodes.append(Node(package='nav2_velocity_smoother',executable='velocity_smoother',name='velocity_smoother',
      parameters=[config],remappings=[('cmd_vel','/cmd_vel_raw'),('cmd_vel_smoothed','/cmd_vel' if mode=='A' else '/cmd_vel_nav')]))
    nodes.append(Node(package='nav2_lifecycle_manager',executable='lifecycle_manager',name='lifecycle_manager',
      parameters=[{'use_sim_time':True,'autostart':True,'node_names':['map_server','amcl','controller_server',
        'planner_server','behavior_server','bt_navigator','waypoint_follower','velocity_smoother']}]))
    if mode!='A':
        nodes.append(Node(package='delivery_robot',executable='supervisor',parameters=[{'use_sim_time':True,'condition':mode}]))
    if mode in ('C','D'):
        nodes.append(Node(package='delivery_robot',executable='predictor',parameters=[{'use_sim_time':True,'checkpoint':checkpoint}]))
    return nodes

def generate_launch_description():
    return LaunchDescription([DeclareLaunchArgument('map'),DeclareLaunchArgument('condition',default_value='A'),
      DeclareLaunchArgument('checkpoint',default_value=''),OpaqueFunction(function=setup)])
