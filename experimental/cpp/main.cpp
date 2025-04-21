#include "sw_controlinfo.h"

#include <QApplication>
#include <QDir>
#include <QIcon>
#include <QString>

int main(int argc, char *argv[]) {
  QApplication app(argc, argv);

  app.setOrganizationName("berkaygediz");
  app.setApplicationName("SolidWriting");
  app.setApplicationDisplayName("SolidWriting 2025.04");
  app.setApplicationVersion("1.5.2025.04-2");

  app.setWindowIcon(QIcon(":/resources/icons/solidwriting_icon.png"));

  SW_ControlInfo sw;
  return app.exec();
}