#include "./ui_rs_workspace.h"
#include "globals.h"
#include "rs_workspace.h"
#include <QAction>
#include <QApplication>
#include <QCloseEvent>
#include <QColor>
#include <QColorDialog>
#include <QDebug>
#include <QDir>
#include <QException>
#include <QFileDialog>
#include <QFontDialog>
#include <QIcon>
#include <QInputDialog>
#include <QKeySequence>
#include <QLabel>
#include <QLocale>
#include <QMainWindow>
#include <QMap>
#include <QMessageBox>
#include <QMimeDatabase>
#include <QObject>
#include <QOpenGLWidget>
#include <QPageLayout>
#include <QPalette>
#include <QRegularExpression>
#include <QSettings>
#include <QStatusBar>
#include <QString>
#include <QTextCursor>
#include <QTextDocument>
#include <QTextEdit>
#include <QTextListFormat>
#include <QThread>
#include <QTimer>
#include <QVBoxLayout>
#include <QWidget>
#include <QtPrintSupport/QPrintPreviewDialog>
#include <QtPrintSupport/QPrinter>
#include <qdockwidget.h>

#ifdef Q_OS_WIN
#include <Windows.h>

#include <shellapi.h>
#endif

using namespace std::chrono;
using std::string;

FallbackValues fallback;

#include <Windows.h>
#include <shellapi.h>

RS_Workspace::RS_Workspace(QWidget *parent)
    : QMainWindow(parent), isSaved(false), llm(nullptr),
      ui(new Ui::RS_Workspace) {
  ui->setupUi(this);
  QTimer::singleShot(0, this, &RS_Workspace::initUI);
}

RS_Workspace::~RS_Workspace() { delete ui; }

void RS_Workspace::readSettings() {
  try {
    QSettings settings("berkaygediz", "SolidWriting");
    QString lang = settings.value("appLanguage").toString();

    if (lang.isEmpty()) {
      settings.setValue("appLanguage", "1252");
      settings.sync();
    }

    if (settings.value("adaptiveResponse").isNull()) {
      settings.setValue("adaptiveResponse", 1);
      settings.sync();
    }
  } catch (const QException &e) {
    qWarning() << "Error while reading settings: " << e.what();
  }
}

void RS_Workspace::initUI() {
  auto starttime = QDateTime::currentDateTime();
  FallbackValues fallback;
  setWindowIcon(QIcon(":/resources/solidwriting_icon.ico"));
  setWindowModality(Qt::ApplicationModal);

  setMinimumSize(768, 540);

  QString system_language = QLocale::system().name().section('_', 0, 0);
  if (!languages.contains(system_language)) {
    QSettings settings;
    settings.setValue("appLanguage", "1252");
    settings.sync();
  }

  QSettings settings;
  if (settings.value("adaptiveResponse") == QVariant()) {
    settings.setValue("adaptiveResponse", 1);
    settings.sync();
  }
  QWidget *centralWidget = new QWidget(this);
  QVBoxLayout *layout = new QVBoxLayout(centralWidget);

  documentArea = new QTextEdit(this);
  documentArea->setFocus();
  documentArea->setAcceptRichText(true);
  documentArea->setTextInteractionFlags(Qt::TextEditorInteraction);
  layout->addWidget(documentArea);

  setCentralWidget(centralWidget);

  connect(documentArea, &QTextEdit::textChanged, this,
          &RS_Workspace::updateStatistics);

  themePalette();
  selectedFile = "";
  fileName = "";
  isSaved = false;
  defaultDirectory = QDir::homePath();
  directory = defaultDirectory;

  LLMinitDock();
  QStatusBar *status_bar = statusBar();
  // documentArea->setContextMenuPolicy(Qt::CustomContextMenu);
  // connect(documentArea,
  //         &QTextEdit::customContextMenuRequested,
  //         this,
  //         &RS_Workspace::showContextMenu);

  initArea();

  documentArea->setDisabled(true);

  initActions();
  initToolbar();

  adaptiveResponse = settings.value("adaptiveResponse").toInt();
  setPalette(lightTheme);

  showMaximized();

  // QTimer::singleShot(50 * adaptiveResponse, this,
  // &RS_Workspace::restoreTheme); QTimer::singleShot(150 * adaptiveResponse,
  // this, &RS_Workspace::restoreState);

  documentArea->setDisabled(false);

  updateTitle();

  auto endtime = QDateTime::currentDateTime();
  status_bar->showMessage(QString::number(starttime.msecsTo(endtime)) + " ms",
                          2500);

  // if (acceleratorHardware() == "cpu") {
  //     LLMwarningCPU();
  // }
}

void RS_Workspace::changeLanguage() {
  QSettings settings;
  settings.setValue("appLanguage", language_combobox->currentData());
  settings.sync();

  toolbarTranslate();
  updateStatistics();
  updateTitle();
}

void RS_Workspace::updateTitle() {
  QSettings settings;
  QString lang = settings.value("appLanguage").toString();

  QString file = !fileName.isEmpty() ? fileName : translations[lang]["new"];
  QString textMode =
      file.endsWith(".docx") ? translations[lang]["readonly"] : "";

  QString asterisk = textMode.isEmpty() && !isSaved ? "*" : "";

  setWindowTitle(file + asterisk + textMode + " — " +
                 qApp->applicationDisplayName());
}

// void RS_Workspace::threadStart() {
//     if (!thread_running) {
//         solidwriting_thread->start();
//         thread_running = true;
//     }
// }

// void RS_Workspace::textChanged() {
//     if (!text_changed_timer->isActive()) {
//         text_changed_timer->start();
//     }
// }

