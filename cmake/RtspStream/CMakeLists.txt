cmake_minimum_required(VERSION 3.5.0)
project(RtspStream)

LIST(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/../cmake-modules") 
INCLUDE("${CMAKE_CURRENT_LIST_DIR}/../cmake-modules/CommonSetup.cmake")
CommonSetup()

IncludeEigen()

find_package(OpenCV REQUIRED)

set(ENV{PKG_CONFIG_PATH} /usr/lib/x86_x64-linux-gnu/pkgconfig)
find_package(PkgConfig REQUIRED)

message(STATUS "gst 1.0")
#pkg_check_modules(GSTREAMER REQUIRED gstreamer-1.0)
#pkg_check_modules(GST_APP REQUIRED gstreamer-app-1.0)
#pkg_check_modules(GST_RTSP REQUIRED gstreamer1.0-rtsp)

pkg_check_modules(GST_FULL REQUIRED gstreamer-1.0 gstreamer-video-1.0 gstreamer-pbutils-1.0 gstreamer-rtsp-1.0 gstreamer-rtp-1.0 gstreamer-app-1.0 gstreamer-rtsp-server-1.0)

SetupConsoleBuild()

## Specify additional locations of header files
include_directories(
  ${AIRSIM_ROOT}/RtspStream
  ${AIRSIM_ROOT}/AirLib/include
  ${RPC_LIB_INCLUDES}
  ${GLIB_INCLUDE_DIRS}
  #${GST_APP_INCLUDE_DIRS}
  ${GST_FULL_INCLUDE_DIRS}
  ${OpenCV_INCLUDE_DIRS}
)

AddExecutableSource()
			
CommonTargetLink()

#target_link_libraries(${PROJECT_NAME} AirLib)
#target_link_libraries(${PROJECT_NAME} ${RPC_LIB})
#target_link_libraries(${PROJECT_NAME} ${GSTREAMER_LIBRARIES} ${GST_APP_LIBRARIES})

# target_link_libraries(${PROJECT_NAME} ${GST_FULL_LIBRARIES})
target_link_libraries(${PROJECT_NAME} AirLib ${RPC_LIB} ${GST_FULL_LIBRARIES})