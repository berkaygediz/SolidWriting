#include "ThreadingEngine.h"
#include <QMutexLocker>
#include <QThread>

ThreadingEngine::ThreadingEngine(double adaptiveResponse, QObject *parent)
    : QThread(parent), adaptiveResponse(adaptiveResponse), running(false) {}

void ThreadingEngine::run() {
  if (!running) {
    QMutexLocker locker(&mutex);
    running = true;

    QThread::msleep(
        static_cast<int>(150 * adaptiveResponse)); // 0.15 * adaptiveResponse
    emit update();

    running = false;
  }
}
