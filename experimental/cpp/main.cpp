#include <QApplication>
#include <QDebug>
#include <QFile>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QString>
#include <QTextEdit>
#include <QThread>
#include <QVBoxLayout>
#include <QWidget>

#include "llama.h"

llama_model *model = nullptr;
llama_context *ctx = nullptr;
llama_sampler *sampler = nullptr;

bool init_llama() {
  QString modelPath = "";
  if (!QFile::exists(modelPath)) {
    qCritical() << "Model dosyası bulunamadı: " << modelPath;
    return false;
  }

  qDebug() << "Model dosyası bulundu. Yükleniyor...";

  llama_backend_init();

  llama_model_params model_params = llama_model_default_params();
  model =
      llama_model_load_from_file(modelPath.toStdString().c_str(), model_params);
  if (!model) {
    qCritical() << "Model yüklenemedi!";
    return false;
  }

  qDebug() << "Model başarıyla yüklendi.";

  llama_context_params ctx_params = llama_context_default_params();
  ctx_params.n_ctx = 2048;
  ctx = llama_init_from_model(model, ctx_params);
  if (!ctx) {
    qCritical() << "Model bağlanırken hata oluştu!";
    return false;
  }

  llama_sampler_chain_params sparams = llama_sampler_chain_default_params();
  sampler = llama_sampler_chain_init(sparams);
  llama_sampler_chain_add(sampler, llama_sampler_init_top_k(40));
  llama_sampler_chain_add(sampler, llama_sampler_init_top_p(0.9f, 1));
  llama_sampler_chain_add(sampler, llama_sampler_init_temp(0.8f));
  llama_sampler_chain_add(sampler, llama_sampler_init_dist(42));

  qDebug() << "Model başarıyla başlatıldı ve hazır.";

  return true;
}

QString token_to_string(llama_token token) {
  char buf[128] = {0};
  const struct llama_vocab *vocab = llama_model_get_vocab(model);
  llama_token_to_piece(vocab, token, buf, sizeof(buf), 0, false);
  return QString::fromUtf8(buf);
}

QString generate_response(const QString &prompt) {
  std::string input = prompt.toStdString();

  qDebug() << "Tokenizing input...";

  const struct llama_vocab *vocab = llama_model_get_vocab(model);
  std::vector<llama_token> tokens(input.size() + 8);
  int n_tokens = llama_tokenize(vocab, input.c_str(),
                                static_cast<int>(input.size()), tokens.data(),
                                static_cast<int>(tokens.size()), true, false);
  if (n_tokens < 0) {
    qCritical() << "Tokenize işlemi başarısız!";
    return "[Tokenize edilemedi]";
  }

  qDebug() << "Tokenize başarıyla tamamlandı!";

  llama_batch batch = llama_batch_init(static_cast<int>(tokens.size()), 0, 1);
  for (size_t i = 0; i < static_cast<size_t>(tokens.size()); ++i) {
    batch.token[i] = tokens[i];
    batch.pos[i] = static_cast<llama_pos>(i);
    batch.n_seq_id[i] = 1;
    batch.seq_id[i] = nullptr;
    batch.logits[i] = false;
  }

  llama_decode(ctx, batch);
  llama_batch_free(batch);

  QString result;
  for (int i = 0; i < 64; ++i) {
    llama_token token = llama_sampler_sample(sampler, ctx, -1);
    if (llama_vocab_is_eog(vocab, token))
      break;

    result += token_to_string(token);

    llama_batch batch_out = llama_batch_init(1, 0, 1);
    batch_out.token[0] = token;
    batch_out.pos[0] = static_cast<int>(tokens.size()) + i;
    batch_out.n_seq_id[0] = 1;
    batch_out.seq_id[0] = nullptr;
    batch_out.logits[0] = false;
    llama_decode(ctx, batch_out);
    llama_batch_free(batch_out);

    llama_sampler_accept(sampler, token);
  }

  return result;
}

class GenerateResponseThread : public QThread {
  Q_OBJECT
public:
  GenerateResponseThread(const QString &inputText, QTextEdit *chatDisplay)
      : input(inputText), display(chatDisplay) {}

  void run() override {
    try {
      qDebug() << "Yanıt üretmeye başlandı...";
      QString response = generate_response(input);
      emit responseReady(response);
    } catch (const std::exception &e) {
      qCritical() << "Yanıt üretme sırasında hata: " << e.what();
      emit responseReady("[Yanıt üretilemedi]");
    }
  }

signals:
  void responseReady(const QString &response);

private:
  QString input;
  QTextEdit *display;
};

int main(int argc, char *argv[]) {
  QApplication app(argc, argv);

  qDebug() << "Qt Uygulama başlatıldı!";

  if (!init_llama()) {
    qCritical() << "LLaMA başlatılamadı!";
    return -1;
  }

  qDebug() << "LLaMA başlatıldı.";

  QWidget window;
  window.setWindowTitle("🦙 LLaMA Chat (Qt6)");

  QVBoxLayout *layout = new QVBoxLayout(&window);

  QLabel *label = new QLabel("💬 Mesaj:");
  layout->addWidget(label);

  QTextEdit *chatDisplay = new QTextEdit();
  chatDisplay->setReadOnly(true);
  layout->addWidget(chatDisplay);

  QLineEdit *inputField = new QLineEdit();
  layout->addWidget(inputField);

  QPushButton *sendButton = new QPushButton("Gönder");
  layout->addWidget(sendButton);

  QObject::connect(sendButton, &QPushButton::clicked, [&]() {
    QString userInput = inputField->text();
    if (!userInput.isEmpty()) {
      chatDisplay->append("👤 Siz: " + userInput);

      GenerateResponseThread *thread =
          new GenerateResponseThread(userInput, chatDisplay);
      QObject::connect(thread, &GenerateResponseThread::responseReady,
                       [&](const QString &response) {
                         chatDisplay->append("🤖 LLaMA: " + response);
                       });

      thread->start();
      inputField->clear();
    }
  });

  window.resize(520, 420);
  window.show();

  return app.exec();
}

#include "main.moc"
