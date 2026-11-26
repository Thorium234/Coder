"""
vibe_coder.py - types whole projects (games, apps, tools) into VS Code at a slow,
human-like pace, with occasional typos it notices and fixes. When one project is
finished it closes the window and DELETES the temporary files, then makes a NEW
temporary folder, opens it in a new VS Code window and starts the next project.
It keeps going until you stop it. Nothing is kept on your PC unless you add --keep.

Every project it types is long (100 to 300 lines). Typing one takes roughly
30 to 60 minutes, so it can run for hours.

Setup:
  pip install pyautogui
  VS Code must have the `code` command on PATH
  (VS Code: Ctrl+Shift+P -> "Shell Command: Install 'code' command in PATH")

IMPORTANT - how to start it:
  Run this script from a normal terminal (PowerShell or Command Prompt) and do
  NOT have vibe_coder.py open in VS Code while it runs. The bot types into
  whatever window is focused, so a stray VS Code window with your script open
  would get the code typed into it. The bot now checks the window title before
  EVERY keystroke. If you click into another window, the bot PAUSES by itself and
  waits for you instead of fighting for the keyboard.

Run:
  python vibe_coder.py                      # built-in projects, loops forever
  python vibe_coder.py --online             # pull ideas from the internet too
  python vibe_coder.py --hours 3            # stop by itself after ~3 hours
  python vibe_coder.py --slowdown 1.5       # even slower (1.0 is the default)
  python vibe_coder.py --projects-dir ./my_snippets   # also type your own .py files
  python vibe_coder.py --keep               # keep finished projects (see --out)

Online mode:
  - Finds popular Python projects on GitHub to get an idea of what to build.
  - If the ANTHROPIC_API_KEY environment variable is set, Claude writes a brand
    new original program (300+ lines) inspired by that idea, and the bot types it.
  - If there is no key, it types a longer public file from the repo instead
    (with a source comment at the top; check the repo's licence if you share it).
  - If the internet fails, it quietly falls back to the built-in projects.

Pausing (so you can use your PC):
  Press Ctrl+Alt+P (or the Pause/Break key) to pause. Use your PC as much as you
  like. Press the same keys again to continue: the bot brings its VS Code window
  back to the front and carries on from the exact spot where it stopped.
  The bot cannot type in the background, because keystrokes always go to the
  window in front. While it is typing, leave that window alone.
  (The pause keys work on Windows. On Mac/Linux use Ctrl+C to stop.)

How to stop:
  Slam the mouse into any screen corner (pyautogui failsafe) or press Ctrl+C in
  the terminal.

Tip: VS Code auto-indents and auto-closes brackets/quotes, which can double
things up. Turn off "Editor: Auto Closing Brackets", "Auto Closing Quotes" and
"Auto Indent" in settings while you run this.

Tip: new project folders can trigger VS Code's "Do you trust the authors of the
files in this folder?" box. Tick "Trust the authors of all files in the parent
folder" once for your projects folder so it never pops up in the middle of typing.
"""

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

import pyautogui

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0  # we control all delays ourselves

# ---------------------------------------------------------------- settings --
COUNTDOWN_SECONDS = 10
TYPO_CHANCE = 0.035           # chance per character of a typo
THINK_PAUSE_CHANCE = 0.05     # chance of a longer "thinking" pause
BASE_DELAY = (0.20, 0.50)     # seconds between keystrokes (slow and human)
THINK_PAUSE = (1.5, 4.0)      # length of a "thinking" pause
LINE_PAUSE = (1.0, 2.6)       # pause after pressing Enter
INDENT_SIZE = 4               # spaces per indent level (match your VS Code setting)
WINDOW_WAIT = 12              # seconds to let a new VS Code window open
BETWEEN_PROJECTS = (8, 20)    # seconds of rest between projects
MIN_LINES = 100               # online code shorter than this is skipped

SLOW = 1.0                    # global slowdown multiplier (set by --slowdown)
MOD = "command" if sys.platform == "darwin" else "ctrl"
IS_WINDOWS = os.name == "nt"

# Rough keyboard neighbours for believable typos
NEIGHBOURS = {
    "a": "qwsz", "b": "vghn", "c": "xdfv", "d": "serfcx", "e": "wsdr",
    "f": "drtgvc", "g": "ftyhbv", "h": "gyujnb", "i": "ujko", "j": "huikmn",
    "k": "jiolm", "l": "kop", "m": "njk", "n": "bhjm", "o": "iklp",
    "p": "ol", "q": "wa", "r": "edft", "s": "awedxz", "t": "rfgy",
    "u": "yhji", "v": "cfgb", "w": "qase", "x": "zsdc", "y": "tghu",
    "z": "asx",
}