void RS_Workspace::closeEvent(QCloseEvent *event) {
  QSettings settings;
  QString lang = settings.value("appLanguage").toString();

  if (!isSaved) {
    QMessageBox::StandardButton reply = QMessageBox::question(
        this, qApp->applicationDisplayName(), "Exit",
        QMessageBox::Yes | QMessageBox::No, QMessageBox::No);

    if (reply == QMessageBox::Yes) {
      // saveState();
      event->accept();
    } else {
      // saveState();
      event->ignore();
    }
  } else {
    // saveState();
    event->accept();
  }
}
void RS_Workspace::updateStatistics() {
  QString text = documentArea->toPlainText();

  int character_count = text.length();
  int word_count =
      text.split(QRegularExpression("\\s+"), Qt::SkipEmptyParts).size();
  int line_count = text.count("\n") + 1;

  double avg_word_length = 0.0;
  double avg_line_length = 0.0;
  int uppercase_count = 0;
  int lowercase_count = 0;
  QString detected_language;
  QString lang = settings.value("appLanguage").toString();

  if (word_count > 0 && line_count > 0 && character_count > 0 &&
      !text.isEmpty()) {
    avg_word_length = static_cast<double>(character_count) / word_count;
    avg_line_length = static_cast<double>(character_count) / line_count;

    for (QChar c : text) {
      if (c.isUpper())
        uppercase_count++;
      if (c.isLower())
        lowercase_count++;
    }
  }

  QString statistics = "<html><head><style>"
                       "table {border-collapse: collapse; width: 100%;}"
                       "th, td {text-align: left; padding: 10px;}"
                       "tr:nth-child(even) {background-color: #f2f2f2;}"
                       "tr:hover {background-color: #ddd;}"
                       "th {background-color: #0379FF; color: white;}"
                       "td {color: white;}"
                       "#rs-text {background-color: #E2E3E1; color: #000000;}"
                       "</style></head><body><table><tr>";

  statistics += QString("<th>%1</th>").arg(translations[lang]["analysis"]);
  statistics += QString("<td>%1</td>")
                    .arg(translations[lang]["analysis_message_1"].arg(
                        QString::number(avg_word_length, 'f', 1)));
  statistics += QString("<td>%1</td>")
                    .arg(translations[lang]["analysis_message_2"].arg(
                        QString::number(avg_line_length, 'f', 1)));
  statistics +=
      QString("<td>%1</td>")
          .arg(translations[lang]["analysis_message_3"].arg(uppercase_count));
  statistics +=
      QString("<td>%1</td>")
          .arg(translations[lang]["analysis_message_4"].arg(lowercase_count));

  if (!detected_language.isEmpty()) {
    statistics += QString("<td>%1</td>")
                      .arg(translations[lang]["analysis_message_5"].arg(
                          detected_language));
  }

  statistics += QString("<th>%1</th>").arg(translations[lang]["statistic"]);
  statistics +=
      QString("<td>%1</td>")
          .arg(translations[lang]["statistic_message_1"].arg(line_count));
  statistics +=
      QString("<td>%1</td>")
          .arg(translations[lang]["statistic_message_2"].arg(word_count));
  statistics +=
      QString("<td>%1</td>")
          .arg(translations[lang]["statistic_message_3"].arg(character_count));

  statistics +=
      QString("<th id='rs-text'>%1</th>").arg(qApp->applicationDisplayName());

  statistics += "</tr></table></body></html>";

  QString new_text = documentArea->toPlainText();
  if (new_text != fallback.content) {
    isSaved = false;
  } else {
    isSaved = true;
  }

  updateTitle();
}

void RS_Workspace::themePalette() {
  lightTheme.setColor(QPalette::Window, QColor(3, 65, 135));
  lightTheme.setColor(QPalette::WindowText, QColor(255, 255, 255));
  lightTheme.setColor(QPalette::Base, QColor(255, 255, 255));
  lightTheme.setColor(QPalette::Text, QColor(0, 0, 0));
  lightTheme.setColor(QPalette::Highlight, QColor(105, 117, 156));
  lightTheme.setColor(QPalette::Button, QColor(0, 0, 0));
  lightTheme.setColor(QPalette::ButtonText, QColor(255, 255, 255));

  darkTheme.setColor(QPalette::Window, QColor(35, 39, 52));
  darkTheme.setColor(QPalette::WindowText, QColor(255, 255, 255));
  darkTheme.setColor(QPalette::Base, QColor(80, 85, 122));
  darkTheme.setColor(QPalette::Text, QColor(255, 255, 255));
  darkTheme.setColor(QPalette::Highlight, QColor(105, 117, 156));
  darkTheme.setColor(QPalette::Button, QColor(0, 0, 0));
  darkTheme.setColor(QPalette::ButtonText, QColor(255, 255, 255));
}

void RS_Workspace::themeAction() {
  if (palette() == lightTheme) {
    setPalette(darkTheme);
    settings.setValue("appTheme", "dark");
  } else {
    setPalette(lightTheme);
    settings.setValue("appTheme", "light");
  }
  toolbarTheme();
}

void RS_Workspace::toolbarTheme() {
  QPalette currentPalette = palette();
  QColor textColor = (currentPalette == lightTheme) ? QColor(255, 255, 255)
                                                    : QColor(255, 255, 255);

  foreach (QToolBar *toolbar, findChildren<QToolBar *>()) {
    foreach (QAction *action, toolbar->actions()) {
      if (!action->text().isEmpty()) {
        QPalette actionColor;
        actionColor.setColor(QPalette::ButtonText, textColor);
        actionColor.setColor(QPalette::WindowText, textColor);
        toolbar->setPalette(actionColor);
      }
    }
  }
}

