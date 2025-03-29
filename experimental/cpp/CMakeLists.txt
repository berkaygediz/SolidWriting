cmake_minimum_required(VERSION 3.16)

project(SolidWriting VERSION 0.1 LANGUAGES CXX)

# Qt6 veya Qt5 için gerekli modülleri bul
find_package(Qt6 REQUIRED COMPONENTS Core Gui OpenGLWidgets Widgets)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(PROJECT_SOURCES
    main.cpp
    sw_workspace.cpp
    sw_workspace.h
    ThreadingEngine.h
    ThreadingEngine.cpp
    globals.cpp
    globals.h
    sw_workspace.ui
)

# UI dosyasını işlemek
qt_wrap_ui(UI_HEADERS rs_workspace.ui)

add_executable(SolidWriting ${PROJECT_SOURCES} ${UI_HEADERS})

# Qt6 kullanıyorsanız uygulamayı sonlandır
if(QT_VERSION_MAJOR EQUAL 6)
    qt_finalize_executable(SolidWriting)
endif()
