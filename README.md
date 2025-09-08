# Mini Crossword Puzzle Generator

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Gemini API](https://img.shields.io/badge/Google-Gemini%20API-orange)](https://ai.google/)

A daily crossword puzzle generator built with **Python**, powered by the **Google Gemini API** for generating themed words and clues.  
It includes a **Tkinter-based GUI** to play puzzles interactively and uses **SQLite** to ensure puzzle uniqueness by avoiding recently used words.

---

<img width="1033" height="641" alt="image" src="https://github.com/user-attachments/assets/d4e93c54-b4a3-456d-92e5-3732b3af25c5" />

## Overview

This project automatically generates a new crossword puzzle every day.  
It ensures that words used in recent puzzles (within the last **14 days**) are not reused.  
Players can solve puzzles using a simple and interactive graphical interface.

### Key Features

- AI-powered **word** and **clue** generation using the Google Gemini API.
- Ensures unique daily puzzles by avoiding words used in the past two weeks.
- Interactive GUI built with Tkinter for solving puzzles, checking answers, and requesting hints.
- SQLite database for storing puzzles and tracking used words.

---

## Requirements

- **Python 3.8+**
- Libraries:
  - [`google-generativeai`](https://pypi.org/project/google-generativeai/) — for Gemini API access
  - [`python-dotenv`](https://pypi.org/project/python-dotenv/) — for loading environment variables
  - `tkinter` *(built-in, but may require installation on some systems)*  
    ```bash
    sudo apt-get install python3-tk  # For Ubuntu/Debian
    ```
  - `sqlite3` *(built-in)*
- A **Google Gemini API key** → [Get one here](https://makersuite.google.com/)

> **Note:** No other external dependencies are required; standard libraries like `json`, `random`, and `os` are already included.

For creating a standalone executable, you will also need **PyInstaller** (optional).

---

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd mini_crossword
```

Install the required dependencies:

```bash
pip install google-generativeai python-dotenv
```

Set up your **Gemini API key**:

```bash
# Create a .env file in the root directory and add:
GEMINI_API_KEY=your_api_key_here
```

---

## Usage

Run the main script to generate and play the daily puzzle:

```bash
python crossword.py
```

---

## Building a Standalone Executable

You can build a standalone executable using **PyInstaller** to run the app without Python installed.

### Install PyInstaller

```bash
pip install pyinstaller
```

### Build Command

```bash
pyinstaller --onefile --noconsole crossword.py
```

This generates the following structure:

```
build/            # Temporary build files
dist/             # Contains the final executable
crossword.spec    # Spec file for future builds
```

The executable will be located in the `dist/` directory:

- **Windows:** `dist\crossword.exe`
- **Linux/Mac:** `dist/crossword`

### Running the Executable

**Windows:**  
Double-click `dist\crossword.exe` or run it via command prompt:

```bash
dist\crossword.exe
```

**Linux/Mac:**  
Make it executable and run it:

```bash
chmod +x dist/crossword
./dist/crossword
```

### Important Notes

- The executable **requires** the `.env` file containing your `GEMINI_API_KEY` in the same directory.
- The SQLite database (`crossword.db`) will be created/used in the directory where the executable is run.
- Build on the **target platform** for compatibility (e.g., build on Windows for `.exe`).
- Avoid embedding the API key directly into the executable for security reasons.

---

## How to Play

When you run the app, a **Tkinter window** will open containing:

- Crossword grid
- Across and Down clues
- Buttons: **Hint**, **Check**, **Quit**

### Controls

- Type letters directly into the grid cells.
- Click **Hint** to reveal a random blank cell.
- Click **Check** to verify if your solution is correct.
- Puzzles are automatically saved in `crossword.db`.

---

## How It Works

### Puzzle Generation

- Selects random themes for **across** and **down** words.
- Uses **Gemini** to fetch themed words and clues.
- Places words into the grid with valid intersections.
- Ensures puzzle connectivity using graph theory.

### Database

- Stores used words along with timestamps.
- Prevents reuse of words within 14 days.
- Caches puzzles for quick loading.

### GUI

- Displays the crossword grid with numbered starts.
- Shows across/down clues with word lengths.
- Supports hints, solution checking, and interactive cell inputs.

---

## Contributing

Contributions are welcome. You can:

- Add new themes
- Improve puzzle generation
- Enhance the GUI
- Fix bugs

To contribute:

1. Fork the repository.
2. Create a new branch:  
   ```bash
   git checkout -b feature/new-feature
   ```
3. Commit your changes:  
   ```bash
   git commit -m "Add new feature"
   ```
4. Push your branch:  
   ```bash
   git push origin feature/new-feature
   ```
5. Open a **Pull Request**.

---

## License

This project is licensed under the **MIT License**.  
See the [LICENSE](./LICENSE) file for details.

---

## Roadmap

- [ ] Add multi-language support
- [ ] Implement difficulty levels
- [ ] Add export-to-PDF feature
- [ ] Improve theme customization

---

## Powered By

- [Google Gemini API](https://ai.google/)
- [Tkinter](https://docs.python.org/3/library/tkinter.html)
- [SQLite](https://www.sqlite.org/)

---

**Enjoy solving your daily crossword puzzles!**
