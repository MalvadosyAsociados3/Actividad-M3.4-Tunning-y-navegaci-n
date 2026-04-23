cmake_minimum_required(VERSION 3.8)
project(puzzlebot_navigation2)

find_package(ament_cmake REQUIRED)

install(DIRECTORY
  config
  launch
  maps
  rviz
  DESTINATION share/${PROJECT_NAME}
)

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/scripts")
  install(PROGRAMS
    scripts/send_goal.py
    scripts/set_initial_pose.py
    scripts/go_and_return.py
    DESTINATION lib/${PROJECT_NAME}
  )
endif()

ament_package()
