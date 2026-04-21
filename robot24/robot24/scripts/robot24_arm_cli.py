#!/usr/bin/env python3

import threading

import rclpy
from builtin_interfaces.msg import Duration
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


PROMPT = "arm> "


class Robot24ArmCli(Node):
    def __init__(self):
        super().__init__("robot24_arm_cli")
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
        self.arm_joint_names = ["trucquay_joint", "khautruot_joint"]

        self.default_arm_positions = {
            "trucquay_joint": 1.1344640137963142,
            "khautruot_joint": 0.05,
        }
        self.arm_limits = {
            "trucquay_joint": (-1.0, 1.57),
            "khautruot_joint": (-0.08, 0.06),
        }
        self.arm_positions = dict(self.default_arm_positions)
        self.target_arm_positions = dict(self.default_arm_positions)
        self.rotate_step = 0.03
        self.slide_step = 0.005
        self.position_tolerance = 1e-4
        self.return_delay_sec = 1.0
        self.command_active = False
        self.auto_return_pending = False
        self.auto_return_time = None
        self.running = True

        self.timer = self.create_timer(0.1, self.publish_arm_command)
        self.input_thread = threading.Thread(target=self.input_loop, daemon=True)
        self.input_thread.start()

        self.get_logger().info("Arm CLI ready.")

    def clamp(self, joint_name, value):
        lower, upper = self.arm_limits[joint_name]
        return min(max(value, lower), upper)

    def move_towards(self, current, target, step):
        if abs(target - current) <= step:
            return target
        if target > current:
            return current + step
        return current - step

    def set_target_positions(self, rotate_value, slide_value):
        self.target_arm_positions["trucquay_joint"] = self.clamp(
            "trucquay_joint", rotate_value
        )
        self.target_arm_positions["khautruot_joint"] = self.clamp(
            "khautruot_joint", slide_value
        )
        self.auto_return_pending = True
        self.auto_return_time = None
        self.get_logger().info(
            "Target: %.3f %.3f"
            % (
                self.target_arm_positions["trucquay_joint"],
                self.target_arm_positions["khautruot_joint"],
            )
        )
        self.command_active = True

    def input_loop(self):
        while rclpy.ok() and self.running:
            try:
                raw = input(PROMPT).strip()
            except EOFError:
                self.running = False
                return

            if not raw:
                continue
            if raw.lower() in {"q", "quit", "exit"}:
                self.running = False
                return
            if raw.lower() in {"h", "help"}:
                self.get_logger().info("arm> r0.8 | s0.02 | 0.8 0.02 | z | q")
                continue
            if raw.lower() in {"home", "reset", "z"}:
                self.target_arm_positions = dict(self.default_arm_positions)
                self.command_active = True
                self.auto_return_pending = False
                self.auto_return_time = None
                self.get_logger().info("Arm home")
                continue

            compact = raw.replace(" ", "")
            if compact.startswith("r"):
                try:
                    rotate_value = float(compact[1:])
                except ValueError:
                    self.get_logger().warn("Sai lenh xoay. Vi du: r0.8")
                    continue
                self.set_target_positions(
                    rotate_value,
                    self.target_arm_positions["khautruot_joint"],
                )
                continue

            if compact.startswith("s"):
                try:
                    slide_value = float(compact[1:])
                except ValueError:
                    self.get_logger().warn("Sai lenh truot. Vi du: s0.02")
                    continue
                self.set_target_positions(
                    self.target_arm_positions["trucquay_joint"],
                    slide_value,
                )
                continue

            normalized = raw.replace(",", " ").replace("/", " ")
            parts = normalized.split()
            if len(parts) != 2:
                self.get_logger().warn("Nhap: r0.8 | s0.02 | 0.8 0.02 | z | q")
                continue

            try:
                rotate_value = float(parts[0])
                slide_value = float(parts[1])
            except ValueError:
                self.get_logger().warn("Input phai la so.")
                continue

            self.set_target_positions(rotate_value, slide_value)

    def update_arm_positions(self):
        rotate_target = self.target_arm_positions["trucquay_joint"]
        rotate_current = self.arm_positions["trucquay_joint"]

        if abs(rotate_target - rotate_current) > self.position_tolerance:
            self.arm_positions["trucquay_joint"] = self.move_towards(
                rotate_current, rotate_target, self.rotate_step
            )
            return

        slide_target = self.target_arm_positions["khautruot_joint"]
        slide_current = self.arm_positions["khautruot_joint"]
        if abs(slide_target - slide_current) > self.position_tolerance:
            self.arm_positions["khautruot_joint"] = self.move_towards(
                slide_current, slide_target, self.slide_step
            )
            return

        if self.auto_return_pending:
            if self.auto_return_time is None:
                self.auto_return_time = self.get_clock().now()
                return

            elapsed = (self.get_clock().now() - self.auto_return_time).nanoseconds / 1e9
            if elapsed < self.return_delay_sec:
                return

            self.target_arm_positions = dict(self.default_arm_positions)
            self.auto_return_pending = False
            self.auto_return_time = None
            self.get_logger().info("Arm home")
            return

        self.command_active = False

    def publish_arm_command(self):
        if not self.command_active:
            return

        self.update_arm_positions()

        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = list(self.arm_joint_names)
        msg.position = [
            self.arm_positions["trucquay_joint"],
            self.arm_positions["khautruot_joint"],
        ]
        self.joint_pub.publish(msg)

        traj = JointTrajectory()
        traj.header.stamp = self.get_clock().now().to_msg()
        traj.header.frame_id = "world"
        traj.joint_names = list(self.arm_joint_names)

        point = JointTrajectoryPoint()
        point.positions = [
            self.arm_positions["trucquay_joint"],
            self.arm_positions["khautruot_joint"],
        ]
        point.time_from_start = Duration(sec=0, nanosec=200000000)
        traj.points = [point]

        self.arm_traj_pub.publish(traj)
        self.arm_traj_fallback_pub.publish(traj)
        self.arm_traj_ns_pub.publish(traj)
        self.arm_traj_ns_default_pub.publish(traj)


def main():
    rclpy.init()
    node = Robot24ArmCli()
    try:
        while rclpy.ok() and node.running:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node.running = False
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