void RS_Workspace::toolbarTranslate() {
  QString lang = settings.value("appLanguage", "en").toString();

  QMap<QAction *, QPair<QString, QString>> actions = {
      {newaction, {"new", "new_message"}},
      {openaction, {"open", "open_message"}},
      {saveaction, {"save", "save_message"}},
      {saveasaction, {"save_as", "save_as_message"}},
      {printaction, {"print", "print_message"}},
      {undoaction, {"undo", "undo_message"}},
      {redoaction, {"redo", "redo_message"}},
      {theme_action, {"darklight", "darklight_message"}},
      {powersaveraction, {"powersaver", "powersaver_message"}},
      {findaction, {"find", "find_message"}},
      {replaceaction, {"replace", "replace_message"}},
      {helpAction, {"help", "help"}},
      {aboutAction, {"about", "about"}},
      {alignrightevent, {"right", "right_message"}},
      {aligncenterevent, {"center", "center_message"}},
      {alignleftevent, {"left", "left_message"}},
      {alignjustifiedevent, {"justify", "justify_message"}},
      {bold, {"bold", "bold_message"}},
      {italic, {"italic", "italic_message"}},
      {underline, {"underline", "underline_message"}},
      {bulletevent, {"bullet", "bullet"}},
      {numberedevent, {"numbered", "numbered"}},
      {color, {"font_color", "font_color_message"}},
      {backgroundcolor,
       {"contentBackgroundColor", "contentBackgroundColor_message"}},
      {fontfamily, {"font", "font_message"}},
      {addimage, {"image", "image_message"}}};

  for (auto it = actions.begin(); it != actions.end(); ++it) {
    QAction *action = it.key();
    QString textKey = it.value().first;
    QString statusKey = it.value().second;

    action->setText(translations[lang][textKey]);
    action->setStatusTip(translations[lang][statusKey]);
  }

  ai_widget.setWindowTitle("AI");

  translateToolbarLabel(file_toolbar, "file", lang);
  translateToolbarLabel(ui_toolbar, "ui", lang);
  translateToolbarLabel(edit_toolbar, "edit", lang);
  translateToolbarLabel(font_toolbar, "font", lang);
  translateToolbarLabel(list_toolbar, "list", lang);
  translateToolbarLabel(color_toolbar, "color", lang);
  translateToolbarLabel(multimedia_toolbar, "multimedia", lang);
}

void RS_Workspace::translateToolbarLabel(QToolBar *toolbar,
                                         const QString &labelKey,
                                         const QString &lang) {
  QString translatedLabel = translations[lang].value(labelKey, labelKey) + ": ";
  updateToolbarLabel(toolbar, translatedLabel);
}

void RS_Workspace::updateToolbarLabel(QToolBar *toolbar,
                                      const QString &newLabel) {
  for (QObject *widget : toolbar->children()) {
    QLabel *label = qobject_cast<QLabel *>(widget);
    if (label) {
      label->setText(QString("<b>%1</b>").arg(newLabel));
      return;
    }
  }
}

void RS_Workspace::initArea() {
  documentArea->setFontFamily(fallback.fontFamily);
  documentArea->setFontPointSize(fallback.fontSize);
  documentArea->setFontWeight(100 ? fallback.bold : 50);
  documentArea->setFontItalic(fallback.italic);
  documentArea->setFontUnderline(fallback.underline);
  documentArea->setAlignment(fallback.contentAlign);
  documentArea->setTextColor(fallback.contentColor);
  documentArea->setTextBackgroundColor(fallback.contentBackgroundColor);
  documentArea->setTabStopDistance(27);
  documentArea->document()->setDocumentMargin(this->width() * 0.25);
}

void RS_Workspace::LLMwarningCPU() {
  QString message = "Your device does not have GPU support. Running intensive "
                    "AI operations on the CPU "
                    "may result in high CPU utilization, causing system "
                    "performance degradation and potential "
                    "long-term damage. This could lead to overheating, system "
                    "instability, or permanent hardware damage. "
                    "By proceeding with CPU usage, you acknowledge and accept "
                    "the risks associated with these operations. "
                    "Do you still wish to continue?";

  QMessageBox::StandardButton reply = QMessageBox::question(
      this, QString(), message, QMessageBox::Yes | QMessageBox::No,
      QMessageBox::No);

  if (reply == QMessageBox::Yes) {
    // QTimer::singleShot(500, this, &RS_Workspace::loadLLM);
  }

  if (reply == QMessageBox::No) {
    // ai_widget->setWidget(new QLabel("GPU/NPU not available."));
  }
}

void RS_Workspace::LLMinitDock() {
  QDockWidget *ai_widget = new QDockWidget("AI", this);
  ai_widget->setObjectName("AI");
  ai_widget->setAllowedAreas(Qt::LeftDockWidgetArea | Qt::RightDockWidgetArea);

  QVBoxLayout *main_layout = new QVBoxLayout();

  scrollableArea = new QScrollArea();
  messages_layout = new QVBoxLayout();

  input_text = new QTextEdit();
  input_text->setPlaceholderText("...");
  input_text->setFixedHeight(80);
  main_layout->addWidget(input_text);

  predict_button = new QPushButton("->");
  connect(predict_button, &QPushButton::clicked, this,
          &RS_Workspace::LLMpredict);
  main_layout->addWidget(predict_button);

  scrollableArea->setVerticalScrollBarPolicy(Qt::ScrollBarAsNeeded);
  scrollableArea->setHorizontalScrollBarPolicy(Qt::ScrollBarAsNeeded);
  scrollableArea->setWidgetResizable(true);

  QWidget *scroll_contents = new QWidget();
  scroll_contents->setLayout(messages_layout);
  scrollableArea->setWidget(scroll_contents);

  main_layout->addWidget(scrollableArea);

  QWidget *container = new QWidget();
  container->setLayout(main_layout);

  ai_widget->setWidget(container);
  ai_widget->setFeatures(QDockWidget::DockWidgetClosable);

  addDockWidget(Qt::RightDockWidgetArea, ai_widget);
}

