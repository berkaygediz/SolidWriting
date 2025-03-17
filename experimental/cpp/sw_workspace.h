#ifndef RS_WORKSPACE_H
#define RS_WORKSPACE_H

#include <QAction>
#include <QApplication>
#include <QCloseEvent>
#include <QColor>
#include <QColorDialog>
#include <QComboBox>
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
#include <QPalette>
#include <QPushButton>
#include <QRegularExpression>
#include <QScrollArea>
#include <QSettings>
#include <QStatusBar>
#include <QString>
#include <QTextCursor>
#include <QTextDocument>
#include <QTextEdit>
#include <QTextListFormat>
#include <QThread>
#include <QTimer>
#include <QToolBar>
#include <QVBoxLayout>
#include <QWidget>

QT_BEGIN_NAMESPACE
namespace Ui {
class RS_Workspace;
}
QT_END_NAMESPACE

class RS_Workspace : public QMainWindow {
  Q_OBJECT

public:
  RS_Workspace(QWidget *parent = nullptr);
  ~RS_Workspace();

private:
  QComboBox *language_combobox;
  QAction *hide_ai_dock;
  int adaptiveResponse;
  QLabel *statistics_label;
  QTextEdit *input_text;
  QPushButton *predict_button;
  QScrollArea *scrollableArea;
  QVBoxLayout *messages_layout;
  QSettings settings;
  Ui::RS_Workspace *ui;
  QTextEdit *documentArea;
  bool isSaved;
  QString selectedFile;
  QString fileName;
  QString defaultDirectory;
  QString directory;
  QObject *llm;
  QPalette lightTheme;
  QPalette darkTheme;

  QAction *newaction, *openaction, *saveaction, *saveasaction, *printaction;
  QAction *undoaction, *redoaction, *theme_action, *powersaveraction,
      *findaction;
  QAction *replaceaction, *helpAction, *aboutAction;
  QAction *alignrightevent, *aligncenterevent, *alignleftevent,
      *alignjustifiedevent;
  QAction *bold, *italic, *underline, *bulletevent, *numberedevent, *color;
  QAction *backgroundcolor, *fontfamily, *addimage;
  QToolBar *file_toolbar, *ui_toolbar, *edit_toolbar, *font_toolbar,
      *list_toolbar;
  QToolBar *color_toolbar, *multimedia_toolbar;
  QWidget ai_widget;

private slots:
  void newFile();
  void openFile();
  void saveFile();
  bool saveAs();
  void saveProcess();
  void printDocument();
  void readSettings();
  void initUI();
  void closeEvent(QCloseEvent *event);
  void themeAction();
  void toolbarTheme();
  void toolbarTranslate();
  void updateStatistics();
  void themePalette();
  void translateToolbarLabel(QToolBar *toolbar, const QString &labelKey,
                             const QString &lang);
  void updateToolbarLabel(QToolBar *toolbar, const QString &newLabel);
  void LLMwarningCPU();
  void LLMinitDock();
  void LLMpredict();
  void LLMmessage(const QString &text, bool is_user);
  void changeLanguage();
  void updateTitle();
  // void threadStart();
  // void textChanged();
  // void saveState();
  // void restoreState();
  // void restoreTheme();
  // void translateToolbarLabel();
  // void updateToolbarLabel();
  void initArea();
  // void loadLLM();
  // void _load_model();
  // int acceleratorHardware();
  void LLMcontextPredict(bool action_type);
  void LLMprompt(const QString &prompt);
  QString LLMresponse(const QString &prompt);
  QString LLMconvertMarkdownHTML(const QString &markdown_text);
  QString convertBoldItalic(const QString &text);
  static QString LLMescapeHTML(const QString &text);
  void toolbarLabel(QToolBar *toolbar, const QString &text);
  QAction *createAction(const QString &text, const QString &statusTip,
                        std::function<void()> function,
                        const QKeySequence &shortcut);

  QString LLMconvertCodeHTML(const QString &text);
  void initActions();
  void initToolbar();
  void toggleDock();
  void hybridSaver(bool checked);
  void addImage();
  // void viewAbout();
  // void viewHelp();
  void bulletList();
  void numberedList();
  void contentAlign(Qt::Alignment alignment);
  void contentBold();
  void contentItalic();
  void contentUnderline();
  void contentColor();
  void contentBGColor();
  void contentFont();
  void incFont();
  void decFont();
  void find();
  void findText(const QString &text);
  void replace();
  void replaceText(const QString &text);
  QString detectEncoding(const QString &file_path);
  void setDocumentDefaultStyle();
};
#endif // RS_WORKSPACE_H
