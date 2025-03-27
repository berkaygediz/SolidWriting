cmake_minimum_required(VERSION 3.16)

project(SolidWriting VERSION 0.1 LANGUAGES CXX)

set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_PREFIX_PATH "C:/Qt/6.8.3/msvc2022_64")

find_package(Qt NAMES Qt6 Qt5 REQUIRED COMPONENTS Core Gui OpenGLWidgets Widgets)

set(PROJECT_SOURCES
        main.cpp
        rs_workspace.cpp
        rs_workspace.h
        ThreadingEngine.h
        ThreadingEngine.cpp
        globals.cpp
        globals.h
        rs_workspace.ui
)

include(GNUInstallDirs)

if(QT_VERSION_MAJOR EQUAL 6)
    qt_finalize_executable(SolidWriting)
endif()
