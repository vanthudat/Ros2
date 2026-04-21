cmake_minimum_required(VERSION 3.8)

project(robot24)

find_package(ament_cmake REQUIRED)

install(PROGRAMS
  scripts/robot24_arm_hold.py
  scripts/robot24_arm_cli.py
  scripts/robot24_base_controller.py
  scripts/robot24_encoder_monitor.py
  scripts/robot24_teleop.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  config
  launch
  meshes
  urdf
  worlds
  DESTINATION share/${PROJECT_NAME}
)

install(FILES README.md
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
