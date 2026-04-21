#!/usr/bin/env python3

import math
import time

import rclpy
from builtin_interfaces.msg import Duration
from geometry_msgs.msg import Twist, TwistStamped
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


class Robot24BaseController(Node):
    def __init__(self):
        super().__init__("robot24_base_controller")

        self.declare_parameter("publish_rate", 30.0)
        self.declare_parameter("wheel_radius", 0.06)
        self.declare_parameter("robot_radius", 0.305)
        self.declare_parameter("gamma_deg", -1.0773502691896257)
        self.declare_parameter("cmd_vel_timeout", 0.5)
        self.declare_parameter(
            "wheel_names",
            ["dongco1_joint", "dongco2_joint", "dongco3_joint"],
        )
        self.declare_parameter("use_stamped_vel", False)

        self.publish_rate = float(self.get_parameter("publish_rate").value)
        self.wheel_radius = float(self.get_parameter("wheel_radius").value)
        self.robot_radius = float(self.get_parameter("robot_radius").value)
        self.gamma = math.radians(float(self.get_parameter("gamma_deg").value))
        self.cmd_vel_timeout = float(self.get_parameter("cmd_vel_timeout").value)
        self.wheel_names = list(self.get_parameter("wheel_names").value)
        self.use_stamped_vel = bool(self.get_parameter("use_stamped_vel").value)

        if len(self.wheel_names) != 3:
            raise ValueError("wheel_names must contain exactly 3 wheel joints.")
        if self.publish_rate <= 0.0:
            raise ValueError("publish_rate must be > 0.")
        if self.wheel_radius <= 0.0:
            raise ValueError("wheel_radius must be > 0.")
        if self.robot_radius <= 0.0:
            raise ValueError("robot_radius must be > 0.")

        self.joint_state_pub = self.create_publisher(JointState, "joint_states", 10)
        self.encoder_pub = self.create_publisher(JointState, "/encoder/joint_states", 10)
        self.wheel_traj_pub = self.create_publisher(
            JointTrajectory,
            "/robot24_base/wheel_joint_trajectory",
            10,
        )

        self.last_cmd = Twist()
        self.last_cmd_time = time.monotonic()
        self.last_update_time = time.monotonic()
        self.wheel_positions = {name: 0.0 for name in self.wheel_names}
        self.wheel_angles = self.compute_wheel_angles()

        if self.use_stamped_vel:
            self.cmd_sub = self.create_subscription(
                TwistStamped, "cmd_vel", self.cmd_stamped_cb, 10
            )
        else:
            self.cmd_sub = self.create_subscription(Twist, "cmd_vel", self.cmd_cb, 10)

        self.timer = self.create_timer(1.0 / self.publish_rate, self.update)
        self.get_logger().info(
            "Base controller ready. Wheel motion follows omni 3-wheel kinematics."
        )

    def compute_wheel_angles(self):
        base_angles = [0.0, -2.0 * math.pi / 3.0, 2.0 * math.pi / 3.0]
        return {
            joint_name: base_angle + self.gamma
            for joint_name, base_angle in zip(self.wheel_names, base_angles)
        }

    def cmd_cb(self, msg):
        self.last_cmd = msg
        self.last_cmd_time = time.monotonic()

    def cmd_stamped_cb(self, msg):
        self.last_cmd = msg.twist
        self.last_cmd_time = time.monotonic()

    def get_active_cmd(self):
        if time.monotonic() - self.last_cmd_time > self.cmd_vel_timeout:
            return 0.0, 0.0, 0.0

        return (
            float(self.last_cmd.linear.x),
            float(self.last_cmd.linear.y),
            float(self.last_cmd.angular.z),
        )

    def compute_wheel_rates(self, vx, vy, wz):
        wheel_rates = {}
        for joint_name, beta in self.wheel_angles.items():
            tangent_x = math.sin(beta)
            tangent_y = -math.cos(beta)

            center_x = self.robot_radius * math.cos(beta)
            center_y = self.robot_radius * math.sin(beta)

            contact_vx = vx - wz * center_y
            contact_vy = vy + wz * center_x

            wheel_rates[joint_name] = (
                contact_vx * tangent_x + contact_vy * tangent_y
            ) / self.wheel_radius

        return wheel_rates

    def publish_encoder_state(self, wheel_rates):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = list(self.wheel_names)
        msg.position = [self.wheel_positions[name] for name in self.wheel_names]
        msg.velocity = [wheel_rates[name] for name in self.wheel_names]
        self.joint_state_pub.publish(msg)
        self.encoder_pub.publish(msg)

        traj = JointTrajectory()
        traj.header.stamp = msg.header.stamp
        traj.header.frame_id = "world"
        traj.joint_names = list(self.wheel_names)

        point = JointTrajectoryPoint()
        point.positions = [self.wheel_positions[name] for name in self.wheel_names]
        point.velocities = [wheel_rates[name] for name in self.wheel_names]
        point.time_from_start = Duration(sec=0, nanosec=20000000)
        traj.points = [point]
        self.wheel_traj_pub.publish(traj)

    def update(self):
        now = time.monotonic()
        dt = max(0.0, min(now - self.last_update_time, 0.2))
        self.last_update_time = now
        if dt <= 0.0:
            return

        vx, vy, wz = self.get_active_cmd()
        wheel_rates = self.compute_wheel_rates(vx, vy, wz)

        for name, rate in wheel_rates.items():
            self.wheel_positions[name] += rate * dt

        self.publish_encoder_state(wheel_rates)


def main():
    rclpy.init()
    node = None
    try:
        node = Robot24BaseController()
        rclpy.spin(node)
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
