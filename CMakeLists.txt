cmake_minimum_required(VERSION 2.8.3)
project(task_behavior_engine)

find_package(catkin REQUIRED)

catkin_python_setup()

catkin_package(
)

###########
## Build ##
###########

#############
## Install ##
#############
install(DIRECTORY example
        DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)


#############
## Testing ##
#############

## Add folders to be run by python nosetests
catkin_add_nosetests(test)
