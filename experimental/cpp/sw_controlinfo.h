#ifndef SW_CONTROLINFO_H
#define SW_CONTROLINFO_H

#include "sw_workspace.h"
#include <QIcon>
#include <QMainWindow>
#include <QTimer>

class QLabel;
class QVBoxLayout;
class QWidget;
class QMainWindow;
class SW_Workspace;

class SW_ControlInfo : public QMainWindow {
  Q_OBJECT

public:
  explicit SW_ControlInfo(QMainWindow *parent = nullptr);

private slots:
  void showWS();

private:
  QWidget *widgetCentral;
  QVBoxLayout *layoutCentral;
  QLabel *title;
  SW_Workspace *wsWindow;
};

#endif // SW_CONTROLINFO_H