# ------------------------------------------------------ built-in projects ---
BUILTIN_PROJECTS = [
    {
        "name": "tetris",
        "filename": "tetris.py",
        "code": r'''
"""Tetris - a complete falling blocks game built with tkinter.

Left and Right move the piece, Up rotates it and Down drops it faster.
Space drops the piece all the way down, P pauses and R restarts.
Your best score is saved in a small text file next to the game.
Only the Python standard library is needed.
"""

import random
import tkinter as tk

COLS = 10
ROWS = 20
CELL = 28
SIDE = 170
START_DELAY = 650
MIN_DELAY = 100
SCORE_FILE = "tetris_best.txt"
LINE_POINTS = {0: 0, 1: 100, 2: 300, 3: 500, 4: 800}

SHAPES = {
    "I": [[1, 1, 1, 1]],
    "O": [[1, 1], [1, 1]],
    "T": [[0, 1, 0], [1, 1, 1]],
    "S": [[0, 1, 1], [1, 1, 0]],
    "Z": [[1, 1, 0], [0, 1, 1]],
    "J": [[1, 0, 0], [1, 1, 1]],
    "L": [[0, 0, 1], [1, 1, 1]],
}

COLORS = {
    "I": "#00d8e8",
    "O": "#f5d90a",
    "T": "#b455e0",
    "S": "#3ddc84",
    "Z": "#ff5252",
    "J": "#4a7bff",
    "L": "#ff9f1a",
}


def rotate(shape):
    """Rotate a shape matrix ninety degrees clockwise."""
    return [list(row) for row in zip(*shape[::-1])]


class Piece:
    """One falling tetromino with a position and a shape matrix."""

    def __init__(self, kind):
        self.kind = kind
        self.shape = [row[:] for row in SHAPES[kind]]
        self.x = COLS // 2 - len(self.shape[0]) // 2
        self.y = 0

    def cells(self, shape=None, x=None, y=None):
        """Yield the board coordinates of every filled square."""
        shape = self.shape if shape is None else shape
        x = self.x if x is None else x
        y = self.y if y is None else y
        for r, row in enumerate(shape):
            for c, filled in enumerate(row):
                if filled:
                    yield x + c, y + r


class Board:
    """The grid of locked squares at the bottom of the well."""

    def __init__(self):
        self.grid = [[None] * COLS for _ in range(ROWS)]

    def fits(self, cells):
        for x, y in cells:
            if x < 0 or x >= COLS or y >= ROWS:
                return False
            if y >= 0 and self.grid[y][x]:
                return False
        return True

    def lock(self, piece):
        for x, y in piece.cells():
            if 0 <= y < ROWS:
                self.grid[y][x] = piece.kind

    def clear_lines(self):
        keep = [row for row in self.grid if not all(row)]
        cleared = ROWS - len(keep)
        self.grid = [[None] * COLS for _ in range(cleared)] + keep
        return cleared


class TetrisGame:
    def __init__(self, root):
        self.root = root
        root.title("Tetris")
        root.resizable(False, False)
        width = COLS * CELL + SIDE
        height = ROWS * CELL
        self.canvas = tk.Canvas(root, width=width, height=height, bg="#14141f", highlightthickness=0)
        self.canvas.pack()
        self.job = None
        self.bag = []
        self.best = self.load_best()
        root.bind("<Key>", self.on_key)
        self.new_game()

    def load_best(self):
        try:
            with open(SCORE_FILE, "r", encoding="utf-8") as f:
                return int(f.read().strip())
        except (OSError, ValueError):
            return 0

    def save_best(self):
        try:
            with open(SCORE_FILE, "w", encoding="utf-8") as f:
                f.write(str(self.best))
        except OSError:
            pass

    def next_kind(self):
        """Seven piece bag so every shape shows up regularly."""
        if not self.bag:
            self.bag = list(SHAPES)
            random.shuffle(self.bag)
        return self.bag.pop()

    def new_game(self):
        self.board = Board()
        self.score = 0
        self.lines = 0
        self.level = 1
        self.paused = False
        self.over = False
        self.current = Piece(self.next_kind())
        self.upcoming = Piece(self.next_kind())
        self.draw()
        self.schedule_tick()

    def delay(self):
        return max(MIN_DELAY, START_DELAY - (self.level - 1) * 55)

    def schedule_tick(self):
        if self.job is not None:
            self.root.after_cancel(self.job)
        self.job = self.root.after(self.delay(), self.tick)

    def tick(self):
        self.job = None
        if self.over:
            return
        if not self.paused and not self.move(0, 1):
            self.settle()
        self.draw()
        if not self.over:
            self.schedule_tick()

    def move(self, dx, dy):
        cells = list(self.current.cells(x=self.current.x + dx, y=self.current.y + dy))
        if self.board.fits(cells):
            self.current.x += dx
            self.current.y += dy
            return True
        return False

    def rotate_current(self):
        turned = rotate(self.current.shape)
        for kick in (0, -1, 1, -2, 2):
            cells = list(self.current.cells(shape=turned, x=self.current.x + kick))
            if self.board.fits(cells):
                self.current.shape = turned
                self.current.x += kick
                return True
        return False

    def settle(self):
        """Lock the piece, clear full lines and bring in the next piece."""
        self.board.lock(self.current)
        cleared = self.board.clear_lines()
        if cleared:
            self.lines += cleared
            self.score += LINE_POINTS.get(cleared, 800) * self.level
            self.level = self.lines // 10 + 1
        self.current = self.upcoming
        self.upcoming = Piece(self.next_kind())
        if not self.board.fits(list(self.current.cells())):
            self.over = True
            if self.score > self.best:
                self.best = self.score
                self.save_best()

    def hard_drop(self):
        while self.move(0, 1):
            self.score += 2
        self.settle()

    def ghost_y(self):
        y = self.current.y
        while self.board.fits(list(self.current.cells(y=y + 1))):
            y += 1
        return y

    def on_key(self, event):
        key = event.keysym
        if key in ("r", "R"):
            self.new_game()
            return
        if self.over:
            return
        if key in ("p", "P"):
            self.paused = not self.paused
        elif self.paused:
            return
        elif key == "Left":
            self.move(-1, 0)
        elif key == "Right":
            self.move(1, 0)
        elif key == "Down":
            if self.move(0, 1):
                self.score += 1
        elif key == "Up":
            self.rotate_current()
        elif key == "space":
            self.hard_drop()
        self.draw()

    def draw_cell(self, gx, gy, color, ox=0, oy=0, ghost=False):
        x1 = ox + gx * CELL
        y1 = oy + gy * CELL
        x2 = x1 + CELL
        y2 = y1 + CELL
        if ghost:
            self.canvas.create_rectangle(x1 + 3, y1 + 3, x2 - 3, y2 - 3, outline=color, width=2)
        else:
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#14141f", width=2)

    def draw(self):
        c = self.canvas
        c.delete("all")
        for x in range(COLS + 1):
            c.create_line(x * CELL, 0, x * CELL, ROWS * CELL, fill="#1f1f2e")
        for y in range(ROWS + 1):
            c.create_line(0, y * CELL, COLS * CELL, y * CELL, fill="#1f1f2e")
        for y, row in enumerate(self.board.grid):
            for x, kind in enumerate(row):
                if kind:
                    self.draw_cell(x, y, COLORS[kind])
        if not self.over:
            ghost = self.ghost_y()
            for x, y in self.current.cells(y=ghost):
                self.draw_cell(x, y, COLORS[self.current.kind], ghost=True)
            for x, y in self.current.cells():
                self.draw_cell(x, y, COLORS[self.current.kind])
        self.draw_side_panel()
        if self.paused:
            self.banner("PAUSED")
        elif self.over:
            self.banner("GAME OVER - press R")

    def draw_side_panel(self):
        c = self.canvas
        left = COLS * CELL + 20
        c.create_text(left, 30, anchor="w", fill="white", font=("Arial", 16, "bold"), text="TETRIS")
        stats = [("Score", self.score), ("Level", self.level), ("Lines", self.lines), ("Best", self.best)]
        for i, (label, value) in enumerate(stats):
            c.create_text(left, 80 + i * 45, anchor="w", fill="#8888aa", font=("Arial", 10), text=label)
            c.create_text(left, 98 + i * 45, anchor="w", fill="white", font=("Arial", 14, "bold"), text=str(value))
        c.create_text(left, 290, anchor="w", fill="#8888aa", font=("Arial", 10), text="Next")
        for x, y in self.upcoming.cells(x=0, y=0):
            self.draw_cell(x, y, COLORS[self.upcoming.kind], ox=left, oy=305)

    def banner(self, text):
        mid_x = COLS * CELL // 2
        mid_y = ROWS * CELL // 2
        self.canvas.create_rectangle(mid_x - 130, mid_y - 30, mid_x + 130, mid_y + 30, fill="black", outline="white")
        self.canvas.create_text(mid_x, mid_y, fill="white", font=("Arial", 14, "bold"), text=text)


def main():
    root = tk.Tk()
    TetrisGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
''',
    },
    {
        "name": "dungeon_crawler_rpg",
        "filename": "dungeon_crawler.py",
        "code": r'''
"""Dungeon Crawler - a text adventure RPG for the terminal.

Explore a randomly generated dungeon, fight monsters, find treasure,
buy potions from the traveling merchant and defeat the boss on the last floor.
You can save your game to a JSON file and load it again later.
Only the Python standard library is needed.
"""

import json
import random

SAVE_FILE = "dungeon_save.json"
FLOORS = 3
ROOMS_PER_FLOOR = 6

# name, hit points, attack, gold reward, experience reward
MONSTER_TYPES = [
    ("Slime", 10, 3, 6, 8),
    ("Goblin", 15, 4, 10, 12),
    ("Skeleton", 20, 5, 14, 16),
    ("Wolf", 18, 6, 12, 15),
    ("Orc", 28, 7, 20, 24),
    ("Dark Mage", 22, 8, 25, 30),
]

ITEMS = {
    "potion": {"price": 15, "kind": "heal", "power": 25},
    "big potion": {"price": 35, "kind": "heal", "power": 60},
    "iron sword": {"price": 70, "kind": "weapon", "power": 3},
    "steel sword": {"price": 140, "kind": "weapon", "power": 6},
    "leather armor": {"price": 60, "kind": "armor", "power": 2},
    "plate armor": {"price": 130, "kind": "armor", "power": 4},
}

ROOM_KINDS = ["monster", "monster", "treasure", "trap", "merchant", "rest", "fountain", "empty"]


def read(prompt):
    """Read a line from the player and quit cleanly if input ends."""
    try:
        return input(prompt).strip().lower()
    except EOFError:
        raise SystemExit


def ask(prompt, valid):
    """Keep asking until the first letter of the answer is one of the valid letters."""
    while True:
        answer = read(prompt)
        if answer and answer[0] in valid:
            return answer[0]
        print("Please choose one of these letters: " + " ".join(valid))


def describe(info):
    if info["kind"] == "heal":
        return f"heals {info['power']} HP"
    if info["kind"] == "weapon":
        return f"+{info['power']} attack"
    return f"-{info['power']} damage taken"


class Character:
    def __init__(self, name, hp, attack):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.attack = attack

    def is_alive(self):
        return self.hp > 0

    def total_attack(self):
        return self.attack

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        return amount

    def roll_damage(self):
        base = self.total_attack()
        damage = random.randint(max(1, base - 2), base + 2)
        critical = random.random() < 0.15
        if critical:
            damage *= 2
        return damage, critical


class Monster(Character):
    def __init__(self, name, hp, attack, gold, xp):
        super().__init__(name, hp, attack)
        self.gold = gold
        self.xp = xp


class Player(Character):
    def __init__(self, name):
        super().__init__(name, 60, 8)
        self.gold = 20
        self.xp = 0
        self.level = 1
        self.inventory = {"potion": 3}
        self.weapon_power = 0
        self.armor_power = 0

    def total_attack(self):
        return self.attack + self.weapon_power

    def take_damage(self, amount):
        reduced = max(1, amount - self.armor_power)
        self.hp = max(0, self.hp - reduced)
        return reduced

    def xp_needed(self):
        return 20 + (self.level - 1) * 15

    def gain_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_needed():
            self.xp -= self.xp_needed()
            self.level += 1
            self.max_hp += 10
            self.attack += 1
            self.hp = self.max_hp
            print(f"*** You reached level {self.level}! Your HP is fully restored. ***")

    def heal(self, amount):
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    def add_item(self, name):
        info = ITEMS[name]
        if info["kind"] == "weapon":
            self.weapon_power = max(self.weapon_power, info["power"])
            print(f"You equip the {name}. Attack is now {self.total_attack()}.")
        elif info["kind"] == "armor":
            self.armor_power = max(self.armor_power, info["power"])
            print(f"You put on the {name}. Armor is now {self.armor_power}.")
        else:
            self.inventory[name] = self.inventory.get(name, 0) + 1

    def potions(self):
        return [name for name, count in self.inventory.items() if count > 0]

    def use_potion(self):
        options = self.potions()
        if not options:
            print("You have no potions.")
            return False
        for i, name in enumerate(options, 1):
            print(f"  {i}. {name} x{self.inventory[name]}")
        raw = read("Use which one? ")
        if not raw.isdigit() or not 1 <= int(raw) <= len(options):
            print("You fumble around in your bag and find nothing.")
            return False
        name = options[int(raw) - 1]
        self.inventory[name] -= 1
        gained = self.heal(ITEMS[name]["power"])
        print(f"You drink a {name} and recover {gained} HP.")
        return True


def make_monster(floor, boss=False):
    if boss:
        return Monster("Dragon Lord", 80 + floor * 5, 10, 200, 150)
    name, hp, attack, gold, xp = random.choice(MONSTER_TYPES)
    scale = 1 + 0.25 * (floor - 1)
    return Monster(name, int(hp * scale), int(attack * scale), int(gold * scale), int(xp * scale))


def fight(player, monster):
    """Turn based combat. Returns won, fled or dead."""
    print(f"\nA {monster.name} blocks your way! It has {monster.hp} HP.")
    while player.is_alive() and monster.is_alive():
        print(f"\n{player.name}: {player.hp}/{player.max_hp} HP    {monster.name}: {monster.hp} HP")
        choice = ask("[a]ttack, [p]otion or [r]un? ", "apr")
        if choice == "a":
            damage, critical = player.roll_damage()
            monster.take_damage(damage)
            note = " Critical hit!" if critical else ""
            print(f"You hit the {monster.name} for {damage} damage.{note}")
        elif choice == "p":
            if not player.use_potion():
                continue
        else:
            if random.random() < 0.5:
                print("You escape into the shadows.")
                return "fled"
            print("You try to run but the monster cuts you off!")
        if monster.is_alive():
            damage, critical = monster.roll_damage()
            taken = player.take_damage(damage)
            note = " Ouch, that was a critical hit!" if critical else ""
            print(f"The {monster.name} hits you for {taken} damage.{note}")
    if not player.is_alive():
        return "dead"
    print(f"\nYou defeated the {monster.name}! You find {monster.gold} gold and earn {monster.xp} XP.")
    player.gold += monster.gold
    player.gain_xp(monster.xp)
    return "won"


def shop(player):
    print("\nA traveling merchant opens his heavy pack and smiles.")
    names = list(ITEMS)
    while True:
        print(f"\nYou have {player.gold} gold.")
        for i, name in enumerate(names, 1):
            info = ITEMS[name]
            print(f"  {i}. {name:<14} {info['price']:>4} gold   ({describe(info)})")
        print("  0. Leave the shop")
        raw = read("Buy which item? ")
        if raw in ("", "0"):
            print("The merchant waves goodbye.")
            return
        if not raw.isdigit() or not 1 <= int(raw) <= len(names):
            print("The merchant looks confused.")
            continue
        name = names[int(raw) - 1]
        price = ITEMS[name]["price"]
        if player.gold < price:
            print("You cannot afford that.")
            continue
        player.gold -= price
        player.add_item(name)
        print(f"You bought a {name} for {price} gold.")


class Game:
    def __init__(self, player):
        self.player = player
        self.floor = 1
        self.room = 0
        self.layout = self.make_layout()

    def make_layout(self):
        rooms = [random.choice(ROOM_KINDS) for _ in range(ROOMS_PER_FLOOR - 1)]
        if self.floor == FLOORS:
            rooms[-1] = "rest"
            rooms.append("boss")
        else:
            rooms.append("stairs")
        return rooms

    def to_dict(self):
        return {"player": self.player.__dict__, "floor": self.floor, "room": self.room, "layout": self.layout}

    @classmethod
    def from_dict(cls, data):
        player = Player(data["player"]["name"])
        player.__dict__.update(data["player"])
        game = cls(player)
        game.floor = data["floor"]
        game.room = data["room"]
        game.layout = data["layout"]
        return game

    def save(self):
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        print("Game saved.")

    def show_status(self):
        p = self.player
        print("\n" + "=" * 52)
        print(f"{p.name}  level {p.level}  HP {p.hp}/{p.max_hp}  gold {p.gold}  XP {p.xp}/{p.xp_needed()}")
        print(f"Attack {p.total_attack()}  Armor {p.armor_power}  Floor {self.floor}/{FLOORS}  Room {self.room + 1}/{ROOMS_PER_FLOOR}")
        print("=" * 52)

    def show_inventory(self):
        items = self.player.potions()
        if not items:
            print("Your bag is empty.")
        for name in items:
            print(f"  {name} x{self.player.inventory[name]}")

    def enter_room(self):
        """Handle the next room. Returns alive, dead or won."""
        kind = self.layout[self.room]
        p = self.player
        print(f"\n--- Floor {self.floor}, room {self.room + 1}: {kind} room ---")
        if kind == "monster":
            if fight(p, make_monster(self.floor)) == "dead":
                return "dead"
        elif kind == "boss":
            print("The air turns hot. A huge shape unfolds in the darkness.")
            result = fight(p, make_monster(self.floor, boss=True))
            if result == "dead":
                return "dead"
            if result == "won":
                return "won"
            print("You cannot leave while the dragon lives. You are back at the door.")
            return "alive"
        elif kind == "treasure":
            self.find_treasure()
        elif kind == "trap":
            damage = random.randint(4, 10) + self.floor * 2
            taken = p.take_damage(damage)
            print(f"Click! A trap springs and you lose {taken} HP.")
            if not p.is_alive():
                return "dead"
        elif kind == "merchant":
            shop(p)
        elif kind == "rest":
            gained = p.heal(p.max_hp // 3)
            print(f"You rest by a campfire and recover {gained} HP.")
        elif kind == "fountain":
            if random.random() < 0.7:
                gained = p.heal(15)
                print(f"The fountain water is cool and sweet. You recover {gained} HP.")
            else:
                print("The water tastes strange, but nothing happens.")
        elif kind == "stairs":
            print("You find a staircase and walk down into the dark.")
            self.floor += 1
            self.room = 0
            self.layout = self.make_layout()
            return "alive"
        else:
            print("The room is empty and quiet.")
        self.room += 1
        return "alive"

    def find_treasure(self):
        p = self.player
        if random.random() < 0.6:
            gold = random.randint(10, 30) * self.floor
            p.gold += gold
            print(f"You open a chest and find {gold} gold!")
        else:
            name = random.choice(["potion", "potion", "big potion", "iron sword", "leather armor"])
            print(f"Inside the chest there is a {name}!")
            p.add_item(name)

    def play(self):
        while self.player.is_alive():
            self.show_status()
            choice = ask("[n]ext room, [u]se potion, [i]nventory, [s]ave or [q]uit? ", "nuisq")
            if choice == "n":
                outcome = self.enter_room()
                if outcome == "dead":
                    print("\nYou collapse in the dark. The dungeon claims another hero. GAME OVER.")
                    return
                if outcome == "won":
                    print(f"\nThe Dragon Lord falls! {self.player.name} escapes with {self.player.gold} gold. YOU WIN!")
                    return
            elif choice == "u":
                self.player.use_potion()
            elif choice == "i":
                self.show_inventory()
            elif choice == "s":
                self.save()
            else:
                print("You leave the dungeon for now.")
                return


def load_game():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return Game.from_dict(json.load(f))
    except (OSError, ValueError, KeyError):
        print("No usable save file was found.")
        return None


def main():
    print("=== DUNGEON CRAWLER ===")
    choice = ask("[n]ew game, [l]oad game or [q]uit? ", "nlq")
    if choice == "q":
        return
    game = load_game() if choice == "l" else None
    if game is None:
        name = read("Name your hero? ").title() or "Hero"
        game = Game(Player(name))
    game.play()


if __name__ == "__main__":
    main()
''',
    },
    {
        "name": "expense_tracker",
        "filename": "expense_tracker.py",
        "code": r'''
"""Expense Tracker - keep track of your spending from the terminal.

Everything is stored in a small SQLite database file, so your data is
still there the next time you start the program. You can add and search
expenses, see summaries by category and by month, set monthly budgets
for each category and export everything to a CSV file.
Only the Python standard library is needed.
"""

import csv
import sqlite3
from datetime import date, datetime

DB_FILE = "expenses.db"
CSV_FILE = "expenses_export.csv"
CATEGORIES = ["food", "transport", "housing", "fun", "health", "shopping", "other"]
BAR_WIDTH = 30


def connect():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, spent_on TEXT NOT NULL, amount REAL NOT NULL, category TEXT NOT NULL, note TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS budgets (category TEXT PRIMARY KEY, monthly_limit REAL NOT NULL)")
    conn.commit()
    return conn


def read_text(prompt, default=""):
    try:
        value = input(prompt).strip()
    except EOFError:
        raise SystemExit
    return value or default


def read_amount(prompt):
    while True:
        raw = read_text(prompt).replace(",", ".")
        try:
            amount = float(raw)
        except ValueError:
            print("Please type a number like 12.50")
            continue
        if amount <= 0:
            print("The amount must be more than zero.")
            continue
        return round(amount, 2)


def read_date(prompt):
    while True:
        raw = read_text(prompt, date.today().isoformat())
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date().isoformat()
        except ValueError:
            print("Use the format YYYY-MM-DD, for example 2026-03-14")


def read_category():
    print("Categories: " + ", ".join(CATEGORIES))
    while True:
        name = read_text("Category (default other)? ", "other").lower()
        if name in CATEGORIES:
            return name
        print("Please pick one of the categories in the list.")


def money(value):
    return f"{value:,.2f}"


def add_expense(conn):
    spent_on = read_date("Date (YYYY-MM-DD, empty for today)? ")
    amount = read_amount("Amount? ")
    category = read_category()
    note = read_text("Note (optional)? ")
    conn.execute("INSERT INTO expenses (spent_on, amount, category, note) VALUES (?, ?, ?, ?)", (spent_on, amount, category, note))
    conn.commit()
    print(f"Saved {money(amount)} for {category} on {spent_on}.")
    warn_if_over_budget(conn, category, spent_on[:7])


def print_rows(rows):
    if not rows:
        print("No expenses found.")
        return
    print(f"{'ID':>4}  {'Date':<10}  {'Amount':>10}  {'Category':<10}  Note")
    print("-" * 56)
    for row in rows:
        print(f"{row['id']:>4}  {row['spent_on']:<10}  {money(row['amount']):>10}  {row['category']:<10}  {row['note'] or ''}")


def list_expenses(conn, limit=15):
    rows = conn.execute("SELECT * FROM expenses ORDER BY spent_on DESC, id DESC LIMIT ?", (limit,)).fetchall()
    print(f"\nYour {len(rows)} most recent expenses")
    print_rows(rows)


def search_expenses(conn):
    term = read_text("Search for (note or category)? ").lower()
    if not term:
        print("Nothing to search for.")
        return
    like = f"%{term}%"
    rows = conn.execute("SELECT * FROM expenses WHERE lower(note) LIKE ? OR category LIKE ? ORDER BY spent_on DESC", (like, like)).fetchall()
    print_rows(rows)
    if rows:
        print(f"Total for these results: {money(sum(r['amount'] for r in rows))}")


def delete_expense(conn):
    raw = read_text("ID of the expense to delete? ")
    if not raw.isdigit():
        print("That is not a valid ID.")
        return
    row = conn.execute("SELECT * FROM expenses WHERE id = ?", (int(raw),)).fetchone()
    if row is None:
        print("There is no expense with that ID.")
        return
    answer = read_text(f"Delete {money(row['amount'])} for {row['category']}? (y/n) ", "n").lower()
    if answer == "y":
        conn.execute("DELETE FROM expenses WHERE id = ?", (row["id"],))
        conn.commit()
        print("Deleted.")
    else:
        print("Nothing was deleted.")


def bar(value, maximum):
    if maximum <= 0:
        return ""
    return "#" * max(1, int(BAR_WIDTH * value / maximum))


def summary_by_category(conn):
    month = read_text("Month (YYYY-MM, empty for all time)? ")
    if month:
        rows = conn.execute("SELECT category, SUM(amount) AS total FROM expenses WHERE substr(spent_on, 1, 7) = ? GROUP BY category ORDER BY total DESC", (month,)).fetchall()
    else:
        rows = conn.execute("SELECT category, SUM(amount) AS total FROM expenses GROUP BY category ORDER BY total DESC").fetchall()
    if not rows:
        print("No data for that period.")
        return
    biggest = rows[0]["total"]
    grand_total = sum(r["total"] for r in rows)
    print(f"\nSpending by category {month or '(all time)'}")
    for row in rows:
        share = 100 * row["total"] / grand_total
        print(f"{row['category']:<10} {money(row['total']):>10} {share:5.1f}%  {bar(row['total'], biggest)}")
    print(f"{'TOTAL':<10} {money(grand_total):>10}")


def monthly_report(conn):
    rows = conn.execute("SELECT substr(spent_on, 1, 7) AS month, SUM(amount) AS total, COUNT(*) AS count FROM expenses GROUP BY month ORDER BY month DESC LIMIT 12").fetchall()
    if not rows:
        print("No expenses yet.")
        return
    biggest = max(r["total"] for r in rows)
    print("\nLast months")
    for row in rows:
        print(f"{row['month']}  {money(row['total']):>10}  ({row['count']:>3} items)  {bar(row['total'], biggest)}")
    average = sum(r["total"] for r in rows) / len(rows)
    print(f"Average per month: {money(average)}")


def set_budget(conn):
    category = read_category()
    limit = read_amount("Monthly limit for this category? ")
    conn.execute("INSERT INTO budgets (category, monthly_limit) VALUES (?, ?) ON CONFLICT(category) DO UPDATE SET monthly_limit = excluded.monthly_limit", (category, limit))
    conn.commit()
    print(f"Budget for {category} is now {money(limit)} per month.")


def spent_in_month(conn, category, month):
    row = conn.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE category = ? AND substr(spent_on, 1, 7) = ?", (category, month)).fetchone()
    return row["total"]


def warn_if_over_budget(conn, category, month):
    row = conn.execute("SELECT monthly_limit FROM budgets WHERE category = ?", (category,)).fetchone()
    if row is None:
        return
    spent = spent_in_month(conn, category, month)
    if spent > row["monthly_limit"]:
        print(f"WARNING: you are over your {category} budget ({money(spent)} of {money(row['monthly_limit'])}).")


def check_budgets(conn):
    month = date.today().isoformat()[:7]
    budgets = conn.execute("SELECT * FROM budgets ORDER BY category").fetchall()
    if not budgets:
        print("You have not set any budgets yet.")
        return
    print(f"\nBudgets for {month}")
    for row in budgets:
        spent = spent_in_month(conn, row["category"], month)
        used = 100 * spent / row["monthly_limit"]
        status = "OVER" if used > 100 else "ok"
        print(f"{row['category']:<10} {money(spent):>10} / {money(row['monthly_limit']):>10}  {used:6.1f}%  {status}")


def export_csv(conn):
    rows = conn.execute("SELECT * FROM expenses ORDER BY spent_on, id").fetchall()
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "date", "amount", "category", "note"])
        for row in rows:
            writer.writerow([row["id"], row["spent_on"], row["amount"], row["category"], row["note"]])
    print(f"Exported {len(rows)} expenses to {CSV_FILE}.")


MENU = """
1. Add an expense
2. Show recent expenses
3. Search expenses
4. Delete an expense
5. Summary by category
6. Monthly report
7. Set a budget
8. Check budgets
9. Export to CSV
0. Quit"""


def main():
    conn = connect()
    actions = {
        "1": add_expense,
        "2": list_expenses,
        "3": search_expenses,
        "4": delete_expense,
        "5": summary_by_category,
        "6": monthly_report,
        "7": set_budget,
        "8": check_budgets,
        "9": export_csv,
    }
    print("=== EXPENSE TRACKER ===")
    while True:
        print(MENU)
        choice = read_text("Choose an option? ")
        if choice == "0":
            print("Goodbye!")
            break
        action = actions.get(choice)
        if action is None:
            print("Please choose a number from the menu.")
            continue
        action(conn)
    conn.close()


if __name__ == "__main__":
    main()
''',
    },
    {
        "name": "minesweeper",
        "filename": "minesweeper.py",
        "code": r'''
"""Minesweeper - the classic mine clearing game built with tkinter.

Left click reveals a square and right click places a flag.
Pick Easy, Medium or Hard with the buttons at the top.
The first click is always safe and opens up some space.
Only the Python standard library is needed.
"""

import random
import time
import tkinter as tk

# columns, rows, mines
LEVELS = {
    "Easy": (9, 9, 10),
    "Medium": (16, 16, 40),
    "Hard": (24, 16, 80),
}

NUMBER_COLORS = {
    1: "#1976d2",
    2: "#2e7d32",
    3: "#d32f2f",
    4: "#283593",
    5: "#6d4c41",
    6: "#00838f",
    7: "#212121",
    8: "#757575",
}


class MineField:
    """Game rules only. This class knows nothing about the window."""

    def __init__(self, cols, rows, mines):
        self.cols = cols
        self.rows = rows
        self.mines = mines
        self.mine_cells = set()
        self.revealed = set()
        self.flags = set()
        self.generated = False
        self.exploded = False

    def neighbours(self, x, y):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx = x + dx
                ny = y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    yield nx, ny

    def generate(self, safe_x, safe_y):
        """Place the mines after the first click so it is never a mine."""
        forbidden = {(safe_x, safe_y)} | set(self.neighbours(safe_x, safe_y))
        spots = [(x, y) for x in range(self.cols) for y in range(self.rows) if (x, y) not in forbidden]
        self.mine_cells = set(random.sample(spots, self.mines))
        self.generated = True

    def count_around(self, x, y):
        return sum(1 for cell in self.neighbours(x, y) if cell in self.mine_cells)

    def reveal(self, x, y):
        """Reveal a square and flood fill empty areas. Returns the newly opened squares."""
        if not self.generated:
            self.generate(x, y)
        if (x, y) in self.flags or (x, y) in self.revealed:
            return []
        if (x, y) in self.mine_cells:
            self.exploded = True
            return [(x, y)]
        opened = []
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in self.revealed or (cx, cy) in self.flags:
                continue
            self.revealed.add((cx, cy))
            opened.append((cx, cy))
            if self.count_around(cx, cy) == 0:
                stack.extend(self.neighbours(cx, cy))
        return opened

    def toggle_flag(self, x, y):
        if (x, y) in self.revealed:
            return
        if (x, y) in self.flags:
            self.flags.remove((x, y))
        elif len(self.flags) < self.mines:
            self.flags.add((x, y))

    def won(self):
        return not self.exploded and len(self.revealed) == self.cols * self.rows - self.mines


class MinesweeperApp:
    def __init__(self, root):
        self.root = root
        root.title("Minesweeper")
        self.top = tk.Frame(root, padx=6, pady=6)
        self.top.pack(fill="x")
        for name in LEVELS:
            tk.Button(self.top, text=name, command=lambda n=name: self.start(n)).pack(side="left", padx=2)
        self.mines_label = tk.Label(self.top, text="Mines: 0", font=("Arial", 11, "bold"))
        self.mines_label.pack(side="left", padx=12)
        self.timer_label = tk.Label(self.top, text="Time: 0", font=("Arial", 11, "bold"))
        self.timer_label.pack(side="left", padx=12)
        self.status_label = tk.Label(self.top, text="", font=("Arial", 11))
        self.status_label.pack(side="left", padx=12)
        self.board_frame = tk.Frame(root, padx=6, pady=6)
        self.board_frame.pack()
        self.buttons = {}
        self.field = None
        self.started_at = None
        self.finished = False
        self.level = "Easy"
        self.start("Easy")
        self.tick()

    def start(self, level):
        self.level = level
        cols, rows, mines = LEVELS[level]
        self.field = MineField(cols, rows, mines)
        self.started_at = None
        self.finished = False
        self.status_label.config(text="Good luck!")
        for widget in self.board_frame.winfo_children():
            widget.destroy()
        self.buttons = {}
        for y in range(rows):
            for x in range(cols):
                button = tk.Button(self.board_frame, width=2, height=1, font=("Arial", 10, "bold"))
                button.grid(row=y, column=x)
                button.bind("<Button-1>", lambda e, x=x, y=y: self.left_click(x, y))
                button.bind("<Button-2>", lambda e, x=x, y=y: self.right_click(x, y))
                button.bind("<Button-3>", lambda e, x=x, y=y: self.right_click(x, y))
                self.buttons[(x, y)] = button
        self.update_counters()

    def left_click(self, x, y):
        if self.finished:
            return
        if self.started_at is None:
            self.started_at = time.time()
        opened = self.field.reveal(x, y)
        if self.field.exploded:
            self.finish(False)
            return
        for cell in opened:
            self.show_cell(*cell)
        self.update_counters()
        if self.field.won():
            self.finish(True)

    def right_click(self, x, y):
        if self.finished:
            return
        self.field.toggle_flag(x, y)
        button = self.buttons[(x, y)]
        if (x, y) in self.field.flags:
            button.config(text="F", fg="#c62828")
        elif (x, y) not in self.field.revealed:
            button.config(text="", fg="black")
        self.update_counters()

    def show_cell(self, x, y):
        count = self.field.count_around(x, y)
        button = self.buttons[(x, y)]
        button.config(relief="sunken", bg="#e0e0e0", state="disabled")
        if count:
            button.config(text=str(count), disabledforeground=NUMBER_COLORS[count])
        else:
            button.config(text="")

    def finish(self, won):
        self.finished = True
        for (x, y) in self.field.mine_cells:
            button = self.buttons[(x, y)]
            if won:
                button.config(text="F", fg="#2e7d32")
            else:
                button.config(text="*", bg="#ef9a9a")
        if won:
            seconds = int(time.time() - self.started_at)
            self.status_label.config(text=f"You won in {seconds} seconds!")
        else:
            self.status_label.config(text="Boom! You hit a mine.")

    def update_counters(self):
        left = self.field.mines - len(self.field.flags)
        self.mines_label.config(text=f"Mines: {left}")

    def tick(self):
        if self.started_at is not None and not self.finished:
            self.timer_label.config(text=f"Time: {int(time.time() - self.started_at)}")
        elif self.started_at is None:
            self.timer_label.config(text="Time: 0")
        self.root.after(500, self.tick)


def main():
    root = tk.Tk()
    MinesweeperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
''',
    },
    {
        "name": "wordle",
        "filename": "wordle.py",
        "code": r'''
"""Wordle - guess the hidden five letter word in six tries.

After every guess each letter is colored. Green means the right letter
in the right place, yellow means the letter is in the word but somewhere
else and grey means the letter is not in the word at all.
Your statistics are saved in a JSON file between games.
Only the Python standard library is needed.
"""

import json
import os
import random
from datetime import date

STATS_FILE = "wordle_stats.json"
WORD_LENGTH = 5
MAX_TRIES = 6

WORDS = [
    "apple", "brave", "candy", "dream", "eagle", "flame", "grape", "house",
    "ivory", "joker", "knife", "lemon", "mango", "night", "ocean", "piano",
    "queen", "river", "stone", "tiger", "uncle", "vivid", "water", "xenon",
    "yacht", "zebra", "angry", "beach", "cloud", "dance", "earth", "field",
    "ghost", "heart", "image", "jolly", "karma", "light", "music", "noble",
    "olive", "pearl", "quiet", "robot", "sugar", "table", "ultra", "voice",
    "whale", "young", "bloom", "crane", "drive", "elbow", "frost", "giant",
    "happy", "input", "jelly", "kneel", "laugh", "mouse", "nurse", "orbit",
    "paint", "quest", "radio", "smile", "toast", "unity", "vapor", "wheat",
    "pride", "plant", "chair", "brick", "swift", "globe", "shark", "flute",
]

GREEN = "\033[97;42m"
YELLOW = "\033[30;43m"
GREY = "\033[97;100m"
RESET = "\033[0m"
STYLES = {"green": GREEN, "yellow": YELLOW, "grey": GREY}
RANK = {"unused": 0, "grey": 1, "yellow": 2, "green": 3}


def read(prompt):
    try:
        return input(prompt).strip().lower()
    except EOFError:
        raise SystemExit


def score_guess(guess, answer):
    """Return a color for every letter, handling repeated letters correctly."""
    result = ["grey"] * len(guess)
    remaining = list(answer)
    for i, letter in enumerate(guess):
        if letter == answer[i]:
            result[i] = "green"
            remaining.remove(letter)
    for i, letter in enumerate(guess):
        if result[i] == "grey" and letter in remaining:
            result[i] = "yellow"
            remaining.remove(letter)
    return result


def render_word(word, colors):
    pieces = []
    for letter, color in zip(word, colors):
        pieces.append(f"{STYLES[color]} {letter.upper()} {RESET}")
    return " ".join(pieces)


def render_keyboard(letter_state):
    rows = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]
    print()
    for index, row in enumerate(rows):
        pieces = []
        for letter in row:
            state = letter_state.get(letter, "unused")
            if state == "unused":
                pieces.append(letter.upper())
            else:
                pieces.append(f"{STYLES[state]}{letter.upper()}{RESET}")
        print(" " * index + " ".join(pieces))


def update_keyboard(letter_state, guess, colors):
    for letter, color in zip(guess, colors):
        if RANK[color] > RANK[letter_state.get(letter, "unused")]:
            letter_state[letter] = color


def load_stats():
    default = {"played": 0, "won": 0, "streak": 0, "best_streak": 0, "distribution": {str(i): 0 for i in range(1, MAX_TRIES + 1)}}
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return default
    default.update(data)
    return default


def save_stats(stats):
    try:
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
    except OSError:
        print("Could not save your statistics.")


def record_result(stats, tries):
    stats["played"] += 1
    if tries is None:
        stats["streak"] = 0
    else:
        stats["won"] += 1
        stats["streak"] += 1
        stats["best_streak"] = max(stats["best_streak"], stats["streak"])
        stats["distribution"][str(tries)] += 1
    save_stats(stats)


def show_stats(stats):
    played = stats["played"]
    percent = 100 * stats["won"] // played if played else 0
    print("\n=== STATISTICS ===")
    print(f"Played {played}   Won {percent}%   Streak {stats['streak']}   Best streak {stats['best_streak']}")
    most = max(stats["distribution"].values()) or 1
    for tries in range(1, MAX_TRIES + 1):
        count = stats["distribution"][str(tries)]
        bar = "#" * max(1 if count else 0, 20 * count // most)
        print(f"  {tries} | {bar} {count}")


def ask_guess(used):
    while True:
        guess = read(f"Guess {len(used) + 1}/{MAX_TRIES}? ")
        if len(guess) != WORD_LENGTH or not guess.isalpha():
            print(f"Please type a word with exactly {WORD_LENGTH} letters.")
        elif guess in used:
            print("You already tried that word.")
        else:
            return guess


def play_round(answer):
    """Play one game. Returns the number of tries used or None when the player lost."""
    used = []
    letter_state = {}
    print(f"\nGuess the {WORD_LENGTH} letter word. You have {MAX_TRIES} tries.")
    while len(used) < MAX_TRIES:
        guess = ask_guess(used)
        colors = score_guess(guess, answer)
        used.append(guess)
        update_keyboard(letter_state, guess, colors)
        print()
        for past in used:
            print("   " + render_word(past, score_guess(past, answer)))
        render_keyboard(letter_state)
        if guess == answer:
            print(f"\nBrilliant! You found it in {len(used)} tries.")
            return len(used)
    print(f"\nOut of tries. The word was {answer.upper()}.")
    return None


def daily_word():
    return WORDS[date.today().toordinal() % len(WORDS)]


def show_help():
    print("\nHOW TO PLAY")
    print(f"Guess the hidden word in {MAX_TRIES} tries. After each guess the letters change color.")
    print(f"  {GREEN} A {RESET} the letter is correct and in the right place")
    print(f"  {YELLOW} B {RESET} the letter is in the word but in a different place")
    print(f"  {GREY} C {RESET} the letter is not in the word")


def main():
    os.system("")
    stats = load_stats()
    print("=== WORDLE ===")
    while True:
        choice = read("\n[p]lay, [d]aily word, [s]tats, [h]elp or [q]uit? ")[:1]
        if choice == "p":
            record_result(stats, play_round(random.choice(WORDS)))
        elif choice == "d":
            record_result(stats, play_round(daily_word()))
        elif choice == "s":
            show_stats(stats)
        elif choice == "h":
            show_help()
        elif choice == "q":
            print("Thanks for playing!")
            return
        else:
            print("Please choose p, d, s, h or q.")


if __name__ == "__main__":
    main()
''',
    },
]


