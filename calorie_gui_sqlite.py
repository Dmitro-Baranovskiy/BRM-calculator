#!/bin/python

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json
import os
from datetime import datetime

# BMR & TDEE formulas

activity_map = {
    "сидячий": 1.2,       "легкий": 1.375,
    "помірний": 1.55,     "активний": 1.725,
    "дуже активний": 1.9,
    "sedentary": 1.2,     "light": 1.375,
    "moderate": 1.55,     "active": 1.725,
    "very_active": 1.9
}

male_indicators = {"m", "male", "ч", "чоловік"}
female_indicators = {"f", "female", "ж", "жінка"}


def calc_bmr(weight, height, age, gender):
    g = gender.lower()
    if g in male_indicators:
        return 10 * weight + 6.25 * height - 5 * age + 5
    return 10 * weight + 6.25 * height - 5 * age - 161


def calc_tdee(bmr, activity):
    return bmr * activity_map.get(activity, 1.2)


# I18N localization

def load_translations(lang="uk"):
    path = os.path.join("locales", f"{lang}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# SQ database

DB_PATH = "calories.db"


def init_db():
    conn = sqlite3.connect("calories.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gender TEXT, weight REAL, height REAL,
        age INTEGER, activity TEXT
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, product TEXT,
        calories REAL, date TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )""")
    conn.commit()
    conn.close()


def add_user(gender, weight, height, age, activity):
    conn = sqlite3.connect("calories.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO users (gender, weight, height, age, activity)
        VALUES (?, ?, ?, ?, ?)
    """, (gender, weight, height, age, activity))
    conn.commit()
    uid = c.lastrowid
    conn.close()
    return uid


def get_all_users():
    conn = sqlite3.connect("calories.db")
    c = conn.cursor()
    c.execute("SELECT id, gender, weight, height, age, activity FROM users")
    users = c.fetchall()
    conn.close()
    return users


def add_entry(user_id, product, calories):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("""
      INSERT INTO entries (user_id, product, calories, date)
      VALUES (?, ?, ?, ?)
    """, (user_id, product, calories, today))
    conn.commit()
    conn.close()


