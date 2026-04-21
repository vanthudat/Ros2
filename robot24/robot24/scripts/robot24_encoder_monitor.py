#!/usr/bin/env python3

import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Bool, String


class Robot24EncoderMonitor(Node):
    def __init__(self):
        super().__init__("robot24_encoder_monitor")

        self.declare_parameter("status_rate", 1.0)
        self.declare_parameter("stale_timeout", 1.0)
        self.declare_parameter("velocity_threshold", 0.01)

        self.status_rate = float(self.get_parameter("status_rate").value)
        self.stale_timeout = float(self.get_parameter("stale_timeout").value)
        self.velocity_threshold = float(self.get_parameter("velocity_threshold").value)

        self.last_msg = None
        self.last_msg_monotonic = None
        self.last_alive_state = None

        self.encoder_sub = self.create_subscription(
            JointState,
            "/encoder/joint_states",
            self.encoder_cb,
            10,
        )
        self.status_pub = self.create_publisher(String, "/encoder/status", 10)
        self.alive_pub = self.create_publisher(Bool, "/encoder/alive", 10)
        self.timer = self.create_timer(1.0 / self.status_rate, self.publish_status)

        self.get_logger().info(
            "Encoder monitor active. Watching /encoder/joint_states."
        )

    def encoder_cb(self, msg):
        self.last_msg = msg
        self.last_msg_monotonic = time.monotonic()

    def format_joint_pairs(self, values):
        if self.last_msg is None:
            return "[]"
        pairs = [
            f"{name}={value:.3f}"
            for name, value in zip(self.last_msg.name, values)
        ]
        return "[" + ", ".join(pairs) + "]"

    def publish_status(self):
        now = time.monotonic()
        alive = (
            self.last_msg_monotonic is not None
            and (now - self.last_msg_monotonic) <= self.stale_timeout
        )

        alive_msg = Bool()
        alive_msg.data = alive
        self.alive_pub.publish(alive_msg)

        if not alive:
            status_text = "alive=false moving=false positions=[] velocities=[]"
        else:
            velocities = list(self.last_msg.velocity)
            positions = list(self.last_msg.position)
            moving = any(abs(value) > self.velocity_threshold for value in velocities)
            status_text = (
                f"alive=true moving={str(moving).lower()} "
                f"positions={self.format_joint_pairs(positions)} "
                f"velocities={self.format_joint_pairs(velocities)}"
            )

        status_msg = String()
        status_msg.data = status_text
        self.status_pub.publish(status_msg)

        if self.last_alive_state != alive:
            self.last_alive_state = alive
            level = self.get_logger().info if alive else self.get_logger().warn
            level(f"Encoder state changed: {status_text}")
        elif alive:
            self.get_logger().info(status_text)


def main():
    rclpy.init()
    node = None
    try:
        node = Robot24EncoderMonitor()
        rclpy.spin(node)
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