class WrongWindow(Exception):
    """Raised when the focused window is not the project's VS Code window."""


ACTIVE_GUARD = None    # set by type_text: True while the project window has the focus
ACTIVE_REFOCUS = None  # set by type_text: brings the project window back to the front
PAUSED = False
PENDING_TOGGLE = False
_hotkey_was_down = False


def hotkey_down():
    """True while Ctrl+Alt+P or Pause/Break is held down (Windows only)."""
    if not IS_WINDOWS:
        return False
    import ctypes
    state = ctypes.windll.user32.GetAsyncKeyState
    combo = all(state(key) & 0x8000 for key in (0x11, 0x12, 0x50))  # Ctrl, Alt, P
    return combo or bool(state(0x13) & 0x8000)                      # Pause/Break


def pause_requested():
    """True once each time the pause keys are pressed (not while they stay held)."""
    global _hotkey_was_down
    down = hotkey_down()
    fired = down and not _hotkey_was_down
    _hotkey_was_down = down
    return fired


def snooze(seconds):
    """Sleep in small slices so a quick press of the pause keys is never missed."""
    global PENDING_TOGGLE
    for _ in range(max(1, int(seconds / 0.05))):
        if pause_requested():
            PENDING_TOGGLE = True
        time.sleep(0.05)


def wait_for_resume():
    """Block (sending no keys at all) until the pause keys are pressed again."""
    global PAUSED, PENDING_TOGGLE
    PAUSED = True
    PENDING_TOGGLE = False
    while PAUSED:
        time.sleep(0.1)
        if pause_requested():
            PAUSED = False


