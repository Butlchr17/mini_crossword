import os
import sys
import json
import random
import sqlite3
import collections
from datetime import date, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai
from tkinter import Tk, Frame, Label, Button, StringVar, Entry, CENTER, W
from tkinter.messagebox import showinfo, showwarning

load_dotenv()
if not os.getenv('GEMINI_API_KEY'):
    print("Missing GEMINI_API_KEY in .env")
    sys.exit(1)
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

DEBUG = True
def dprint(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

def get_theme_words(theme: str, num_words: int = 30, min_length: int = 3) -> List[str]:
    prompt = f"""
    Generate {num_words} unique words related to the theme '{theme}'.
    Each word should be at least {min_length} letters long, uppercase, A-Z only.
    Output ONLY a JSON list of strings, e.g., ["WORD1", "WORD2", ...]
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:].strip()
        if text.endswith("```"):
            text = text[:-3].strip()
        words = json.loads(text)
        words = [w.upper() for w in words if len(w) >= min_length and w.isalpha()]
        if words:
            return words
    except:
        dprint(f"Gemini failed to fetch words for theme '{theme}' — using fallback.")

    fallback = [
        "APPLE","TIGER","LASER","ROBOT","PYTHON","EARTH","CLOUD","ZEBRA","HONEY","SOLAR",
        "RIVER","PLANE","MANGO","PIZZA","QUARK","NEURON","MUSIC","CHAIR","BRICK","OCEAN",
        "SPORT","CYCLE","SMILE","STORM","EAGLE","BRAIN","LIGHT","CODE","SPACE","PARTY"
    ]
    return random.sample(fallback, min(num_words, len(fallback)))

def get_clues(words: List[str], theme: str) -> Dict[str, str]:
    prompt = f"""
    Generate crossword-style clues for each of the following words, related to the theme '{theme}'.
    Words: {', '.join(words)}
    Each clue should be concise, like in a real crossword.
    Output ONLY a JSON object: {{"WORD1": "clue1", "WORD2": "clue2", ...}}
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:].strip()
        if text.endswith("```"):
            text = text[:-3].strip()
        clues = json.loads(text)
        return {k.upper(): v for k, v in clues.items()}
    except Exception as e:
        dprint(f"Failed to get clues: {e}")
        return {w: f"Related to {theme}" for w in words}

def place_word(grid: Dict[tuple, str], word: str, r: int, c: int, direction: str) -> None:
    for i, letter in enumerate(word):
        rr = r + i if direction == "down" else r
        cc = c + i if direction == "across" else c
        grid[(rr, cc)] = letter

