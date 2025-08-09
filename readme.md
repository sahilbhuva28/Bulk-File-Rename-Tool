# File Renamer — Modern Cross-Platform GUI Tool

A modern, cross-platform **GUI tool** for browsing, previewing, and batch-renaming files with undo support.  
Built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for a sleek, dark-themed interface.

---

## ✨ Features

- **Folder Browser** – Quickly choose and load files from any directory.
- **File Filtering** – View all files or limit to images, documents, or videos.
- **Sortable File List** – Sort by name, date modified, size, or type (ascending/descending).
- **Preview Panel** –  
  - Images: Thumbnail preview  
  - Text files: Inline text preview  
  - Other formats: Detailed file info  
- **Batch Rename** – Rename multiple files at once with custom base names and numbering.
- **Undo Last Rename** – Revert your last rename operation (even after restarting).
- **Context Menu** – Open files, show location, select/deselect, refresh.
- **Cross-Platform Support** – Works on Windows, macOS, and Linux.

---

## 🛠 Installation

### 1️⃣ Clone the repository:
```bash
git clone https://github.com/sahilbhuva28/file-renamer.git
cd file-renamer
````

### 2️⃣ Install dependencies:

```bash
pip install customtkinter pillow
```

### 3️⃣ Run the application:

```bash
python main.py
```

---

## 💡 Usage

1. Launch the app.
2. Click 📁 **Choose Folder** to select a directory.
3. Use the filter dropdown to narrow file types.
4. Select files from the list (or use **Select All**).
5. Enter a base name and start number.
6. Preview changes in the **Preview New Names** section.
7. Click 🔄 **Rename Selected Files** to apply changes.
8. Use ↶ **Undo** if needed.

---

## 🔙 Undo History

* Undo history is stored in:

```bash
~/.file_renamer_history.json
```

* Only the last 10 operations are saved.
* Undo works only if the folder is the same as when the rename was performed.

---

## 📦 Dependencies

* Python 3.8+
* `customtkinter` – Modern Tkinter UI
* `pillow` – Image preview support

---

## 🖥 Compatibility

| OS      | Supported? |
| ------- | ---------- |
| Windows | ✅          |
| macOS   | ✅          |
| Linux   | ✅          |

---

## 📜 License

MIT License

```text
Copyright (c) 2025 Sahil Bhuva

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙌 Credits

* **Author:** Sahil Bhuva
* **UI Framework:** CustomTkinter
* **Image Handling:** Pillow


