cmake_minimum_required(VERSION 3.21)
project(SolidWriting LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 6.9 REQUIRED COMPONENTS Core Gui Widgets OpenGLWidgets PrintSupport OpenGL)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

qt_standard_project_setup()

add_subdirectory(${CMAKE_SOURCE_DIR}/externals/llama.cpp)

qt_add_executable(SolidWriting
    WIN32 MACOSX_BUNDLE
    main.cpp
    sw_modules/sw_crypto.cpp
    sw_modules/sw_crypto.h
    sw_modules/sw_globals.cpp
    sw_modules/sw_globals.h
    sw_modules/sw_threading.cpp
    sw_modules/sw_threading.h
    sw_controlinfo.cpp
    sw_controlinfo.h
    sw_about.cpp
    sw_about.h
)

target_include_directories(SolidWriting PUBLIC
    ${CMAKE_SOURCE_DIR}/sw_modules
    ${CMAKE_SOURCE_DIR}/sw_modules/llama.cpp/include
    ${CMAKE_SOURCE_DIR}/sw_modules/llama.cpp/ggml/include
)

target_link_libraries(SolidWriting
    PUBLIC
    Qt::Core
    Qt::Gui
    Qt::Widgets
    Qt::OpenGLWidgets
    Qt::PrintSupport
    Qt::OpenGL
    llama
)

set(CMAKE_GENERATOR_PLATFORM x64)

include(GNUInstallDirs)

install(TARGETS SolidWriting
    BUNDLE DESTINATION .
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
)

qt_generate_deploy_app_script(
    TARGET SolidWriting
    OUTPUT_SCRIPT deploy_script
    NO_UNSUPPORTED_PLATFORM_ERROR
)
install(SCRIPT ${deploy_script})