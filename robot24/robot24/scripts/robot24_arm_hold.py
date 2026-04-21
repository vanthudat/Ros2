#!/usr/bin/env python3

import rclpy
from builtin_interfaces.msg import Duration
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


class Robot24ArmHold(Node):
    def __init__(self):
        super().__init__("robot24_arm_hold")
        self.joint_pub = self.create_publisher(JointState, "joint_states", 10)
        self.arm_traj_pub = self.create_publisher(
            JointTrajectory, "arm_joint_trajectory", 10
        )
        self.arm_traj_fallback_pub = self.create_publisher(
            JointTrajectory, "set_joint_trajectory", 10
        )
        self.arm_traj_ns_pub = self.create_publisher(
            JointTrajectory, "/robot24_arm/arm_joint_trajectory", 10
        )
        self.arm_traj_ns_default_pub = self.create_publisher(
            JointTrajectory, "/robot24_arm/set_joint_trajectory", 10
        )
        self.arm_traj_sub = self.create_subscription(
            JointTrajectory, "arm_joint_trajectory", self.arm_traj_cb, 10
        )

        self.declare_parameter("publish_rate", 10.0)
        self.declare_parameter("trucquay_default", 1.1344640137963142)
        self.declare_parameter("khautruot_default", 0.05)

        self.publish_rate = float(self.get_parameter("publish_rate").value)
        self.target_positions = {
            "trucquay_joint": float(self.get_parameter("trucquay_default").value),
            "khautruot_joint": float(self.get_parameter("khautruot_default").value),
        }

        self.timer = self.create_timer(1.0 / self.publish_rate, self.publish_hold_pose)
        self.get_logger().info("Arm state keeper active.")

    def arm_traj_cb(self, msg):
        if not msg.points:
            return
        latest_point = msg.points[-1]
        if len(latest_point.positions) != len(msg.joint_names):
            return
        for joint_name, position in zip(msg.joint_names, latest_point.positions):
            if joint_name in self.target_positions:
                self.target_positions[joint_name] = float(position)

    def publish_hold_pose(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = ["trucquay_joint", "khautruot_joint"]
        msg.position = [
            self.target_positions["trucquay_joint"],
            self.target_positions["khautruot_joint"],
        ]
        self.joint_pub.publish(msg)

        traj = JointTrajectory()
        traj.header.stamp = msg.header.stamp
        traj.header.frame_id = "world"
        traj.joint_names = list(msg.name)
        point = JointTrajectoryPoint()
        point.positions = list(msg.position)
        point.time_from_start = Duration(sec=0, nanosec=200000000)
        traj.points = [point]
        self.arm_traj_pub.publish(traj)
        self.arm_traj_fallback_pub.publish(traj)
        self.arm_traj_ns_pub.publish(traj)
        self.arm_traj_ns_default_pub.publish(traj)


def main():
    rclpy.init()
    node = Robot24ArmHold()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
