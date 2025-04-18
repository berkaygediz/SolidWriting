#include "sw_threading.h"
#include <QDebug>
#include <QThread>

ThreadingEngine::ThreadingEngine(float adaptiveResponse, QObject *parent)
    : QThread(parent), m_adaptiveResponse(adaptiveResponse), m_running(false) {}

ThreadingEngine::~ThreadingEngine() {}

void ThreadingEngine::run() {
  if (m_running) {
    return;
  }
  m_running = true;

  QThread::sleep(static_cast<int>(0.15 * m_adaptiveResponse));

  emit update();

  m_running = false;
}
