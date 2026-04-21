#!/usr/bin/env python3

import select
import sys
import termios
import tty

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node

HELP_TEXT = """\
robot24 teleop
w/x : tang/giam toc tien lui
q/e : di ngang trai/phai
a/d : quay trai/phai
s or space : dung
h : in lai huong dan
Ctrl+C : thoat
"""


class Robot24Teleop(Node):
    def __init__(self):
        super().__init__("robot24_teleop")

        self.declare_parameter("linear_step", 0.05)
        self.declare_parameter("angular_step", 0.3)
        self.declare_parameter("max_linear_speed", 0.6)
        self.declare_parameter("max_angular_speed", 1.5)
        self.declare_parameter("publish_rate", 10.0)

        self.linear_step = float(self.get_parameter("linear_step").value)
        self.angular_step = float(self.get_parameter("angular_step").value)
        self.max_linear_speed = float(self.get_parameter("max_linear_speed").value)
        self.max_angular_speed = float(self.get_parameter("max_angular_speed").value)
        self.publish_rate = float(self.get_parameter("publish_rate").value)

        self.cmd_pub = self.create_publisher(Twist, "cmd_vel", 10)
        self.current_cmd = Twist()
        self.timer = self.create_timer(1.0 / self.publish_rate, self.publish_cmd)

        self.get_logger().info("Teleop ready. Focus this terminal and use w/x/q/e/a/d.")
        print(HELP_TEXT)

    def clamp(self, value, limit):
        return max(min(value, limit), -limit)

    def adjust_linear_x(self, delta):
        self.current_cmd.linear.x = self.clamp(
            self.current_cmd.linear.x + delta,
            self.max_linear_speed,
        )

    def adjust_linear_y(self, delta):
        self.current_cmd.linear.y = self.clamp(
            self.current_cmd.linear.y + delta,
            self.max_linear_speed,
        )

    def adjust_angular_z(self, delta):
        self.current_cmd.angular.z = self.clamp(
            self.current_cmd.angular.z + delta,
            self.max_angular_speed,
        )

    def stop(self):
        self.current_cmd = Twist()

    def handle_key(self, key):
        if key == "w":
            self.adjust_linear_x(self.linear_step)
        elif key == "x":
            self.adjust_linear_x(-self.linear_step)
        elif key == "q":
            self.adjust_linear_y(self.linear_step)
        elif key == "e":
            self.adjust_linear_y(-self.linear_step)
        elif key == "a":
            self.adjust_angular_z(self.angular_step)
        elif key == "d":
            self.adjust_angular_z(-self.angular_step)
        elif key in {"s", " "}:
            self.stop()
        elif key == "h":
            print(HELP_TEXT)
        else:
            return False

        self.publish_cmd()
        self.get_logger().info(
            "cmd_vel x=%.2f y=%.2f wz=%.2f"
            % (
                self.current_cmd.linear.x,
                self.current_cmd.linear.y,
                self.current_cmd.angular.z,
            )
        )
        return True

    def publish_cmd(self):
        self.cmd_pub.publish(self.current_cmd)


def get_key(timeout=0.1):
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if ready:
        return sys.stdin.read(1)
    return ""


def main():
    if not sys.stdin.isatty():
        raise RuntimeError("stdin is not a TTY. Run this node in a real terminal.")

    settings = termios.tcgetattr(sys.stdin)
    rclpy.init()
    node = Robot24Teleop()

    try:
        tty.setraw(sys.stdin.fileno())
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.0)
            key = get_key(0.1)
            if key == "\x03":
                break
            if key:
                node.handle_key(key)
    finally:
        node.stop()
        node.publish_cmd()
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
