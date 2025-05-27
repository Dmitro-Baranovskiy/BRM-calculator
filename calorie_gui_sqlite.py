#!/bin/python

import tkinter as tk
from tkinter import messagebox
import sqlite3
import json
import os
from datetime import datetime

# ---------- I18N ----------


def load_translations(lang="uk"):
    with open(os.path.join("locales", f"{lang}.json"), "r", encoding="utf-8") as f:
        return json.load(f)

# ---------- database ----------


def init_db():
    conn = sqlite3.connect("calories.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gender TEXT,
        weight REAL,
        height REAL,
        age INTEGER,
        activity TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product TEXT,
        calories REAL,
        date TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()


def add_user(gender, weight, height, age, activity):
    conn = sqlite3.connect("calories.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (gender, weight, height, age, activity) VALUES (?, ?, ?, ?, ?)",
                   (gender, weight, height, age, activity))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def get_all_users():
    conn = sqlite3.connect("calories.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, gender, weight, height, age, activity FROM users")
    users = cursor.fetchall()
    conn.close()
    return users


def add_product(user_id, product, calories):
    conn = sqlite3.connect("calories.db")
    cursor = conn.cursor()
    date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO entries (user_id, product, calories, date) VALUES (?, ?, ?, ?)",
                   (user_id, product, calories, date))
    conn.commit()
    conn.close()

# ---------- GUI ----------


class CalorieApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Calorie App")
        self.root.geometry("400x750")

        self.language = "uk"
        self.T = load_translations(self.language)

        init_db()
        self.user_id = None
        self.total_calories = 0

        self.build_language_switcher()
        self.build_user_selector()

    def build_language_switcher(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=5)
        tk.Label(frame, text="🌐 Language:").pack(side=tk.LEFT)
        tk.Button(frame, text="Українська",
                  command=lambda: self.switch_language("uk")).pack(side=tk.LEFT)
        tk.Button(frame, text="English", command=lambda: self.switch_language(
            "en")).pack(side=tk.LEFT)

    def switch_language(self, lang):
        self.language = lang
        self.T = load_translations(lang)
        self.clear_gui()
        self.build_language_switcher()
        self.build_user_selector()

    def clear_gui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def build_user_selector(self):
        tk.Label(self.root, text=self.T["title"], font=(
            "Arial", 16, "bold")).pack(pady=10)
        tk.Label(self.root, text=self.T["choose_user"]).pack()

        self.user_list = tk.Listbox(self.root, height=6)
        self.user_list.pack()
        self.load_users()

        tk.Button(self.root, text=self.T["select_user"],
                  command=self.select_user).pack(pady=5)
        tk.Button(self.root, text=self.T["create_user"],
                  command=self.build_user_form).pack(pady=5)

        self.result_label = tk.Label(self.root, text="")
        self.result_label.pack()

    def load_users(self):
        self.user_list.delete(0, tk.END)
        users = get_all_users()
        for user in users:
            label = f"ID {user[0]}: {user[1]}, {user[2]}кг, {user[4]} років"
            self.user_list.insert(tk.END, label)

    def select_user(self):
        selection = self.user_list.curselection()
        if selection:
            index = selection[0]
            user_data = get_all_users()[index]
            self.user_id = user_data[0]
            self.result_label.config(text=f"ID: {self.user_id}")
            self.clear_gui()
            self.build_language_switcher()
            self.build_entry_form()
        else:
            messagebox.showwarning("!", self.T["select_user"])

    def build_user_form(self):
        self.clear_gui()
        self.build_language_switcher()

        tk.Label(self.root, text=self.T["title"], font=(
            "Arial", 16, "bold")).pack(pady=10)
        tk.Label(self.root, text=self.T["gender"]).pack()
        self.gender_var = tk.StringVar(value="ж")
        tk.Entry(self.root, textvariable=self.gender_var).pack()

        tk.Label(self.root, text=self.T["weight"]).pack()
        self.weight_entry = tk.Entry(self.root)
        self.weight_entry.pack()

        tk.Label(self.root, text=self.T["height"]).pack()
        self.height_entry = tk.Entry(self.root)
        self.height_entry.pack()

        tk.Label(self.root, text=self.T["age"]).pack()
        self.age_entry = tk.Entry(self.root)
        self.age_entry.pack()

        tk.Label(self.root, text=self.T["activity"]).pack()
        self.activity_var = tk.StringVar(value="сидячий")
        tk.Entry(self.root, textvariable=self.activity_var).pack()

        tk.Button(self.root, text=self.T["save_user"],
                  command=self.register_user).pack(pady=10)

    def register_user(self):
        try:
            gender = self.gender_var.get()
            weight = float(self.weight_entry.get())
            height = float(self.height_entry.get())
            age = int(self.age_entry.get())
            activity = self.activity_var.get()

            self.user_id = add_user(gender, weight, height, age, activity)
            self.result_label.config(text=f"ID: {self.user_id}")
            self.clear_gui()
            self.build_language_switcher()
            self.build_entry_form()
        except ValueError:
            messagebox.showerror("!", "Дані невалідні!")

    def build_entry_form(self):
        tk.Label(self.root, text=self.T["product_name"]).pack()
        self.product_name = tk.StringVar()
        tk.Entry(self.root, textvariable=self.product_name).pack()

        tk.Label(self.root, text=self.T["calories"]).pack()
        self.product_calories = tk.StringVar()
        tk.Entry(self.root, textvariable=self.product_calories).pack()

        tk.Button(self.root, text=self.T["add_product"],
                  command=self.add_product_entry).pack(pady=5)

        self.output = tk.Text(self.root, height=10, width=40)
        self.output.pack()

        self.total_label = tk.Label(
            self.root, text=f"{self.T['total_calories']} 0")
        self.total_label.pack()

    def add_product_entry(self):
        if not self.user_id:
            messagebox.showerror("!", "Обери користувача!")
            return
        try:
            name = self.product_name.get()
            cal = float(self.product_calories.get())
            add_product(self.user_id, name, cal)
            self.total_calories += cal
            self.output.insert(tk.END, f"{name}: {cal} ккал\n")
            self.total_label.config(
                text=f"{self.T['total_calories']} {self.total_calories}")
            self.product_name.set("")
            self.product_calories.set("")
        except ValueError:
            messagebox.showerror("!", "Помилка вводу калорій.")


if __name__ == "__main__":
    root = tk.Tk()
    app = CalorieApp(root)
    root.mainloop()
