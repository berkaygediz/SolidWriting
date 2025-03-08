# SolidWriting

<p align="center">
    <img src="images/banner/solidwriting_banner_1.png" alt="SolidWriting Banner" />
</p>

<p align="center">
    <a href="https://github.com/berkaygediz/solidwriting/releases/latest">
        <img src="https://img.shields.io/github/v/release/berkaygediz/solidwriting" alt="GitHub release" />
    </a>
    <a href="https://github.com/berkaygediz/solidwriting">
        <img src="https://img.shields.io/github/repo-size/berkaygediz/solidwriting" alt="GitHub repo size" />
    </a>
    <a href="https://github.com/berkaygediz/solidwriting">
        <img src="https://img.shields.io/github/license/berkaygediz/solidwriting" alt="GitHub license" />
    </a>
</p>

SolidWriting is a supercharged, modern word processor designed as a powerful alternative to traditional software. Built with Python and PySide6, it delivers a lightweight yet feature-rich experience while ensuring seamless cross-platform compatibility on Windows, macOS, and Linux. With its offline AI chat for content generation and intelligent assistance, SolidWriting enhances productivity while prioritizing privacy by processing all interactions locally on your device.

## Features

- [x] **Cross-Platform**: Fully compatible with Windows, macOS, and Linux.
- [x] **Document Management**: Create, open, save, and print documents effortlessly.
- [x] **Find & Replace**: Search and replace text within your document.
- [x] **Printing & Exporting**: Print documents or export them as PDFs.
- [x] **File Format Support**: Supports .txt, .html, .docx (partial), and .swdoc (SolidWriting).
- [x] **Text Formatting**: Customize text with bold, italic, underline, font selection, size adjustment, color, background color, and alignment options.
- [x] **Undo & Redo**: Easily reverse or reapply changes.
- [x] **Cut, Copy, Paste**: Standard clipboard functions for efficient editing.
- [x] **Lists & Tables**: Create numbered/bulleted lists and insert customizable tables.
- [x] **Hyperlinks**: Add and open hyperlinks to reference external resources.
- [x] **Image Support**: Embed images in documents with Base64 encoding.
- [x] **Performance & Power Saving**: Fast and lightweight, with threading support and hardware acceleration. Optimized for power efficiency with hybrid ultra and standard power saving modes.
- [x] **Document Statistics**: Provides key statistical information about the document.
- [x] **User Experience**: Drag and drop functionality, dark mode support, and alerts for unsaved changes.
- [x] **Customizable Toolbar**: Personalize the user interface toolbar to suit your workflow.
- [x] **Multilingual Support**: English, Deutsch, Español, Türkçe, Azərbaycanca, Uzbek, 中文 (Chinese), 한국어 (Korean), 日本語 (Japanese), العربية (Arabic), Русский (Russian), Français, Ελληνικά (Greek), Kinyarwanda (Rwandan), Hebrew (עברית).
- [x] **Offline AI Chat**: Built-in AI assistant (offline mode) for content generation & Q&A, with automatic language detection and a context menu for seamless interaction.

## Prerequisites

- Python 3.12+
- PySide6
- mammoth
- chardet
- psutil
- langdetect
- pyinstaller
- llama-cpp-python
- torch

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/berkaygediz/SolidWriting.git
   ```

2. Install requirements:

   ```bash
   pip install -r requirements.txt
   ```

3. Creating a executable file (Unsigned):

   ```bash
   pyinstaller --name="SolidWriting" --noconsole --onedir --windowed --optimize "2" --clean --noconfirm --icon=".\solidwriting_icon.ico" --add-data "./.venv/Lib/site-packages/llama_cpp/*:llama_cpp" --add-binary "./.venv/Lib/site-packages/llama_cpp/*:llama_cpp" ".\SolidWriting.py"
   ```

## Usage

Launch SolidWriting from the command line:

```bash
python SolidWriting.py
```

## Contributing

Contributions to the SolidWriting project are welcomed. Please refer to [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute and our code of conduct.

## License

This project is licensed under GNU GPLv3, GNU LGPLv3, and Mozilla Public License Version 2.0.