def load_today_entries(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("""
      SELECT product, calories FROM entries
      WHERE user_id=? AND date=?
    """, (user_id, today))
    rows = c.fetchall()
    conn.close()
    return rows


#  GUI

class CalorieApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Calorie App")
        self.root.geometry("500x500")

        init_db()

        # Localization
        self.translations = {
            "uk": load_translations("uk"),
            "en": load_translations("en")
        }
        self.lang = "uk"
        self.T = self.translations[self.lang]

        # Style
        style = ttk.Style(self.root)
        style.theme_use("clam")

        # Variables
        self.user_id = None
        self.bmr = 0
        self.tdee = 0
        self.total_cal = tk.DoubleVar(value=0)

        self.gender_var = tk.StringVar()
        self.weight_var = tk.DoubleVar()
        self.height_var = tk.DoubleVar()
        self.age_var = tk.IntVar()
        self.activity_var = tk.StringVar()

        self.product_var = tk.StringVar()
        self.cal_var = tk.DoubleVar()

        # Building GUI
        self.build_language_switcher()
        self.build_ui()

    def build_language_switcher(self):
        frame = ttk.Frame(self.root)
        frame.pack(fill="x", pady=5)
        ttk.Label(frame, text="🌐").pack(side="left")
        ttk.Button(frame, text="Українська",
                   command=lambda: self.switch_lang("uk")
                   ).pack(side="left", padx=2)
        ttk.Button(frame, text="English",
                   command=lambda: self.switch_lang("en")
                   ).pack(side="left")

    def switch_lang(self, lang):
        self.lang = lang
        self.T = self.translations[lang]

        for widget in self.root.winfo_children():
            widget.destroy()
        self.__init__(self.root)

    def build_ui(self):
        # Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        self.tab_user = ttk.Frame(self.notebook, padding=10)
        self.tab_entry = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_user,  text=self.T["tab_user"])
        self.notebook.add(self.tab_entry, text=self.T["tab_entry"])

        self.build_user_tab()
        self.build_entry_tab()

    def build_user_tab(self):
        # User selection frame
        sf = ttk.LabelFrame(self.tab_user, text=self.T["choose_user"])
        sf.pack(fill="x", pady=5)

        self.user_list = ttk.Combobox(
            sf, state="readonly", width=50
        )
        self.user_list.pack(side="left", padx=5)
        self.refresh_user_list()

        ttk.Button(
            sf, text=self.T["select_user"],
            command=self.select_user
        ).pack(side="left", padx=5)

        # Create new user form
        cf = ttk.LabelFrame(self.tab_user, text=self.T["create_user"])
        cf.pack(fill="x", pady=10)

        # Gender
        ttk.Label(cf, text=self.T["gender"]).grid(
            row=0, column=0, sticky="w", pady=2)
        gender_cb = ttk.Combobox(
            cf, values=[self.T["male"], self.T["female"]],
            state="readonly", textvariable=self.gender_var
        )
        gender_cb.grid(row=0, column=1, sticky="ew", padx=5)

        # Weight
        ttk.Label(cf, text=self.T["weight"]).grid(
            row=1, column=0, sticky="w", pady=2)
        ttk.Entry(cf, textvariable=self.weight_var).grid(
            row=1, column=1, sticky="ew", padx=5)

        # Hight
        ttk.Label(cf, text=self.T["height"]).grid(
            row=2, column=0, sticky="w", pady=2)
        ttk.Entry(cf, textvariable=self.height_var).grid(
            row=2, column=1, sticky="ew", padx=5)

        # Age
        ttk.Label(cf, text=self.T["age"]).grid(
            row=3, column=0, sticky="w", pady=2)
        ttk.Entry(cf, textvariable=self.age_var).grid(
            row=3, column=1, sticky="ew", padx=5)

        # Activity level
        ttk.Label(cf, text=self.T["activity"]).grid(
            row=4, column=0, sticky="w", pady=2)
        act_cb = ttk.Combobox(
            cf,
            values=[
                self.T["sedentary"], self.T["light"],
                self.T["moderate"], self.T["active"],
                self.T["very_active"]
            ],
            state="readonly",
            textvariable=self.activity_var
        )
        act_cb.grid(row=4, column=1, sticky="ew", padx=5)

        cf.columnconfigure(1, weight=1)

        ttk.Button(
            cf, text=self.T["save_user"],
            command=self.register_user
        ).grid(row=5, column=0, columnspan=2, pady=10)

    def refresh_user_list(self):
        users = get_all_users()
        labels = [
            f"ID {u[0]}: {u[1]}, {u[2]}кг, {u[3]}см, {u[4]}р, {u[5]}"
            for u in users
        ]
        self.user_list['values'] = labels

    def select_user(self):
        idx = self.user_list.current()
        if idx < 0:
            messagebox.showwarning(self.T["title"], self.T["choose_user"])
            return

        u = get_all_users()[idx]
        self.user_id = u[0]
        gender, w, h, age, act = u[1], u[2], u[3], u[4], u[5]

        self.bmr = calc_bmr(w, h, age, gender)
        self.tdee = calc_tdee(self.bmr, act)
        self.total_cal.set(
            sum(cal for _, cal in load_today_entries(self.user_id))
        )

        messagebox.showinfo(
            self.T["title"],
            f"{self.T['bmr']}: {self.bmr:.0f} ккал\n"
            f"{self.T['tdee']}: {self.tdee:.0f} ккал/день"
        )
        self.load_entries_into_tab()

    def register_user(self):
        try:
            g = self.gender_var.get()
            w = self.weight_var.get()
            h = self.height_var.get()
            a = self.age_var.get()
            act = self.activity_var.get()
        except tk.TclError:
            messagebox.showerror(self.T["title"], self.T["invalid_data"])
            return

        if not all([g, w, h, a, act]):
            messagebox.showerror(self.T["title"], self.T["invalid_data"])
            return

        uid = add_user(g, w, h, a, act)
        self.refresh_user_list()
        self.user_list.current(len(self.user_list['values']) - 1)
        self.select_user()

    def build_entry_tab(self):
        ff = ttk.LabelFrame(self.tab_entry, text=self.T["product_name"])
        ff.pack(fill="x", pady=5)

        ttk.Label(ff, text=self.T["product_name"]).grid(
            row=0, column=0, sticky="w")
        ttk.Entry(ff, textvariable=self.product_var).grid(
            row=0, column=1, sticky="ew", padx=5)

        ttk.Label(ff, text=self.T["calories"]).grid(
            row=1, column=0, sticky="w", pady=5)
        ttk.Entry(ff, textvariable=self.cal_var).grid(
            row=1, column=1, sticky="ew", padx=5)

        ff.columnconfigure(1, weight=1)

        ttk.Button(
            ff, text=self.T["add_product"],
            command=self.add_product_entry
        ).grid(row=2, column=0, columnspan=2, pady=10)

        # History output
        hist = ttk.LabelFrame(self.tab_entry, text=self.T["total_calories"])
        hist.pack(fill="both", expand=True, pady=5)

        self.output = tk.Text(hist, height=10)
        self.output.pack(fill="both", expand=True, padx=5, pady=5)

        ttk.Label(
            hist,
            textvariable=self.total_cal,
            font=("Arial", 14, "bold")
        ).pack(pady=5)

        self.load_entries_into_tab()

    def load_entries_into_tab(self):
        if self.user_id is None:
            return
        self.output.delete("1.0", tk.END)
        entries = load_today_entries(self.user_id)
        total = 0
        for prod, cal in entries:
            self.output.insert(tk.END, f"{prod}: {cal:.0f} ккал\n")
            total += cal
        self.total_cal.set(total)

    def add_product_entry(self):
        if self.user_id is None:
            messagebox.showerror(self.T["title"], self.T["choose_user"])
            return
        try:
            prod = self.product_var.get()
            cal = self.cal_var.get()
        except tk.TclError:
            messagebox.showerror(self.T["title"], self.T["invalid_cal"])
            return

        if not prod or cal <= 0:
            messagebox.showerror(self.T["title"], self.T["invalid_cal"])
            return

        add_entry(self.user_id, prod, cal)
        self.product_var.set("")
        self.cal_var.set(0)
        self.load_entries_into_tab()


# Start the application


if __name__ == "__main__":
    root = tk.Tk()
    app = CalorieApp(root)
    root.mainloop()
