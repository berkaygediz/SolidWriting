#include "sw_crypto.h"
#include <QByteArray>
#include <QCryptographicHash>

CryptoEngine::CryptoEngine(const QString &key) {
  QCryptographicHash hash(QCryptographicHash::Md5);
  hash.addData(key.toUtf8());
  this->key = hash.result();
}

QString CryptoEngine::b64Encrypt(const QString &content) {
  QByteArray encryptedContent = content.toUtf8();

  for (int i = 0; i < encryptedContent.size(); ++i) {
    encryptedContent[i] ^= this->key[i % this->key.size()];
  }

  return QString::fromUtf8(encryptedContent.toBase64());
}

QString CryptoEngine::b64Decrypt(const QString &encryptedContent) {
  QByteArray decodedContent = QByteArray::fromBase64(encryptedContent.toUtf8());
  QByteArray decryptedContent = decodedContent;

  for (int i = 0; i < decryptedContent.size(); ++i) {
    decryptedContent[i] ^= this->key[i % this->key.size()];
  }

  return QString::fromUtf8(decryptedContent);
}
