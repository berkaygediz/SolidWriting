#ifndef SW_CONTROLINFO_H
#define SW_CONTROLINFO_H

#include "sw_about.h"
#include <QMainWindow>
#include <QTimer>

class QLabel;
class QVBoxLayout;
class QWidget;
class SW_Workspace;

class SW_ControlInfo : public QMainWindow {
  Q_OBJECT

public:
  explicit SW_ControlInfo(QWidget *parent = nullptr);

private slots:
  void showWS();

private:
  QWidget *widgetCentral;
  QVBoxLayout *layoutCentral;
  QLabel *title;
  SW_About *wsWindow;
};

#endif // SW_CONTROLINFO_H
