# Ros2
Package ROS 2 Humble de mo phong robot omni 3 banh robot24 trong Gazebo va RViz.

Co san:

robot model URDF
Gazebo simulation
RViz config
teleop ban phim cho base
arm CLI
encoder monitor
SLAM + hien thi /map trong RViz
1. Chuan bi may moi
Can co:

Ubuntu 22.04
ROS 2 Humble
Cai cac goi can thiet:

sudo apt update
sudo apt install -y \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-gazebo-plugins \
  ros-humble-robot-state-publisher \
  ros-humble-rviz2 \
  ros-humble-joint-state-publisher-gui \
  ros-humble-tf2-ros \
  ros-humble-slam-toolbox \
  ros-humble-turtlebot3-gazebo \
  python3-colcon-common-extensions \
  python3-rosdep
Neu chua khoi tao rosdep:

sudo rosdep init
rosdep update
2. Tao workspace va copy package
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
Neu ban co source code local:

cp -r /duong_dan_toi/robot24 ./robot24
Neu ban clone tu git:

git clone <repo_url> robot24
3. Build workspace
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select robot24
source ~/ros2_ws/install/setup.bash
4. Chay robot
Mo terminal 1:

cd ~/ros2_ws
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch robot24 bringup.launch.py
Launch nay se:

mo Gazebo
spawn robot vao world mac dinh
mo RViz
chay base controller
chay encoder monitor
chay slam_toolbox de hien thi /map
Mac dinh:

neu may co turtlebot3_gazebo thi world se la turtlebot3_world.world
neu khong co thi fallback sang worlds/robot24.world
5. Teleop robot
Mo terminal 2:

cd ~/ros2_ws
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 run robot24 robot24_teleop.py --ros-args -p use_sim_time:=true
Phim dieu khien:

w: tang toc tien
x: lui
q: di ngang trai
e: di ngang phai
a: quay trai
d: quay phai
s hoac space: dung
h: in lai huong dan
6. Dieu khien tay may
Mo terminal 3:

cd ~/ros2_ws
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 run robot24 robot24_arm_cli.py --ros-args -p use_sim_time:=true
7. Kiem tra encoder
Mo terminal khac:

cd ~/ros2_ws
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 topic echo /encoder/status
Co the kiem tra them:

ros2 topic echo /encoder/alive
ros2 topic echo /encoder/joint_states
8. Kiem tra SLAM va lidar
Trong RViz:

Map doc tu /map
LaserScan doc tu /scan
Kiem tra topic:

ros2 topic list | grep -E "/map|/scan"
Neu robot dang chay, map se duoc tao dan trong RViz.

9. Lenh nhanh
Chi mo Gazebo:

cd ~/ros2_ws
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch robot24 gazebo.launch.py
Chi mo RViz:

cd ~/ros2_ws
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch robot24 display.launch.py
10. Neu co loi
Neu ros2 launch robot24 ... khong tim thay package:

cd ~/ros2_ws
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
Neu launch xong ma khong thay map:

kiem tra slam_toolbox da cai chua
cho robot di chuyen bang teleop de lidar quet moi truong
Neu RViz van dung config cu:

cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select robot24
source ~/ros2_ws/install/setup.bash
