#ifndef THREADINGENGINE_H
#define THREADINGENGINE_H

#include <QMutex>
#include <QThread>

class ThreadingEngine : public QThread {
  Q_OBJECT

public:
  explicit ThreadingEngine(double adaptiveResponse, QObject *parent = nullptr);

signals:
  void update();

protected:
  void run() override;

private:
  double adaptiveResponse;
  bool running;
  QMutex mutex;
};

#endif // THREADINGENGINE_H