def checkpoint():
    """If the pause keys were pressed, pause now. Returns True if it paused."""
    global PENDING_TOGGLE
    if PENDING_TOGGLE or pause_requested():
        PENDING_TOGGLE = False
        print("\n[paused] Use your PC freely. Press Ctrl+Alt+P (or Pause/Break) to continue.")
        wait_for_resume()
        print("[resumed]")
        return True
    return False


def ensure_focus(guard, refocus, waited=False):
    """Make sure keys will go to the project window.

    If you moved to another window, wait for you (no keys are sent) and bring
    the project window back when you resume. If it cannot be brought back, stop.
    """
    if guard is None:
        return
    if waited or not guard():
        if not waited:
            print("\n[paused] You switched to another window. Finish what you are doing, then press "
                  "Ctrl+Alt+P (or Pause/Break) and the bot will carry on.")
            wait_for_resume()
            print("[resumed]")
        if not (refocus and refocus()):
            raise WrongWindow("The project's VS Code window could not be brought back to the front.")


def ready(guard, refocus):
    """Call before sending any key: handles the pause keys and lost focus."""
    resumed = checkpoint()
    ensure_focus(guard, refocus, waited=resumed)


def check_focus():
    ready(ACTIVE_GUARD, ACTIVE_REFOCUS)


