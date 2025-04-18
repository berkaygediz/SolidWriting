#ifndef SW_CRYPTO_H
#define SW_CRYPTO_H

#include <QByteArray>
#include <QString>

class CryptoEngine {
public:
  explicit CryptoEngine(const QString &key);
  QString b64Encrypt(const QString &content);
  QString b64Decrypt(const QString &encryptedContent);

private:
  QByteArray key;
};

#endif // SW_CRYPTO_H