def find_intersection_positions(grid, word, direction, placed_words):
    positions = []
    min_r = min((k[0] for k in grid), default=0)
    max_r = max((k[0] for k in grid), default=0)
    min_c = min((k[1] for k in grid), default=0)
    max_c = max((k[1] for k in grid), default=0)
    buffer = len(word) + 2

    for start_r in range(min_r - buffer, max_r + buffer + 1):
        for start_c in range(min_c - buffer, max_c + buffer + 1):
            intersects = 0
            can_place = True
            occupied_positions = []

            for i, letter in enumerate(word):
                rr = start_r + i if direction == "down" else start_r
                cc = start_c + i if direction == "across" else start_c
                occupied_positions.append((rr, cc))

                # Check conflicts with existing grid
                if (rr, cc) in grid and grid[(rr, cc)] != letter:
                    can_place = False
                    break

                # Check same-direction adjacency violations in the same line
                for pw in placed_words:
                    if pw["direction"] != direction:
                        continue
                    pw_r, pw_c = pw["start_row"], pw["start_col"]
                    pw_len = len(pw["word"])
                    pw_end_r = pw_r + (pw_len - 1 if pw["direction"] == "down" else 0)
                    pw_end_c = pw_c + (pw_len - 1 if pw["direction"] == "across" else 0)

                    if direction == "across" and pw_r == rr:
                        if not (cc + 1 < pw_c or cc - 1 > pw_end_c):
                            can_place = False
                            break
                    if direction == "down" and pw_c == cc:
                        if not (rr + 1 < pw_r or rr - 1 > pw_end_r):
                            can_place = False
                            break
                if not can_place:
                    break

                # Count intersections
                if (rr, cc) in grid and grid[(rr, cc)] == letter:
                    intersects += 1

            if not can_place:
                continue

            # Additional check for parallel same-direction words
            for pw in placed_words:
                if pw["direction"] != direction:
                    continue
                pw_r, pw_c = pw["start_row"], pw["start_col"]
                pw_len = len(pw["word"])
                if direction == "across":
                    if abs(start_r - pw_r) != 1:
                        continue
                    new_start_c = start_c
                    new_end_c = start_c + len(word) - 1
                    pw_start_c = pw_c
                    pw_end_c = pw_c + pw_len - 1
                    overlap_start = max(new_start_c, pw_start_c)
                    overlap_end = min(new_end_c, pw_end_c)
                    overlap_len = max(0, overlap_end - overlap_start + 1)
                    if overlap_len > 1:
                        can_place = False
                        break
                else:  # down
                    if abs(start_c - pw_c) != 1:
                        continue
                    new_start_r = start_r
                    new_end_r = start_r + len(word) - 1
                    pw_start_r = pw_r
                    pw_end_r = pw_r + pw_len - 1
                    overlap_start = max(new_start_r, pw_start_r)
                    overlap_end = min(new_end_r, pw_end_r)
                    overlap_len = max(0, overlap_end - overlap_start + 1)
                    if overlap_len > 1:
                        can_place = False
                        break
            if not can_place or intersects != 1:
                continue

            # Check start and end buffers (avoid encapsulation)
            start_before_r = start_r - 1 if direction == "down" else start_r
            start_before_c = start_c - 1 if direction == "across" else start_c
            end_after_r = start_r + (len(word) if direction == "down" else 0)
            end_after_c = start_c + (len(word) if direction == "across" else 0)

            if (start_before_r, start_before_c) in grid:
                continue
            if (end_after_r, end_after_c) in grid:
                continue

            positions.append((start_r, start_c))

    return positions

def normalize_grid(grid):
    min_r = min(k[0] for k in grid)
    max_r = max(k[0] for k in grid)
    min_c = min(k[1] for k in grid)
    max_c = max(k[1] for k in grid)
    rows = max_r - min_r + 1
    cols = max_c - min_c + 1
    new_grid = [["." for _ in range(cols)] for _ in range(rows)]
    for (r, c), letter in grid.items():
        new_grid[r - min_r][c - min_c] = letter
    return new_grid, min_r, min_c

def adjust_positions(words, row_offset, col_offset):
    for w in words:
        w["start_row"] -= row_offset
        w["start_col"] -= col_offset

def generate_puzzle(used_words: list[str], target_words=10) -> dict:
    # Choose themes: across & down
    themes = ["animals", "technology", "food", "sports", "movies", "science"]
    across_theme, down_theme = random.sample(themes, 2)
    across_candidates = list({w for w in get_theme_words(across_theme, 50) if w not in used_words})
    down_candidates = list({w for w in get_theme_words(down_theme, 50) if w not in used_words})

    if len(across_candidates) < 5 or len(down_candidates) < 5:
        return {}

    # Place seed word in center
    seed = random.choice(across_candidates)
    across_candidates.remove(seed)
    grid = {}
    placed_words = [{"word": seed, "start_row": 0, "start_col": 0, "direction": "across"}]
    place_word(grid, seed, 0, 0, "across")

    # Alternate across & down until we reach target
    while len(placed_words) < target_words:
        direction = "down" if len(placed_words) % 2 == 1 else "across"
        candidates = down_candidates if direction == "down" else across_candidates
        if not candidates:
            break
        new_word = random.choice(candidates)
        candidates.remove(new_word)
        positions = find_intersection_positions(grid, new_word, direction, placed_words)
        if positions:
            pos = random.choice(positions)
            place_word(grid, new_word, pos[0], pos[1], direction)
            placed_words.append({"word": new_word, "start_row": pos[0], "start_col": pos[1], "direction": direction})

    if len(placed_words) < target_words:
        return {}

    # Normalize grid + positions
    new_grid, min_r, min_c = normalize_grid(grid)
    adjust_positions(placed_words, min_r, min_c)

    # Generate clues using Gemini
    across_words = [w["word"] for w in placed_words if w["direction"] == "across"]
    down_words = [w["word"] for w in placed_words if w["direction"] == "down"]
    across_clues = get_clues(across_words, across_theme)
    down_clues = get_clues(down_words, down_theme)
    clues = {**across_clues, **down_clues}

    for w in placed_words:
        w["clue"] = clues.get(w["word"], f"Related to {across_theme if w['direction']=='across' else down_theme}")

    return {
        "grid_size": {"rows": len(new_grid), "cols": len(new_grid[0])},
        "words": placed_words,
        "grid": new_grid
    }