# ---------------------------------------------------------- window safety ---
def window_titles():
    """Return [(handle, title)] for visible top-level windows (Windows only)."""
    if not IS_WINDOWS:
        return []
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    found = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def callback(hwnd, _lparam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                found.append((hwnd, buf.value))
        return True

    user32.EnumWindows(callback, 0)
    return found


def active_title():
    """Title of the window that currently has the keyboard focus (Windows only)."""
    if not IS_WINDOWS:
        return None
    import ctypes
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def is_project_window(title, file_name, folder_name):
    return bool(title) and file_name in title and folder_name in title and "Visual Studio Code" in title


def focus_editor(file_name, folder_name):
    """Make sure the focused window is this project's VS Code window.

    Returns True when it is. On systems where the title cannot be read
    (macOS and Linux) it always returns True.
    """
    if not IS_WINDOWS:
        return True
    import ctypes
    user32 = ctypes.windll.user32
    for _ in range(6):
        if is_project_window(active_title(), file_name, folder_name):
            return True
        for hwnd, text in window_titles():
            if is_project_window(text, file_name, folder_name):
                user32.ShowWindow(hwnd, 9)
                pyautogui.press("alt")  # lets Windows allow the focus change
                user32.SetForegroundWindow(hwnd)
                break
        time.sleep(1.5)
    return is_project_window(active_title(), file_name, folder_name)


# ------------------------------------------------------------ typing core ---
def pause(lo=None, hi=None):
    lo = BASE_DELAY[0] if lo is None else lo
    hi = BASE_DELAY[1] if hi is None else hi
    snooze(random.uniform(lo, hi) * SLOW)


def nap(lo, hi):
    snooze(random.uniform(lo, hi) * SLOW)


def press_char(ch):
    check_focus()
    if ch == "\n":
        pyautogui.press("enter")
    elif ch == "\t":
        pyautogui.press("tab")
    else:
        pyautogui.write(ch)


def wrong_char(ch):
    options = NEIGHBOURS.get(ch.lower())
    if not options:
        return None
    wrong = random.choice(options)
    return wrong.upper() if ch.isupper() else wrong


def fix_typo(wrong_count):
    """Notice the mistake after a beat, then backspace slowly."""
    nap(0.5, 1.3)
    for _ in range(wrong_count):
        check_focus()
        pyautogui.press("backspace")
        pause(0.15, 0.3)


def fix_indent(cur, target):
    """Tab / Shift+Tab until the cursor line's indent matches the target."""
    levels = round((target - cur) / INDENT_SIZE)
    for _ in range(abs(levels)):
        check_focus()
        if levels > 0:
            pyautogui.press("tab")
        else:
            pyautogui.hotkey("shift", "tab")
        pause(0.2, 0.45)
    return target


def type_line(line):
    i = 0
    while i < len(line):
        ch = line[i]

        if ch.isalpha() and random.random() < TYPO_CHANCE:
            wrong = wrong_char(ch)
            if wrong:
                press_char(wrong)
                pause()
                # sometimes keep typing a character or two before noticing
                extra = 0
                if random.random() < 0.4 and i + 1 < len(line):
                    press_char(line[i + 1])
                    extra = 1
                    pause()
                fix_typo(1 + extra)
                # fall through and type the correct char

        press_char(ch)
        pause()
        if random.random() < THINK_PAUSE_CHANCE:
            nap(*THINK_PAUSE)
        i += 1


def clean_text(text):
    """Keep only what pyautogui can type: plain ASCII, spaces instead of tabs."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    lines = [ln.rstrip() for ln in text.expandtabs(INDENT_SIZE).split("\n")]
    return "\n".join(lines).strip("\n") + "\n"


def opens_block(content):
    code = re.sub(r"\s+#.*$", "", content).rstrip()
    return code.endswith((":", "{", "(", "["))


def type_text(text, guard=None, refocus=None):
    global ACTIVE_GUARD, ACTIVE_REFOCUS
    ACTIVE_GUARD = guard
    ACTIVE_REFOCUS = refocus
    try:
        type_lines(clean_text(text).split("\n"))
    finally:
        ACTIVE_GUARD = None
        ACTIVE_REFOCUS = None


def type_lines(lines):
    cur = 0  # indent (in spaces) the editor currently has on the cursor's line
    for idx, line in enumerate(lines):
        content = line.strip()
        if content:
            target = len(line) - len(line.lstrip())
            cur = fix_indent(cur, target)
            type_line(content)
        if idx < len(lines) - 1:
            press_char("\n")
            # the editor keeps the same indent on the new line,
            # and adds one level after a line that opens a block
            if opens_block(content):
                cur += INDENT_SIZE
            nap(*LINE_PAUSE)


# ------------------------------------------------------------ online part ---
def http_get(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "vibe-coder/1.0", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def github_headers():
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


TOPICS = [
    "game", "cli tool", "text adventure", "tkinter app", "flask app", "automation script",
    "web scraper", "chat bot", "data visualisation", "productivity tool", "puzzle game",
    "file utility", "calculator", "note taking app", "weather app", "quiz app",
    "inventory system", "bank app", "library manager", "pygame game",
]


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug[:40] or "project"


def code_lines(code):
    return len([ln for ln in code.splitlines() if ln.strip()])


def looks_ok(code):
    """True when the code compiles and is long enough to be worth typing."""
    if not code or code_lines(code) < MIN_LINES:
        return False
    try:
        compile(code, "<project>", "exec")
    except (SyntaxError, ValueError):
        return False
    return True


def generate_with_claude(idea):
    """Ask Claude for a long original program inspired by the idea (needs ANTHROPIC_API_KEY)."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    prompt = (
        "Write one complete, original, single-file Python program inspired by this idea "
        f"found online: {idea}\n\n"
        "Make it a real, fairly large application with several classes or functions, a menu "
        "or game loop, input checking and saving data to a file. "
        "Rules: standard library only, runnable as-is, between 300 and 500 lines, clear comments, "
        "4-space indentation (no tabs), ASCII characters only, and a module docstring. "
        "Never end a comment or docstring line with a colon. "
        "Reply with ONLY the code, no markdown fences, no explanation."
    )
    body = json.dumps({
        "model": os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5"),
        "max_tokens": 16000,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    text = "".join(block.get("text", "") for block in data.get("content", []))
    return re.sub(r"^```[a-zA-Z]*\n|\n```\s*$", "", text.strip()) or None


def fetch_online_project():
    """Find a popular Python repo for inspiration; return a project dict or None."""
    topic = random.choice(TOPICS)
    query = urllib.parse.quote(f"{topic} language:python")
    url = (
        "https://api.github.com/search/repositories"
        f"?q={query}&sort=stars&per_page=30&page={random.randint(1, 4)}"
    )
    repos = json.loads(http_get(url, github_headers())).get("items", [])
    random.shuffle(repos)

    for repo in repos[:6]:
        name = repo["name"]
        idea = f"{name} - {repo.get('description') or topic} (topic: {topic})"
        print(f"[online] idea: {idea}")

        # 1) Preferred: Claude writes something original and long from the idea
        try:
            code = generate_with_claude(idea)
        except Exception as exc:  # network / API problems -> try the next option
            print(f"[online] Claude generation failed: {exc}")
            code = None
        if looks_ok(code):
            return {"name": slugify(name), "filename": f"{slugify(name)}.py", "code": code}
        if code:
            print("[online] generated code was too short or broken, skipping it")

        # 2) Otherwise type a longer public file from the repo
        try:
            listing = json.loads(http_get(f"https://api.github.com/repos/{repo['full_name']}/contents", github_headers()))
        except Exception as exc:
            print(f"[online] could not list repo: {exc}")
            continue
        files = [
            f for f in listing
            if isinstance(f, dict) and f.get("name", "").endswith(".py")
            and 4000 <= f.get("size", 0) <= 40000 and f.get("download_url")
        ]
        random.shuffle(files)
        for chosen in files[:3]:
            try:
                code = http_get(chosen["download_url"])
            except Exception as exc:
                print(f"[online] download failed: {exc}")
                continue
            if looks_ok(code):
                header = f"# Inspired by / copied from: {repo['html_url']}\n# Check the repo's licence before reusing.\n\n"
                return {"name": slugify(name), "filename": chosen["name"], "code": header + code}
    return None


# -------------------------------------------------------------- project loop
def load_local_projects(folder):
    projects = []
    if not folder:
        return projects
    for path in sorted(Path(folder).expanduser().glob("*.py")):
        try:
            projects.append({"name": slugify(path.stem), "filename": path.name, "code": path.read_text(encoding="utf-8")})
        except OSError as exc:
            print(f"Skipping {path}: {exc}")
    return projects


def find_code_command():
    return shutil.which("code") or shutil.which("code.cmd")


def open_in_new_window(folder, file_path, wait):
    cmd = find_code_command()
    if not cmd:
        sys.exit(
            "Could not find the 'code' command. In VS Code press Ctrl+Shift+P and run "
            "\"Shell Command: Install 'code' command in PATH\", then try again."
        )
    subprocess.Popen([cmd, "-n", str(folder), str(file_path)], shell=(os.name == "nt"))
    time.sleep(wait)


def remove_folder(folder):
    """Delete a temporary project folder. VS Code may need a moment to let go of it."""
    for _ in range(6):
        shutil.rmtree(folder, ignore_errors=True)
        if not folder.exists():
            return True
        time.sleep(2)
    return False


def new_project_folder(out_root, name):
    """Create the next numbered folder, never reusing or overwriting an old one."""
    number = 1
    while True:
        folder = out_root / f"{number:03d}_{slugify(name)}"
        if not folder.exists() and not any(out_root.glob(f"{number:03d}_*")):
            folder.mkdir(parents=True)
            return folder
        number += 1


def run(args):
    if args.keep:
        out_root = Path(args.out).expanduser().resolve()
        out_root.mkdir(parents=True, exist_ok=True)
        print(f"Finished projects are KEPT under: {out_root}")
    else:
        out_root = Path(tempfile.mkdtemp(prefix="vibe_coder_"))
        print("Nothing is kept: each project is deleted from your PC as soon as it has been typed.")
    try:
        type_projects(args, out_root)
    finally:
        if not args.keep:
            shutil.rmtree(out_root, ignore_errors=True)


def type_projects(args, out_root):
    pool = list(BUILTIN_PROJECTS) + load_local_projects(args.projects_dir)
    queue = []
    started = time.time()
    round_no = 0

    if IS_WINDOWS and args.no_focus_check:
        print("Window check is OFF (--no-focus-check).")
    print(f"Starting in {COUNTDOWN_SECONDS}s. PAUSE / RESUME: press Ctrl+Alt+P (or Pause/Break). "
          "STOP: Ctrl+C or move the mouse to a screen corner.")
    print("While it is typing, keep the VS Code window in front. If you click elsewhere it pauses by itself.")
    for s in range(COUNTDOWN_SECONDS, 0, -1):
        print(s, end=" ", flush=True)
        time.sleep(1)
    print()

    while True:
        if args.hours and (time.time() - started) > args.hours * 3600:
            print("Time limit reached. Done.")
            return

        project = None
        if args.online:
            try:
                project = fetch_online_project()
            except Exception as exc:
                print(f"[online] failed, using built-in project instead: {exc}")
        if not project:
            if not queue:
                queue = random.sample(pool, len(pool))
            project = queue.pop()

        round_no += 1
        folder = new_project_folder(out_root, project["name"])
        file_path = folder / project["filename"]
        file_path.write_text("", encoding="utf-8")

        print(f"\n=== Project {round_no}: {project['name']} ({code_lines(project['code'])} lines) -> {folder}")
        open_in_new_window(folder, file_path, args.window_wait)

        if args.no_focus_check:
            in_front = lambda: True
            bring_back = lambda: True
        else:
            in_front = lambda: is_project_window(active_title(), project["filename"], folder.name) if IS_WINDOWS else True
            bring_back = lambda: focus_editor(project["filename"], folder.name)
        if not bring_back():
            raise WrongWindow("The new VS Code window did not come to the front.")
        snooze(1.5)

        type_text(project["code"].lstrip("\n"), guard=in_front, refocus=bring_back)

        nap(2, 4)
        ready(in_front, bring_back)
        pyautogui.hotkey(MOD, "s")
        nap(2, 4)
        closed = False
        if not args.keep_windows:
            ready(in_front, bring_back)
            pyautogui.hotkey(MOD, "shift", "w")  # close this project's window
            closed = True
        if closed and not args.keep:
            nap(2, 3)
            if remove_folder(folder):
                print("    (temporary files deleted)")
            else:
                print("    (could not delete the temporary folder yet, it is removed when the bot stops)")
        print(f"=== Finished {project['name']}")
        time.sleep(random.uniform(*BETWEEN_PROJECTS))


def main():
    global SLOW
    parser = argparse.ArgumentParser(description="Slow, human-like auto-typer that builds long projects forever.")
    parser.add_argument("--keep", action="store_true", help="keep the finished projects on disk (default: delete them)")
    parser.add_argument("--out", default="~/vibe_projects", help="where projects are kept when you use --keep")
    parser.add_argument("--online", action="store_true", help="get project ideas/code from the internet")
    parser.add_argument("--hours", type=float, default=0, help="stop after this many hours (0 = until you stop it)")
    parser.add_argument("--slowdown", type=float, default=1.0, help="multiply all delays (1.5 = 50%% slower)")
    parser.add_argument("--projects-dir", default=None, help="folder of your own .py files to type too")
    parser.add_argument("--keep-windows", action="store_true", help="don't close each VS Code window afterwards")
    parser.add_argument("--window-wait", type=float, default=WINDOW_WAIT, help="seconds to wait for a new VS Code window")
    parser.add_argument("--no-focus-check", action="store_true", help="skip the window title safety check")
    args = parser.parse_args()
    SLOW = max(0.2, args.slowdown)

    try:
        run(args)
    except KeyboardInterrupt:
        print("\nStopped (Ctrl+C).")
    except pyautogui.FailSafeException:
        print("\nStopped (mouse hit a screen corner).")
    except WrongWindow as exc:
        print(f"\nSTOPPED for safety: {exc}")
        print("Nothing more was typed. Close extra VS Code windows, make sure vibe_coder.py is not "
              "open in VS Code, and run the script again from PowerShell or Command Prompt.")
        print("If your VS Code uses a custom window title, add --no-focus-check.")


if __name__ == "__main__":
    main()