void RS_Workspace::LLMmessage(const QString &text, bool is_user = true) {
  QString current_time =
      QDateTime::currentDateTime().toString("yyyy-MM-dd HH:mm:ss");

  // QString formatted_text = text.replace("\n", "<br>");
  // formatted_text = LLMconvertMarkdownHTML(formatted_text);

  QWidget *message_widget = new QWidget();
  QHBoxLayout *message_layout = new QHBoxLayout();

  // QString message_label_content = formatted_text;

  // message_label_content += QString("<br><br> (%1)").arg(current_time);

  QLabel *message_label = new QLabel(text);
  message_label->setWordWrap(true);
  message_label->setTextInteractionFlags(Qt::TextSelectableByMouse);
  message_label->setTextFormat(Qt::RichText);
  message_label->setMaximumWidth(400);

  if (is_user) {
    message_label->setStyleSheet(
        "background-color: #d1e7ff; color: #000; border-radius: 15px; padding: "
        "10px; margin: 5px;");
    message_layout->addWidget(message_label, Qt::AlignRight);
  } else {
    message_label->setStyleSheet(
        "background-color: #f1f1f1; color: #000; border-radius: 15px; padding: "
        "10px; margin: 5px;");
    message_layout->addWidget(message_label, Qt::AlignLeft);
  }

  message_widget->setLayout(message_layout);

  messages_layout->addWidget(message_widget);
}

void RS_Workspace::LLMpredict() {
  QString prompt = input_text->toPlainText().trimmed();

  if (prompt.isEmpty()) {
    LLMmessage("Please enter a question.", false);
    return;
  }

  LLMmessage(prompt, true);

  predict_button->setText("...");
  predict_button->setEnabled(false);

  // QTimer::singleShot(100, this, &RS_Workspace::LLMprompt);
}

void RS_Workspace::LLMcontextPredict(bool action_type) {
  QString selected_text = documentArea->textCursor().selectedText().trimmed();

  QString prompt;
  if (action_type) {
    prompt = QString("%1: %2").arg(action_type ? "Action" : "No Action",
                                   selected_text);
  } else {
    prompt = selected_text;
  }

  ai_widget.show();
  LLMmessage(prompt, true);
  predict_button->setText("...");
  predict_button->setEnabled(false);

  if (selected_text.isEmpty()) {
    LLMmessage("No text selected.", false); // Bot message
    return;
  }

  QTimer::singleShot(100, [this, prompt]() { LLMprompt(prompt); });
}

void RS_Workspace::LLMprompt(const QString &prompt) {
  if (!prompt.isEmpty()) {
    QString response = LLMresponse(prompt);
    LLMmessage(response, false); // Bot message
    input_text->clear();
  } else {
    LLMmessage("Please enter a question.", false); // Bot message
  }

  predict_button->setText("->");
  predict_button->setEnabled(true);
}

QString RS_Workspace::LLMresponse(const QString &prompt) {
  try {
    QString response = "Simulated response to: " + prompt;
    return response;
  } catch (const std::exception &e) {
    return QString("Error: %1").arg(e.what());
  }
}

QString RS_Workspace::LLMconvertMarkdownHTML(const QString &markdown_text) {
  QString text = LLMconvertCodeHTML(markdown_text);
  text = convertBoldItalic(text);
  return text;
}

QString RS_Workspace::convertBoldItalic(const QString &text) {
  QString modified_text = text;
  modified_text.replace(QRegularExpression("\\*\\*(.*?)\\*\\*"),
                        "<b>\\1</b>"); // **bold**
  modified_text.replace(QRegularExpression("__(.*?)__"),
                        "<b>\\1</b>"); // __bold__
  modified_text.replace(QRegularExpression("\\*(.*?)\\*"),
                        "<i>\\1</i>"); // *italic*
  modified_text.replace(QRegularExpression("_(.*?)_"),
                        "<i>\\1</i>"); // _italic_
  return modified_text;
}

QString RS_Workspace::LLMconvertCodeHTML(const QString &input_text) {
  QString modified_text = input_text;

  QRegularExpression code_block_regex(
      R"(\[code\](.*?)\[/code\])",
      QRegularExpression::DotMatchesEverythingOption);

  auto replace_code_block =
      [](const QRegularExpressionMatch &match) -> QString {
    QString code_content = match.captured(1);
    return "<pre><code>" + code_content + "</code></pre>";
  };

  QRegularExpressionMatchIterator matchIterator =
      code_block_regex.globalMatch(modified_text);

  int offset = 0;
  while (matchIterator.hasNext()) {
    QRegularExpressionMatch match = matchIterator.next();
    QString replacement = replace_code_block(match);
    modified_text.replace(match.capturedStart(), match.capturedLength(),
                          replacement);
  }

  return modified_text;
}

