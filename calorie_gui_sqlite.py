#!/bin/python

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt


DB_PATH = "calories.db"

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

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gender TEXT, weight REAL,
        height REAL, age INTEGER,
        activity TEXT
      )
    """)
    c.execute("""
      CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, product TEXT,
        grams REAL, calories REAL, date TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
      )
    """)
    conn.commit()
    conn.close()


def add_user(gender, weight, height, age, activity):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
      INSERT INTO users (gender, weight, height, age, activity)
      VALUES (?, ?, ?, ?, ?)
    """, (gender, weight, height, age, activity))
    uid = c.lastrowid
    conn.commit()
    conn.close()
    return uid


def delete_user_db(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM entries WHERE user_id=?", (user_id,))
    c.execute("DELETE FROM users   WHERE id=?",      (user_id,))
    conn.commit()
    conn.close()


def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, gender, weight, height, age, activity FROM users")
    rows = c.fetchall()
    conn.close()
    return rows


def add_entry(user_id, product, grams, calories):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("""
      INSERT INTO entries (user_id, product, grams, calories, date)
      VALUES (?, ?, ?, ?, ?)
    """, (user_id, product, grams, calories, today))
    conn.commit()
    conn.close()


def load_today_entries(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("""
      SELECT product, grams, calories FROM entries
      WHERE user_id=? AND date=?
    """, (user_id, today))
    rows = c.fetchall()
    conn.close()
    return rows

# Building graphs


def show_calorie_chart(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT date, SUM(calories)
        FROM entries
        WHERE user_id=?
        GROUP BY date
        ORDER BY date DESC
        LIMIT 7
    """, (user_id,))
    data = c.fetchall()
    conn.close()

    if not data:
        messagebox.showinfo("!", "No data available.")
        return

    # Reverse to show the most recent date on the right
    data.reverse()
    dates = [d for d, _ in data]
    totals = [cal for _, cal in data]

    plt.figure(figsize=(7, 4))
    plt.plot(dates, totals, marker='o', linestyle='-', color='darkorange')
    plt.title("Calories over last 7 days")
    plt.xlabel("Date")
    plt.ylabel("Calories")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

#  GUI


class CalorieApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Calorie App")
        self.root.geometry("550x550")

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
        self.grams_var = tk.DoubleVar()
        self.cal100_var = tk.DoubleVar()

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

        for w in self.root.winfo_children():
            w.destroy()
        self.build_language_switcher()
        self.build_ui()

    def build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        self.tab_user = ttk.Frame(self.notebook, padding=10)
        self.tab_entry = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_user,  text=self.T["tab_user"])
        self.notebook.add(self.tab_entry, text=self.T["tab_entry"])

        self.build_user_tab()
        self.build_entry_tab()

    # User management tab
    def build_user_tab(self):
        sf = ttk.LabelFrame(self.tab_user, text=self.T["choose_user"])
        sf.pack(fill="x", pady=5)

        self.user_list = ttk.Combobox(sf, state="readonly", width=60)
        self.user_list.pack(side="left", padx=5)
        self.refresh_user_list()

        ttk.Button(sf, text=self.T["select_user"],
                   command=self.select_user
                   ).pack(side="left", padx=5)
        ttk.Button(sf, text=self.T["delete_user"],
                   command=self.on_delete_user
                   ).pack(side="left", padx=5)

        cf = ttk.LabelFrame(self.tab_user, text=self.T["create_user"])
        cf.pack(fill="x", pady=10)

        ttk.Label(cf, text=self.T["gender"]) .grid(
            row=0, column=0, sticky="w", pady=2)
        ttk.Combobox(cf,
                     values=[self.T["male"], self.T["female"]],
                     state="readonly",
                     textvariable=self.gender_var
                     ).grid(row=0, column=1, sticky="ew", padx=5)

        for i, (lbl, var) in enumerate([
            (self.T["weight"], self.weight_var),
            (self.T["height"], self.height_var),
            (self.T["age"], self.age_var)
        ], start=1):
            ttk.Label(cf, text=lbl).grid(row=i, column=0, sticky="w", pady=2)
            ttk.Entry(cf, textvariable=var).grid(
                row=i, column=1, sticky="ew", padx=5)

        ttk.Label(cf, text=self.T["activity"]) .grid(
            row=4, column=0, sticky="w", pady=2)
        ttk.Combobox(cf,
                     values=[
                         self.T["sedentary"], self.T["light"],
                         self.T["moderate"], self.T["active"],
                         self.T["very_active"]
                     ],
                     state="readonly",
                     textvariable=self.activity_var
                     ).grid(row=4, column=1, sticky="ew", padx=5)

        cf.columnconfigure(1, weight=1)

        ttk.Button(cf, text=self.T["save_user"],
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
        self.user_id, g, w, h, age, act = u
        self.bmr = calc_bmr(w, h, age, g)
        self.tdee = calc_tdee(self.bmr, act)
        self.total_cal.set(
            sum(cal for _, _, cal in load_today_entries(self.user_id))
        )

        messagebox.showinfo(
            self.T["title"],
            f"{self.T['bmr']}: {self.bmr:.0f} ккал\n"
            f"{self.T['tdee']}: {self.tdee:.0f} ккал/день"
        )
        self.load_entries_into_tab()

    def on_delete_user(self):
        idx = self.user_list.current()
        if idx < 0:
            messagebox.showwarning(self.T["title"], self.T["choose_user"])
            return
        if not messagebox.askyesno(
            self.T["title"], self.T["confirm_delete_user"]
        ):
            return

        uid = get_all_users()[idx][0]
        delete_user_db(uid)
        self.user_id = None
        self.refresh_user_list()
        if hasattr(self, "output"):
            self.output.delete("1.0", tk.END)
        self.total_cal.set(0)
        messagebox.showinfo(self.T["title"], self.T["user_deleted"])

    def register_user(self):
        try:
            g, w, h, a, act = (
                self.gender_var.get(), self.weight_var.get(),
                self.height_var.get(), self.age_var.get(),
                self.activity_var.get()
            )
        except tk.TclError:
            return messagebox.showerror(self.T["title"], self.T["invalid_data"])
        if not all([g, w, h, a, act]):
            return messagebox.showerror(self.T["title"], self.T["invalid_data"])

        uid = add_user(g, w, h, a, act)
        self.refresh_user_list()
        self.user_list.current(len(self.user_list['values']) - 1)
        self.select_user()

    # Tab for adding food entries
    def build_entry_tab(self):
        ff = ttk.LabelFrame(self.tab_entry, text=self.T["add_entry"])
        ff.pack(fill="x", pady=5)

        ttk.Label(ff, text=self.T["product_name"]) .grid(
            row=0, column=0, sticky="w")
        ttk.Entry(ff, textvariable=self.product_var) .grid(
            row=0, column=1, sticky="ew", padx=5)

        ttk.Label(ff, text=self.T["grams"]) .grid(
            row=1, column=0, sticky="w", pady=5)
        ttk.Entry(ff, textvariable=self.grams_var) .grid(
            row=1, column=1, sticky="ew", padx=5)

        ttk.Label(ff, text=self.T["cal100"]) .grid(
            row=2, column=0, sticky="w", pady=5)
        ttk.Entry(ff, textvariable=self.cal100_var) .grid(
            row=2, column=1, sticky="ew", padx=5)

        ff.columnconfigure(1, weight=1)
        ttk.Button(ff, text=self.T["add_product"],
                   command=self.add_product_entry
                   ).grid(row=3, column=0, columnspan=2, pady=10)

        hist = ttk.LabelFrame(self.tab_entry, text=self.T["total_calories"])
        hist.pack(fill="both", expand=True, pady=5)

        self.output = tk.Text(hist, height=10)
        self.output.pack(fill="both", expand=True, padx=5, pady=5)

        ttk.Label(hist,
                  textvariable=self.total_cal,
                  font=("Arial", 14, "bold")
                  ).pack(pady=5)

        # Show chart button
        ttk.Button(
            self.tab_entry,
            text="Show Chart",
            command=lambda: show_calorie_chart(self.user_id)
        ).pack(pady=5)

        self.load_entries_into_tab()

    def load_entries_into_tab(self):
        self.output.delete("1.0", tk.END)
        if self.user_id is None:
            self.total_cal.set(0)
            return

        rows = load_today_entries(self.user_id)
        total = 0
        for prod, grams, cal in rows:
            self.output.insert(
                tk.END,
                f"{prod}: {grams:.0f} г → {cal:.0f} ккал\n"
            )
            total += cal
        self.total_cal.set(total)

    def add_product_entry(self):
        if self.user_id is None:
            return messagebox.showerror(self.T["title"], self.T["choose_user"])

        prod = self.product_var.get()
        grams = self.grams_var.get()
        cal100 = self.cal100_var.get()
        if not prod or grams <= 0 or cal100 <= 0:
            return messagebox.showerror(self.T["title"], self.T["invalid_cal"])

        calories = grams * cal100 / 100
        add_entry(self.user_id, prod, grams, calories)

        self.product_var.set("")
        self.grams_var.set(0)
        self.cal100_var.set(0)
        self.load_entries_into_tab()


# Start the application
if __name__ == "__main__":
    root = tk.Tk()
    app = CalorieApp(root)
    root.mainloop()
