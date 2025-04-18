#include "sw_controlinfo.h"
#include "sw_about.h"

#include <QApplication>
#include <QFont>
#include <QGuiApplication>
#include <QIcon>
#include <QLabel>
#include <QScreen>
#include <QStyle>
#include <QTimer>
#include <QVBoxLayout>
#include <QWidget>

SW_ControlInfo::SW_ControlInfo(QWidget *parent)
    : QMainWindow(parent), wsWindow(nullptr) {
  setAttribute(Qt::WA_TranslucentBackground);
  setWindowModality(Qt::ApplicationModal);
  setWindowFlags(Qt::FramelessWindowHint);
  setWindowOpacity(0.75);

  QString iconPath =
      QCoreApplication::applicationDirPath() + "/resources/icons/app_icon.png";
  setWindowIcon(QIcon(iconPath));

  QRect screenGeometry = QGuiApplication::primaryScreen()->availableGeometry();
  QSize size(screenGeometry.width() * 0.2, screenGeometry.height() * 0.2);
  QRect alignedRect = QStyle::alignedRect(Qt::LeftToRight, Qt::AlignCenter,
                                          size, screenGeometry);
  setGeometry(alignedRect);

  setStyleSheet("background-color: transparent;");

  widgetCentral = new QWidget(this);
  layoutCentral = new QVBoxLayout(widgetCentral);

  title = new QLabel("SolidWriting", this);
  title->setAlignment(Qt::AlignCenter);
  title->setFont(QFont("Roboto", 30));
  title->setStyleSheet(
      "background-color: #0D47A1; color: #FFFFFF; font-weight: bold; "
      "font-size: 30px; border-radius: 25px; border: 1px solid #021E56;");

  layoutCentral->addWidget(title);
  setCentralWidget(widgetCentral);

  QTimer::singleShot(500, this, SLOT(showWS()));
}

void SW_ControlInfo::showWS() {
  this->hide();
  wsWindow = new SW_About();
  wsWindow->show();
}