QString RS_Workspace::LLMescapeHTML(const QString &text) {
  QString modified_text = text;

  QRegularExpression html_escape_regex(R"([&<>\"'])");

  QRegularExpressionMatchIterator matchIterator =
      html_escape_regex.globalMatch(modified_text);

  int offset = 0;
  while (matchIterator.hasNext()) {
    QRegularExpressionMatch match = matchIterator.next();

    QString matched_char = match.captured(0);
    QString replacement;

    switch (matched_char[0].toLatin1()) {
    case '&':
      replacement = "&amp;";
      break;
    case '<':
      replacement = "&lt;";
      break;
    case '>':
      replacement = "&gt;";
      break;
    case '"':
      replacement = "&quot;";
      break;
    case '\'':
      replacement = "&#039;";
      break;
    default:
      replacement = matched_char;
      break;
    }

    modified_text.replace(match.capturedStart(), match.capturedLength(),
                          replacement);
  }

  return modified_text;
}

QAction *RS_Workspace::createAction(const QString &text,
                                    const QString &statusTip,
                                    std::function<void()> function,
                                    const QKeySequence &shortcut) {
  QAction *action = new QAction(text);
  action->setStatusTip(statusTip);

  connect(action, &QAction::triggered, this,
          [this, function]() { function(); });

  if (!shortcut.isEmpty()) {
    action->setShortcut(shortcut);
  }

  return action;
}

void RS_Workspace::toolbarLabel(QToolBar *toolbar, const QString &text) {
  QLabel *label = new QLabel("<b>" + text + "</b>");
  toolbar->addWidget(label);
}

void RS_Workspace::initActions() {
  struct ActionDefinition {
    QString name;
    QString text;
    QString statusTip;
    std::function<void()> function;
    QKeySequence shortcut;
  };

  QList<ActionDefinition> actionDefinitions = {
      {"newaction", "New", "Create a new file", [this]() { newFile(); },
       QKeySequence::New},
      {"openaction", "Open", "Open an existing file", [this]() { openFile(); },
       QKeySequence::Open},
      {"saveaction", "Save", "Save the current file", [this]() { saveFile(); },
       QKeySequence::Save},
      {"saveasaction", "Save As", "Save the file with a new name",
       [this]() { saveAs(); }, QKeySequence::SaveAs},
      {"printaction", "Print", "Print the document",
       [this]() { printDocument(); }, QKeySequence::Print},
      {"findaction", "Find", "Find text in the document", [this]() { find(); },
       QKeySequence::Find},
      {"replaceaction", "Replace", "Replace text in the document",
       [this]() { replace(); }, QKeySequence::Replace},
      {"undoaction", "Undo", "Undo the last action",
       [this]() { documentArea->undo(); }, QKeySequence::Undo},
      {"redoaction", "Redo", "Redo the last undone action",
       [this]() { documentArea->redo(); }, QKeySequence::Redo},
      {"alignrightevent", "Align Right", "Align the text to the right",
       [this]() { contentAlign(Qt::AlignRight); }, QKeySequence()},
      {"alignleftevent", "Align Left", "Align the text to the left",
       [this]() { contentAlign(Qt::AlignLeft); }, QKeySequence()},
      {"aligncenterevent", "Align Center", "Align the text to the center",
       [this]() { contentAlign(Qt::AlignCenter); }, QKeySequence()},
      {"alignjustifiedevent", "Justify", "Justify the text",
       [this]() { contentAlign(Qt::AlignJustify); }, QKeySequence()},
      {"bulletevent", "Bullet List", "Insert a bullet list",
       [this]() { bulletList(); }, QKeySequence("Ctrl+Shift+U")},
      {"numberedevent", "Numbered List", "Insert a numbered list",
       [this]() { numberedList(); }, QKeySequence("Ctrl+Shift+O")},
      {"bold", "Bold", "Bold the selected text", [this]() { contentBold(); },
       QKeySequence::Bold},
      {"italic", "Italic", "Italicize the selected text",
       [this]() { contentItalic(); }, QKeySequence::Italic},
      {"underline", "Underline", "Underline the selected text",
       [this]() { contentUnderline(); }, QKeySequence::Underline},
      {"color", "Font Color", "Change the font color",
       [this]() { contentColor(); }, QKeySequence("Ctrl+Shift+C")},
      {"backgroundcolor", "Background Color", "Change the background color",
       [this]() { contentBGColor(); }, QKeySequence("Ctrl+Shift+B")},
      {"fontfamily", "Font", "Change the font", [this]() { contentFont(); },
       QKeySequence("Ctrl+Shift+F")},
      {"inc_fontaction", "Increase Font", "Increase the font size",
       [this]() { incFont(); }, QKeySequence("Ctrl++")},
      {"dec_fontaction", "Decrease Font", "Decrease the font size",
       [this]() { decFont(); }, QKeySequence("Ctrl+-")},
      {"addimage", "Add Image", "Insert an image", [this]() { addImage(); },
       QKeySequence("Ctrl+Shift+P")},
      // {"helpAction",
      //  "Help",
      //  "View help documentation",
      //  [this]() { viewHelp(); },
      //  QKeySequence("Ctrl+H")},
      // {"aboutAction",
      //  "About",
      //  "View information about the application",
      //  [this]() { viewAbout(); },
      // QKeySequence("Ctrl+Shift+I")}
  };

  for (const ActionDefinition &actionDef : actionDefinitions) {
    QAction *action = createAction(actionDef.text, actionDef.statusTip,
                                   actionDef.function, actionDef.shortcut);
    action->setObjectName(actionDef.name);
    addAction(action);
  }
}

