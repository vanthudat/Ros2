from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import PackageNotFoundError, get_package_share_directory

import os


def generate_launch_description():
    package_share = get_package_share_directory("robot24")
    gazebo_ros_share = get_package_share_directory("gazebo_ros")
    gzserver_launch = os.path.join(gazebo_ros_share, "launch", "gzserver.launch.py")
    gzclient_launch = os.path.join(gazebo_ros_share, "launch", "gzclient.launch.py")
    try:
        turtlebot3_share = get_package_share_directory("turtlebot3_gazebo")
        default_world = os.path.join(
            turtlebot3_share,
            "worlds",
            "turtlebot3_world.world",
        )
        default_x_pose = "-2.0"
        default_y_pose = "-0.5"
    except PackageNotFoundError:
        default_world = os.path.join(package_share, "worlds", "robot24.world")
        default_x_pose = "0.0"
        default_y_pose = "0.0"

    world = LaunchConfiguration("world")
    use_sim_time = LaunchConfiguration("use_sim_time")
    x_pose = LaunchConfiguration("x_pose")
    y_pose = LaunchConfiguration("y_pose")
    z_pose = LaunchConfiguration("z_pose")
    urdf_path = os.path.join(package_share, "urdf", "robot24.urdf")
    rviz_config = os.path.join(package_share, "config", "robot24.rviz")
    controller_config = os.path.join(package_share, "config", "controller.yaml")
    slam_params = os.path.join(
        get_package_share_directory("slam_toolbox"),
        "config",
        "mapper_params_online_async.yaml",
    )

    with open(urdf_path, "r", encoding="utf-8") as urdf_file:
        gazebo_robot_description = urdf_file.read()
    robot_description = gazebo_robot_description.replace(
        "package://robot24/",
        f"file://{package_share}/",
    )
    # spawn_entity.py rejects a Unicode string that still carries an encoding declaration.
    robot_description = robot_description.replace(
        '<?xml version="1.0" encoding="utf-8"?>',
        "",
        1,
    )

    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            gzserver_launch
        ),
        launch_arguments={
            "world": world,
            "verbose": "false",
            "extra_gazebo_args": "-s libgazebo_ros_state.so -s libgazebo_ros_properties.so",
        }.items(),
    )

    gzclient = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gzclient_launch),
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "robot_description": robot_description,
                "use_sim_time": use_sim_time,
            }
        ],
    )

    spawn_robot = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=[
            "-entity",
            "robot24",
            "-topic",
            "robot_description",
            "-x",
            x_pose,
            "-y",
            y_pose,
            "-z",
            z_pose,
        ],
        output="screen",
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", rviz_config],
        parameters=[
            {
                "use_sim_time": use_sim_time,
                "robot_description": robot_description,
            }
        ],
        output="screen",
    )

    arm_hold = Node(
        package="robot24",
        executable="robot24_arm_hold.py",
        name="robot24_arm_hold",
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )

    base_controller = Node(
        package="robot24",
        executable="robot24_base_controller.py",
        name="robot24_base_controller",
        parameters=[controller_config, {"use_sim_time": use_sim_time}],
        output="screen",
    )

    encoder_monitor = Node(
        package="robot24",
        executable="robot24_encoder_monitor.py",
        name="robot24_encoder_monitor",
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )

    base_footprint_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="base_link_to_base_footprint",
        arguments=["0", "0", "0", "0", "0", "0", "base_link", "base_footprint"],
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )

    slam_toolbox = Node(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="slam_toolbox",
        parameters=[slam_params, {"use_sim_time": use_sim_time}],
        output="screen",
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "world",
                default_value=default_world,
            ),
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("x_pose", default_value=default_x_pose),
            DeclareLaunchArgument("y_pose", default_value=default_y_pose),
            DeclareLaunchArgument("z_pose", default_value="0.1"),
            gzserver,
            gzclient,
            robot_state_publisher,
            spawn_robot,
            arm_hold,
            base_controller,
            encoder_monitor,
            base_footprint_tf,
            slam_toolbox,
            rviz,
        ]
    )
