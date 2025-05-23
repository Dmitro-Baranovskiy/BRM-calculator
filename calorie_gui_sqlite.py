
import tkinter as tk
from tkinter import messagebox
import sqlite3
from datetime import datetime

# ---------- БАЗА ДАНИХ ----------


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
        self.root.title("Калькулятор калорій з базою даних")
        self.root.geometry("400x650")

        init_db()
        self.user_id = None
        self.total_calories = 0

        self.build_user_form()

    def build_user_form(self):
        tk.Label(self.root, text="Стать (ч/ж):").pack()
        self.gender_var = tk.StringVar(value="ж")
        tk.Entry(self.root, textvariable=self.gender_var).pack()

        tk.Label(self.root, text="Вага (кг):").pack()
        self.weight_entry = tk.Entry(self.root)
        self.weight_entry.pack()

        tk.Label(self.root, text="Зріст (см):").pack()
        self.height_entry = tk.Entry(self.root)
        self.height_entry.pack()

        tk.Label(self.root, text="Вік:").pack()
        self.age_entry = tk.Entry(self.root)
        self.age_entry.pack()

        tk.Label(self.root, text="Активність:").pack()
        self.activity_var = tk.StringVar(value="сидячий")
        tk.Entry(self.root, textvariable=self.activity_var).pack()

        tk.Button(self.root, text="Почати",
                  command=self.register_user).pack(pady=10)

        self.result_label = tk.Label(self.root, text="")
        self.result_label.pack()

    def register_user(self):
        try:
            gender = self.gender_var.get()
            weight = float(self.weight_entry.get())
            height = float(self.height_entry.get())
            age = int(self.age_entry.get())
            activity = self.activity_var.get()

            self.user_id = add_user(gender, weight, height, age, activity)
            self.result_label.config(
                text=f"Користувач створений (ID: {self.user_id})")
            self.build_entry_form()
        except ValueError:
            messagebox.showerror("Помилка", "Невірні дані користувача.")

    def build_entry_form(self):
        tk.Label(self.root, text="Назва продукту:").pack()
        self.product_name = tk.StringVar()
        tk.Entry(self.root, textvariable=self.product_name).pack()

        tk.Label(self.root, text="Калорії:").pack()
        self.product_calories = tk.StringVar()
        tk.Entry(self.root, textvariable=self.product_calories).pack()

        tk.Button(self.root, text="Додати продукт",
                  command=self.add_product_entry).pack(pady=5)

        self.output = tk.Text(self.root, height=10, width=40)
        self.output.pack()

        self.total_label = tk.Label(
            self.root, text="Загальна кількість калорій: 0")
        self.total_label.pack()

    def add_product_entry(self):
        if not self.user_id:
            messagebox.showerror("Помилка", "Спочатку зареєструй користувача.")
            return
        try:
            name = self.product_name.get()
            cal = float(self.product_calories.get())
            add_product(self.user_id, name, cal)
            self.total_calories += cal
            self.output.insert(tk.END, f"{name}: {cal} ккал\n")
            self.total_label.config(
                text=f"Загальна кількість калорій: {self.total_calories}")
            self.product_name.set("")
            self.product_calories.set("")
        except ValueError:
            messagebox.showerror("Помилка", "Невірна кількість калорій.")


if __name__ == "__main__":
    root = tk.Tk()
    app = CalorieApp(root)
    root.mainloop()