void RS_Workspace::addImage() {
  QFileDialog::Options options;
  options |= QFileDialog::ReadOnly;
  QString selectedFile = QFileDialog::getOpenFileName(
      this, "Open", directory, "Images (*.png *.jpg *.bmp);;All Files (*)",
      nullptr, options);

  if (!selectedFile.isEmpty()) {
    QString mimeType = QMimeDatabase().mimeTypeForFile(selectedFile).name();
    if (mimeType.isEmpty()) {
      mimeType = "image/png";
    }

    QFile file(selectedFile);
    if (file.open(QIODevice::ReadOnly)) {
      QByteArray data = file.readAll();
      QString encodedData = data.toBase64();
      QString imgTag = QString("<img src=\"data:%1;base64,%2\"/>")
                           .arg(mimeType, encodedData);
      documentArea->insertHtml(imgTag);
    }
  }
}

// void RS_Workspace::viewAbout() {
//     aboutWindow = new RS_About(this);
//     aboutWindow->show();
// }

// void RS_Workspace::viewHelp() {
//     RS_Help *helpWindow = new RS_Help(this);
//     helpWindow->show();
// }

void RS_Workspace::bulletList() {
  QTextCursor cursor = documentArea->textCursor();
  cursor.beginEditBlock();
  QString selectedText = cursor.selectedText();
  QTextCharFormat charFormat = cursor.charFormat();
  cursor.removeSelectedText();
  cursor.insertList(QTextListFormat::ListDisc);
  cursor.insertText(selectedText);
  QTextCursor newCursor = documentArea->textCursor();
  newCursor.movePosition(QTextCursor::PreviousBlock);
  newCursor.mergeCharFormat(charFormat);
  cursor.endEditBlock();
}

void RS_Workspace::numberedList() {
  QTextCursor cursor = documentArea->textCursor();
  cursor.beginEditBlock();
  QString selectedText = cursor.selectedText();
  QTextCharFormat charFormat = cursor.charFormat();
  cursor.removeSelectedText();
  cursor.insertList(QTextListFormat::ListDecimal);
  cursor.insertText(selectedText);
  QTextCursor newCursor = documentArea->textCursor();
  newCursor.movePosition(QTextCursor::PreviousBlock);
  newCursor.mergeCharFormat(charFormat);
  cursor.endEditBlock();
}

void RS_Workspace::contentAlign(Qt::Alignment alignment) {
  documentArea->setAlignment(alignment);
}

void RS_Workspace::contentBold() {
  QFont font = documentArea->currentFont();
  font.setBold(!font.bold());
  documentArea->setCurrentFont(font);
}

void RS_Workspace::contentItalic() {
  QFont font = documentArea->currentFont();
  font.setItalic(!font.italic());
  documentArea->setCurrentFont(font);
}

void RS_Workspace::contentUnderline() {
  QFont font = documentArea->currentFont();
  font.setUnderline(!font.underline());
  documentArea->setCurrentFont(font);
}

void RS_Workspace::contentColor() {
  QColor color = QColorDialog::getColor();
  if (color.isValid()) {
    documentArea->setTextColor(color);
  }
}

void RS_Workspace::contentBGColor() {
  QColor color = QColorDialog::getColor();
  if (color.isValid()) {
    documentArea->setTextBackgroundColor(color);
  }
}

void RS_Workspace::contentFont() {
  bool ok;
  QFont font = QFontDialog::getFont(&ok, documentArea->currentFont(), this);
  if (ok) {
    documentArea->setCurrentFont(font);
  }
}

void RS_Workspace::incFont() {
  QFont font = documentArea->currentFont();
  font.setPointSize(font.pointSize() + 1);
  documentArea->setCurrentFont(font);
}

void RS_Workspace::decFont() {
  QFont font = documentArea->currentFont();
  font.setPointSize(font.pointSize() - 1);
  documentArea->setCurrentFont(font);
}

void RS_Workspace::find() {
  QInputDialog *findDialog = new QInputDialog(this);
  findDialog->setInputMode(QInputDialog::TextInput);
  findDialog->setLabelText("Find");
  findDialog->setWindowTitle("Find");
  findDialog->setOkButtonText("Find");
  findDialog->setCancelButtonText("Cancel");
  connect(findDialog, &QInputDialog::textValueSelected, this,
          &RS_Workspace::findText);
  findDialog->show();
}

void RS_Workspace::findText(const QString &text) { documentArea->find(text); }

void RS_Workspace::replace() {
  QInputDialog *replaceDialog = new QInputDialog(this);
  replaceDialog->setInputMode(QInputDialog::TextInput);
  replaceDialog->setLabelText("Replace");
  replaceDialog->setWindowTitle("Replace");
  replaceDialog->setOkButtonText("Replace");
  replaceDialog->setCancelButtonText("Cancel");
  connect(replaceDialog, &QInputDialog::textValueSelected, this,
          &RS_Workspace::replaceText);
  replaceDialog->show();
}

void RS_Workspace::replaceText(const QString &text) {
  QTextCursor cursor = documentArea->textCursor();
  cursor.removeSelectedText();
  cursor.insertText(text);
}

