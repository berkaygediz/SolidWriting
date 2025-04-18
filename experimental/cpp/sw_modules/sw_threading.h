#ifndef SW_THREADING_H
#define SW_THREADING_H

#include <QObject>
#include <QThread>

class ThreadingEngine : public QThread {
  Q_OBJECT

public:
  explicit ThreadingEngine(float adaptiveResponse, QObject *parent = nullptr);
  ~ThreadingEngine();

signals:
  void update();

protected:
  void run() override;

private:
  float m_adaptiveResponse;
  bool m_running;
};

#endif // SW_THREADING_H
