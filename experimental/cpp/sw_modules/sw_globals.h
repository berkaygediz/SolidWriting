#ifndef SW_GLOBALS_H
#define SW_GLOBALS_H

#include <QMap>
#include <QString>
#include <QVariant>

class Globals {
public:
  static QMap<QString, QVariant> fallbackValues;
  static QMap<QString, QString> languages;
  static QMap<QString, QMap<QString, QString>> translations;
};

#endif // SW_GLOBALS_H