def is_connected(words):
    n = len(words)
    graph = [[] for _ in range(n)]
    pos = []
    for w in words:
        r, c, d = w["start_row"], w["start_col"], w["direction"]
        s = set()
        for i in range(len(w["word"])):
            rr = r + i if d == "down" else r
            cc = c + i if d == "across" else c
            s.add((rr, cc))
        pos.append(s)
    for i in range(n):
        for j in range(i + 1, n):
            overlap = pos[i] & pos[j]
            if overlap:
                if len(overlap) != 1:
                    return False
                if words[i]["direction"] == words[j]["direction"]:
                    return False
                graph[i].append(j)
                graph[j].append(i)
    visited = [False] * n
    q = collections.deque([0])
    visited[0] = True
    count = 1
    while q:
        u = q.popleft()
        for v in graph[u]:
            if not visited[v]:
                visited[v] = True
                q.append(v)
                count += 1
    return count == n

def validate_puzzle(puzzle):
    if not puzzle:
        return False
    try:
        rows, cols = puzzle['grid_size']['rows'], puzzle['grid_size']['cols']
        grid = puzzle['grid']
        words = puzzle['words']
    except:
        return False
    if not is_connected(words):
        dprint("Puzzle rejected: disconnected graph")
        return False
    return True

DB_PATH = "crossword.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS used_words (
            word TEXT UNIQUE,
            date_used DATE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS puzzles (
            date DATE UNIQUE,
            puzzle_json TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_used_words(words: list[str], current_date: date):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for word in words:
        cursor.execute(
            'INSERT OR REPLACE INTO used_words (word, date_used) VALUES (?, ?)',
            (word.upper(), current_date.isoformat())
        )
    conn.commit()
    conn.close()

def get_used_words() -> list[str]:
    today = date.today()
    cutoff = (today - timedelta(days=14)).isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT word FROM used_words WHERE date_used > ?', (cutoff,))
    used = [row[0] for row in cursor.fetchall()]
    conn.close()
    return used

def save_puzzle(current_date: date, puzzle: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR REPLACE INTO puzzles (date, puzzle_json) VALUES (?, ?)',
        (current_date.isoformat(), json.dumps(puzzle))
    )
    conn.commit()
    conn.close()

def load_puzzle(current_date: date) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT puzzle_json FROM puzzles WHERE date = ?', (current_date.isoformat(),))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row[0]) if row else {}

def get_daily_puzzle(retries=20):
    today = date.today()
    init_db()
    puzzle = load_puzzle(today)
    if puzzle and validate_puzzle(puzzle):
        return puzzle
    used_words = get_used_words()
    for attempt in range(retries):
        dprint(f"Attempt {attempt + 1}: generating puzzle...")
        puzzle = generate_puzzle(used_words)
        if validate_puzzle(puzzle):
            words = [w["word"].upper() for w in puzzle["words"]]
            add_used_words(words, today)
            save_puzzle(today, puzzle)
            return puzzle
        dprint("Invalid puzzle generated; retrying...")
    return {}

class CellEntry(Entry):
    def __init__(self, master, **kw):
        self.var = StringVar()
        self.var.trace('w', self.callback)
        super().__init__(master, textvariable=self.var, **kw)

    def callback(self, *args):
        val = self.var.get().upper()
        if len(val) > 1:
            self.var.set(val[-1])
        else:
            self.var.set(val)

def play_game(puzzle):
    grid = puzzle["grid"]
    words = puzzle["words"]
    rows = puzzle["grid_size"]["rows"]
    cols = puzzle["grid_size"]["cols"]

    # Assign numbers to starting positions
    start_pos_to_num = {}
    starts = set((w["start_row"], w["start_col"]) for w in words)
    sorted_starts = sorted(starts)
    for i, (r, c) in enumerate(sorted_starts, 1):
        start_pos_to_num[(r, c)] = i

    for w in words:
        w["number"] = start_pos_to_num[(w["start_row"], w["start_col"])]

    # Create GUI
    root = Tk()
    root.title(f"Daily Crossword - {rows}x{cols}")

    main_frame = Frame(root)
    main_frame.pack(padx=10, pady=10)

    grid_frame = Frame(main_frame)
    grid_frame.grid(row=0, column=0, padx=10)

    clues_frame = Frame(main_frame)
    clues_frame.grid(row=0, column=1, padx=10, sticky="n")

    buttons_frame = Frame(main_frame)
    buttons_frame.grid(row=1, column=0, columnspan=2, pady=10)

    user_vars = {}

    cell_size = 30

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == ".":
                black = Frame(grid_frame, width=cell_size, height=cell_size, bg="black", bd=1, relief="solid")
                black.grid(row=r, column=c)
            else:
                cell_frame = Frame(grid_frame, width=cell_size, height=cell_size, bd=1, relief="solid")
                cell_frame.grid(row=r, column=c)

                num_text = ""
                if (r, c) in start_pos_to_num:
                    num_text = str(start_pos_to_num[(r, c)])

                num_label = Label(cell_frame, text=num_text, font=("Arial", 8), anchor="nw")
                num_label.place(x=2, y=0)

                entry = CellEntry(cell_frame, width=3, justify=CENTER, font=("Arial", 12))
                entry.place(x=5, y=10)

                user_vars[(r, c)] = entry.var

    # Clues
    across_words = [w for w in words if w["direction"] == "across"]
    down_words = [w for w in words if w["direction"] == "down"]

    sorted_across = sorted(across_words, key=lambda w: w["number"])
    sorted_down = sorted(down_words, key=lambda w: w["number"])

    across_label = Label(clues_frame, text="Across", font=("Arial", 12, "bold"))
    across_label.grid(row=0, column=0, sticky=W)

    row_idx = 1
    for w in sorted_across:
        Label(clues_frame, text=f"{w['number']} {w['clue']} ({len(w['word'])})", anchor=W, wraplength=300).grid(row=row_idx, column=0, sticky=W)
        row_idx += 1

    down_label = Label(clues_frame, text="Down", font=("Arial", 12, "bold"))
    down_label.grid(row=0, column=1, sticky=W)

    row_idx = 1
    for w in sorted_down:
        Label(clues_frame, text=f"{w['number']} {w['clue']} ({len(w['word'])})", anchor=W, wraplength=300).grid(row=row_idx, column=1, sticky=W)
        row_idx += 1

    # Buttons
    def hint():
        blanks = [(rr, cc) for (rr, cc), v in user_vars.items() if not v.get()]
        if blanks:
            rr, cc = random.choice(blanks)
            user_vars[(rr, cc)].set(grid[rr][cc])

    def check():
        for (rr, cc), v in user_vars.items():
            if v.get() != grid[rr][cc]:
                showwarning("Incorrect", "Not correct yet.")
                return
        showinfo("Congratulations", "Puzzle solved!")

    def quit_game():
        root.destroy()

    Button(buttons_frame, text="Hint", command=hint).pack(side="left", padx=5)
    Button(buttons_frame, text="Check", command=check).pack(side="left", padx=5)
    Button(buttons_frame, text="Quit", command=quit_game).pack(side="left", padx=5)

    root.mainloop()

if __name__ == "__main__":
    puzzle = get_daily_puzzle()
    if puzzle:
        play_game(puzzle)
    else:
        print("Failed to generate puzzle.")