void RS_Workspace::initToolbar() {
  file_toolbar = addToolBar("File");
  toolbarLabel(file_toolbar, "File: ");
  file_toolbar->addActions(
      {createAction(
           "New", "Create a new file", [this]() { newFile(); },
           QKeySequence::New),
       createAction(
           "Open", "Open an existing file", [this]() { openFile(); },
           QKeySequence::Open),
       createAction(
           "Save", "Save the current file", [this]() { saveFile(); },
           QKeySequence::Save),
       createAction(
           "Save As", "Save the file with a new name", [this]() { saveAs(); },
           QKeySequence::SaveAs),
       createAction(
           "Print", "Print the document", [this]() { printDocument(); },
           QKeySequence::Print),
       createAction(
           "Undo", "Undo the last action", [this]() { /* Undo logic */ },
           QKeySequence::Undo),
       createAction(
           "Redo", "Redo the last undone action", [this]() { /* Redo logic */ },
           QKeySequence::Redo),
       createAction(
           "Find", "Find text in the document", [this]() { find(); },
           QKeySequence::Find),
       createAction(
           "Replace", "Replace text in the document", [this]() { replace(); },
           QKeySequence::Replace)});

  ui_toolbar = addToolBar("UI");
  toolbarLabel(ui_toolbar, "UI: ");
  theme_action = createAction(
      "Dark/Light Mode", "Toggle Dark/Light theme", [this]() { themeAction(); },
      QKeySequence("Ctrl+Shift+T"));
  theme_action->setCheckable(true);
  // theme_action->setChecked();
  ui_toolbar->addAction(theme_action);

  powersaveraction = new QAction("Power Saver", this);
  powersaveraction->setStatusTip("Enable or disable power saver mode");
  powersaveraction->setCheckable(true);
  // powersaveraction->setChecked();
  connect(powersaveraction, &QAction::toggled, this,
          &RS_Workspace::hybridSaver);
  ui_toolbar->addAction(powersaveraction);

  hide_ai_dock = createAction(
      "AI", "Show or hide the AI dock", [this]() { toggleDock(); },
      QKeySequence("Ctrl+Shift+D"));
  ui_toolbar->addAction(hide_ai_dock);

  // ui_toolbar->addAction(
  // createAction("Help", "View help", [this]() { viewHelp(); },
  // QKeySequence("Ctrl+H")));
  // ui_toolbar->addAction(
  // createAction("About", "View about", [this]() { viewAbout(); },
  // QKeySequence("Ctrl+Shift+I")));

  language_combobox = new QComboBox(this);
  for (const auto &language : languages) {
    // language_combobox->addItem(language.second, language.first);
  }
  // language_combobox->currentIndexChanged(this,
  // &RS_Workspace::changeLanguage);
  ui_toolbar->addWidget(language_combobox);

  addToolBarBreak();

  edit_toolbar = addToolBar("Edit");
  toolbarLabel(edit_toolbar, "Edit: ");
  edit_toolbar->addActions({createAction(
                                "Align Left", "Align text to the left",
                                [this]() { contentAlign(Qt::AlignLeft); },
                                QKeySequence(Qt::CTRL + Qt::Key_L)),
                            createAction(
                                "Align Center", "Align text to the center",
                                [this]() { contentAlign(Qt::AlignCenter); },
                                QKeySequence(Qt::CTRL + Qt::Key_C)),
                            createAction(
                                "Align Right", "Align text to the right",
                                [this]() { contentAlign(Qt::AlignRight); },
                                QKeySequence(Qt::CTRL + Qt::Key_R)),
                            createAction(
                                "Justify", "Justify text",
                                [this]() { contentAlign(Qt::AlignJustify); },
                                QKeySequence(Qt::CTRL + Qt::Key_J))});

  addToolBarBreak();

  font_toolbar = addToolBar("Font");
  toolbarLabel(font_toolbar, "Font: ");
  font_toolbar->addActions(
      {createAction(
           "Bold", "Make text bold", [this]() { contentBold(); },
           QKeySequence(Qt::CTRL + Qt::Key_B)),
       createAction(
           "Italic", "Make text italic", [this]() { contentItalic(); },
           QKeySequence(Qt::CTRL + Qt::Key_I)),
       createAction(
           "Underline", "Underline text", [this]() { contentUnderline(); },
           QKeySequence(Qt::CTRL + Qt::Key_U))});

  addToolBarBreak();

  list_toolbar = addToolBar("List");
  toolbarLabel(list_toolbar, "List: ");
  list_toolbar->addActions(
      {createAction(
           "Bullet List", "Insert a bullet list", [this]() { bulletList(); },
           QKeySequence(Qt::CTRL + Qt::Key_B)),
       createAction(
           "Numbered List", "Insert a numbered list",
           [this]() { numberedList(); }, QKeySequence(Qt::CTRL + Qt::Key_B))});

  addToolBarBreak();

  color_toolbar = addToolBar("Color");
  toolbarLabel(color_toolbar, "Color: ");
  color_toolbar->addActions(
      {createAction(
           "Font Color", "Change font color", [this]() { contentColor(); },
           QKeySequence(Qt::CTRL + Qt::Key_B)),
       createAction(
           "Background Color", "Change background color",
           [this]() { contentBGColor(); }, QKeySequence(Qt::CTRL + Qt::Key_B)),
       createAction(
           "Font Family", "Change font family", [this]() { contentFont(); },
           QKeySequence(Qt::CTRL + Qt::Key_F)),
       createAction(
           "A+", "Increase font size", [this]() { incFont(); },
           QKeySequence(Qt::CTRL + Qt::Key_J)),
       createAction(
           "A-", "Decrease font size", [this]() { decFont(); },
           QKeySequence(Qt::CTRL + Qt::Key_Minus))});

  multimedia_toolbar = addToolBar("Multimedia");
  toolbarLabel(multimedia_toolbar, "Multimedia: ");
  multimedia_toolbar->addActions({createAction(
      "Add Image", "Add an image", [this]() { addImage(); },
      QKeySequence(Qt::CTRL + Qt::Key_X))});
}

