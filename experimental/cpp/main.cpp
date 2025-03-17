#include "rs_workspace.h"

#include <QApplication>
#include <QDebug>
#include <QDir>
#include <QIcon>
#include <QLocale>
#include <QStandardPaths>
#include <QToolBar>
#include <stdio.h>
#include <windows.h>

int main(int argc, char *argv[]) {
  QString applicationPath;
#ifdef Q_OS_WIN
  if (GetModuleFileName(NULL, NULL, 0) != 0) {
    applicationPath = QCoreApplication::applicationDirPath();
  }
#else
  applicationPath = QCoreApplication::applicationDirPath();
#endif
  qDebug() << "Application Path:" << applicationPath;

  QApplication app(argc, argv);
  app.setWindowIcon(QIcon(":/resources/solidwriting_icon.ico"));
  app.setOrganizationName("berkaygediz");
  app.setApplicationName("SolidWriting");
  app.setApplicationDisplayName("SolidWriting 2024.12");
  app.setApplicationVersion("1.5.2024.12");
  RS_Workspace ws;
  ws.show();
  return app.exec();
}
