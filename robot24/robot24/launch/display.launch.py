from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():
    package_share = get_package_share_directory("robot24")
    urdf_path = os.path.join(package_share, "urdf", "robot24.urdf")
    rviz_config = os.path.join(package_share, "config", "robot24.rviz")
    default_joint_positions = {
        "zeros.trucquay_joint": 1.1344640137963142,
        "zeros.khautruot_joint": 0.05,
    }

    with open(urdf_path, "r", encoding="utf-8") as urdf_file:
        robot_description = urdf_file.read()
    robot_description = robot_description.replace(
        "package://robot24/",
        f"file://{package_share}/",
    )

    return LaunchDescription(
        [
            Node(
                package="joint_state_publisher_gui",
                executable="joint_state_publisher_gui",
                name="joint_state_publisher_gui",
                parameters=[default_joint_positions],
            ),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                parameters=[{"robot_description": robot_description}],
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz2",
                arguments=["-d", rviz_config],
                parameters=[{"robot_description": robot_description}],
            ),
        ]
    )