void RS_Workspace::toggleDock() {
  if (ai_widget.isHidden()) {
    ai_widget.show();
  } else {
    ai_widget.hide();
  }
}

void RS_Workspace::hybridSaver(bool checked) {
  QSettings settings("berkaygediz", "SolidWriting");
  FallbackValues fallback;

  if (checked) {
    // psutil::sensors_battery battery = psutil::sensors_battery();
    // if (battery.percent <= 35 && !battery.power_plugged) {
    //     adaptiveResponse = 12; // Ultra power saver
    // } else {
    //     adaptiveResponse = 6; // Standard power saver
    // }
  } else {
    adaptiveResponse = fallback.adaptiveResponse;
  }

  settings.setValue("adaptiveResponse", adaptiveResponse);
  settings.sync();
}

QString RS_Workspace::detectEncoding(const QString &file_path) {
  QFile file(file_path);
  if (!file.open(QIODevice::ReadOnly)) {
    return "utf-8";
  }

  QByteArray byteArray = file.readAll();
  QTextStream stream(&file);
  QString text;

  stream.autoDetectUnicode();
  text = stream.readAll();
  if (!text.isEmpty()) {
    return "UTF-8";
  }

  stream.autoDetectUnicode();
  text = stream.readAll();
  if (!text.isEmpty()) {
    return "ISO-8859-1";
  }

  return "UTF-8";
}

void RS_Workspace::newFile() {
  if (isSaved) {
    documentArea->clear();
    initArea();
    fileName.clear();
    directory = defaultDirectory;
    isSaved = false;
    updateTitle();
  } else {
    QMessageBox::StandardButton reply = QMessageBox::question(
        this, qApp->applicationDisplayName(), "New",
        QMessageBox::Yes | QMessageBox::No, QMessageBox::No);

    if (reply == QMessageBox::Yes) {
      documentArea->clear();
      initArea();
      fileName.clear();
      directory = defaultDirectory;
      isSaved = false;
      updateTitle();
    }
  }
}

void RS_Workspace::setDocumentDefaultStyle() { initArea(); }

void RS_Workspace::openFile() {
  // QFileDialog::Options options;
  // options |= QFileDialog::ReadOnly;

  // QString selected_file = file_to_open.isEmpty()
  //                             ? QFileDialog::getOpenFileName(this,
  //                                                            "Open — "
  //                                                                +
  //                                                                qApp->applicationDisplayName(),
  //                                                            directory,
  //                                                            fallback.readFilter,
  //                                                            options)
  //                             : file_to_open;

  // if (!selected_file.isEmpty()) {
  //     fileName = selected_file;
  //     QString encoding = detectEncoding(fileName);

  //     QFile file((fileName));
  //     if (file.open(QIODevice::ReadOnly | QIODevice::Text)) {
  //         QTextStream in(&file);
  //         // in.setCodec(encoding.toUtf8());

  //         if (fileName.endsWith(".docx")) {
  //             // Load DOCX file using a third-party library
  //         } else {
  //             if (fileName.endsWith(".rsdoc") || fileName.endsWith(".html")
  //                 || fileName.endsWith(".htm")) {
  //                 documentArea->setHtml(in.readAll());
  //             } else if (fileName.endsWith(".md")) {
  //                 documentArea->setMarkdown(in.readAll());
  //             } else {
  //                 documentArea->setPlainText(in.readAll());
  //             }
  //         }
  //     }
  //     directory = QFileInfo(fileName).absolutePath();
  //     isSaved = true;
  //     updateTitle();
  // }
}

void RS_Workspace::saveFile() {
  if (!isSaved) {
    saveProcess();
  } else if (fileName.isEmpty()) {
    saveAs();
  } else {
    saveProcess();
  }
}

bool RS_Workspace::saveAs() {
  // QFileDialog::Options options;
  // options |= QFileDialog::ReadOnly;

  // QString selected_file = QFileDialog::getSaveFileName(this,
  //                                                      "Save As — "
  //                                                          +
  //                                                          qApp->applicationDisplayName(),
  //                                                      directory,
  //                                                      fallback.writeFilter,
  //                                                      options);

  // if (!selected_file.isEmpty()) {
  //     fileName = selected_file;
  //     directory = QFileInfo(fileName).absolutePath();
  //     saveProcess();
  //     return true;
  // }
  return false;
}
void RS_Workspace::saveProcess() {
  if (fileName.isEmpty()) {
    saveAs();
  } else {
    QFile file((fileName));
    if (file.open(QIODevice::WriteOnly | QIODevice::Text)) {
      QTextStream out(&file);
      // out.setCodec("UTF-8");

      if (fileName.endsWith(".rsdoc") || fileName.endsWith(".html") ||
          fileName.endsWith(".htm")) {
        out << documentArea->toHtml();
      } else if (fileName.endsWith(".md")) {
        out << documentArea->toMarkdown();
      } else {
        out << documentArea->toPlainText();
      }
    }

    statusBar()->showMessage("Saved.", 2000);
    isSaved = true;
    updateTitle();
  }
}
void RS_Workspace::printDocument() {
  // QPrinter printer;
  // printer.setResolution(QPrinter::HighResolution);
  // printer.setPageOrientation(QPageLayout::Portrait);
  // printer.setPageMargins(QMargins(10, 10, 10, 10), QPageLayout::Millimeter);
  // printer.setFullPage(true);
  // printer.setDocName(fileName);

  // QPrintPreviewDialog preview_dialog(&printer, this);
  // connect(&preview_dialog, &QPrintPreviewDialog::paintRequested,
  // documentArea, &QTextEdit::print); preview_dialog.exec();
}
