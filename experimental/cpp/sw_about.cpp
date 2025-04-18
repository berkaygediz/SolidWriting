#include "sw_about.h"

#include <QApplication>
#include <QDesktopServices>
#include <QHBoxLayout>
#include <QIcon>
#include <QLabel>
#include <QPushButton>
#include <QScreen>
#include <QStyle>
#include <QUrl>
#include <QVBoxLayout>

SW_About::SW_About(QWidget *parent) : QMainWindow(parent) {
  setWindowFlags(Qt::Dialog);
  setWindowModality(Qt::ApplicationModal);
  setWindowIcon(QIcon(QApplication::applicationDirPath() +
                      "/resources/icons/solidwriting_icon.png"));

  QRect screenGeometry = QGuiApplication::primaryScreen()->availableGeometry();
  QRect alignedRect = QStyle::alignedRect(Qt::LeftToRight, Qt::AlignCenter,
                                          size(), screenGeometry);
  setGeometry(alignedRect);

  QWidget *centralWidget = new QWidget(this);
  setCentralWidget(centralWidget);
  QVBoxLayout *mainLayout = new QVBoxLayout(centralWidget);

  aboutLabel = new QLabel(this);
  aboutLabel->setWordWrap(true);
  aboutLabel->setTextInteractionFlags(Qt::TextSelectableByMouse);
  aboutLabel->setTextFormat(Qt::RichText);
  aboutLabel->setText(
      "<center>"
      "<b>SolidWriting 2025.04</b><br><br>"
      "A supercharged word processor with AI integration, supporting real-time "
      "computing and advanced formatting.<br><br>"
      "Made by Berkay Gediz<br><br>"
      "GNU General Public License v3.0<br>GNU LESSER GENERAL PUBLIC LICENSE "
      "v3.0<br>Mozilla Public License Version 2.0<br><br>"
      "<b>Libraries: </b>ggml-org/llama.cpp<br><br>"
      "OpenGL: <b>ON</b>"
      "</center>");

  mainLayout->addWidget(aboutLabel);

  QHBoxLayout *buttonLayout = new QHBoxLayout();

  donateGithub = new QPushButton("GitHub Sponsors", this);
  connect(donateGithub, &QPushButton::clicked, this,
          [=]() { donationLink("github"); });
  buttonLayout->addWidget(donateGithub);

  donateBuyMeACoffee = new QPushButton("Buy Me a Coffee", this);
  connect(donateBuyMeACoffee, &QPushButton::clicked, this,
          [=]() { donationLink("buymeacoffee"); });
  buttonLayout->addWidget(donateBuyMeACoffee);

  // QLabel *newLabel = new QLabel(this);
  // newLabel->setText(
  //     Globals::translations[currentLanguage].value("welcome-title", "???"));
  // mainLayout->addWidget(newLabel);

  mainLayout->addLayout(buttonLayout);
}

void SW_About::donationLink(const QString &origin) {
  if (origin == "github") {
    QDesktopServices::openUrl(QUrl("https://github.com/sponsors/berkaygediz"));
  } else if (origin == "buymeacoffee") {
    QDesktopServices::openUrl(QUrl("https://buymeacoffee.com/berkaygediz"));
  }
}
