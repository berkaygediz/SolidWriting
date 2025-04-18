#ifndef SW_ABOUT_H
#define SW_ABOUT_H

#include <QMainWindow>

class QLabel;
class QPushButton;

class SW_About : public QMainWindow {
  Q_OBJECT

public:
  explicit SW_About(QWidget *parent = nullptr);

private slots:
  void donationLink(const QString &origin);

private:
  QLabel *aboutLabel;
  QPushButton *donateGithub;
  QPushButton *donateBuyMeACoffee;
};

#endif // SW_ABOUT_H
