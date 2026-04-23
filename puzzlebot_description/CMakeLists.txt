cmake_minimum_required(VERSION 3.8)
project(puzzlebot_description)

find_package(ament_cmake REQUIRED)

# Install all directories so they are findable via get_package_share_directory
install(DIRECTORY
  launch
  meshes
  rviz
  urdf
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
