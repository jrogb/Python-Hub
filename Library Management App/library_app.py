
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime, date

# Database setup
def init_db():
    conn = sqlite3.connect("library.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    quantity INTEGER NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS borrowed_books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_name TEXT NOT NULL,
                    book_id INTEGER,
                    borrow_date TEXT,
                    return_date TEXT,
                    fine REAL DEFAULT 0,
                    FOREIGN KEY(book_id) REFERENCES books(id))""")
    c.execute("SELECT COUNT(*) FROM books")
    if c.fetchone()[0] == 0:
        sample_books = [
            ("The Great Gatsby", 3),
            ("1984", 2),
            ("To Kill a Mockingbird", 4),
            ("Pride and Prejudice", 5),
            ("Moby Dick", 1)
        ]
        c.executemany("INSERT INTO books (title, quantity) VALUES (?, ?)", sample_books)
    c.execute("SELECT COUNT(*) FROM borrowed_books")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO borrowed_books (student_name, book_id, borrow_date, return_date, fine) VALUES (?, ?, ?, ?, ?)",
                  ("Alice", 1, "2024-04-01", "2024-04-05", 0))
        c.execute("INSERT INTO borrowed_books (student_name, book_id, borrow_date, return_date, fine) VALUES (?, ?, ?, ?, ?)",
                  ("Bob", 2, "2024-03-25", "2024-04-02", 15))
    conn.commit()
    conn.close()

def get_available_books():
    conn = sqlite3.connect("library.db")
    c = conn.cursor()
    c.execute("SELECT id, title FROM books WHERE quantity > 0")
    books = c.fetchall()
    conn.close()
    return books

def refresh_book_dropdown():
    book_combobox['values'] = [f"{book[0]} - {book[1]}" for book in get_available_books()]
    if book_combobox['values']:
        book_combobox.current(0)

def refresh_table():
    for row in tree.get_children():
        tree.delete(row)
    conn = sqlite3.connect("library.db")
    c = conn.cursor()
    query = """SELECT bb.id, bb.student_name, b.title, bb.borrow_date, bb.return_date, bb.fine
               FROM borrowed_books bb
               JOIN books b ON bb.book_id = b.id"""
    c.execute(query)
    rows = c.fetchall()
    for row in rows:
        tag = 'fine' if row[5] > 0 else ''
        tree.insert('', 'end', values=row, tags=(tag,))
    conn.close()
    update_record_count()

def add_record():
    student = student_entry.get().strip()
    book_info = book_combobox.get()
    borrow = borrow_date.get_date()
    return_ = return_date.get_date()
    if not student or not book_info:
        messagebox.showerror("Error", "Please fill all fields.")
        return
    if borrow < date.today():
        messagebox.showerror("Error", "Borrow date cannot be in the past.")
        return
    if return_ < borrow:
        messagebox.showerror("Error", "Return date cannot be before borrow date.")
        return
    book_id = int(book_info.split(" - ")[0])
    fine = 0
    if return_ < date.today():
        fine = (date.today() - return_).days * 5
    conn = sqlite3.connect("library.db")
    c = conn.cursor()
    c.execute("INSERT INTO borrowed_books (student_name, book_id, borrow_date, return_date, fine) VALUES (?, ?, ?, ?, ?)",
              (student, book_id, borrow.isoformat(), return_.isoformat(), fine))
    c.execute("UPDATE books SET quantity = quantity - 1 WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    refresh_table()
    refresh_book_dropdown()
    clear_fields()

def delete_record():
    selected = tree.selection()
    if not selected:
        messagebox.showerror("Error", "No record selected.")
        return
    if not messagebox.askyesno("Confirm", "Are you sure you want to delete this record?"):
        return
    item = tree.item(selected)
    record_id = item['values'][0]
    book_title = item['values'][2]
    conn = sqlite3.connect("library.db")
    c = conn.cursor()
    c.execute("SELECT id FROM books WHERE title = ?", (book_title,))
    book_id = c.fetchone()[0]
    c.execute("DELETE FROM borrowed_books WHERE id = ?", (record_id,))
    c.execute("UPDATE books SET quantity = quantity + 1 WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()
    refresh_table()
    refresh_book_dropdown()

def clear_fields():
    student_entry.delete(0, tk.END)
    borrow_date.set_date(date.today())
    return_date.set_date(date.today())

def filter_table(*args):
    search_term = search_var.get().lower()
    for row in tree.get_children():
        tree.delete(row)
    conn = sqlite3.connect("library.db")
    c = conn.cursor()
    query = """SELECT bb.id, bb.student_name, b.title, bb.borrow_date, bb.return_date, bb.fine
               FROM borrowed_books bb
               JOIN books b ON bb.book_id = b.id
               WHERE LOWER(bb.student_name) LIKE ? OR LOWER(b.title) LIKE ?"""
    c.execute(query, (f"%{search_term}%", f"%{search_term}%"))
    rows = c.fetchall()
    for row in rows:
        tag = 'fine' if row[5] > 0 else ''
        tree.insert('', 'end', values=row, tags=(tag,))
    conn.close()
    update_record_count()

def update_record_count():
    count_label.config(text=f"Total Records: {len(tree.get_children())}")

# Initialize DB
init_db()

# GUI setup
root = tk.Tk()
root.title("Library Management System v1.0.0")

form_frame = ttk.LabelFrame(root, text="Borrow Book")
form_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

tk.Label(form_frame, text="Student Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
student_entry = tk.Entry(form_frame)
student_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(form_frame, text="Book:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
book_combobox = ttk.Combobox(form_frame, state="readonly", width=30)
book_combobox.grid(row=1, column=1, padx=5, pady=5)

tk.Label(form_frame, text="Borrow Date:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
borrow_date = DateEntry(form_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
borrow_date.set_date(date.today())
borrow_date.grid(row=2, column=1, padx=5, pady=5)

tk.Label(form_frame, text="Return Date:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
return_date = DateEntry(form_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
return_date.set_date(date.today())
return_date.grid(row=3, column=1, padx=5, pady=5)

btn_frame = tk.Frame(form_frame)
btn_frame.grid(row=4, column=0, columnspan=2, pady=10)

tk.Button(btn_frame, text="Add", bg="green", fg="white", command=add_record).grid(row=0, column=0, padx=5)
tk.Button(btn_frame, text="Delete", bg="red", fg="white", command=delete_record).grid(row=0, column=1, padx=5)
tk.Button(btn_frame, text="Clear", bg="grey", fg="white", command=clear_fields).grid(row=0, column=2, padx=5)

search_frame = tk.Frame(root)
search_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

tk.Label(search_frame, text="Search:").pack(side="left")
search_var = tk.StringVar()
search_var.trace("w", filter_table)
search_entry = tk.Entry(search_frame, textvariable=search_var)
search_entry.pack(side="left", padx=5)

count_label = tk.Label(search_frame, text="Total Records: 0")
count_label.pack(side="right")

tree_frame = tk.Frame(root)
tree_frame.grid(row=2, column=0, padx=10, pady=5)

columns = ("ID", "Student", "Book", "Borrow Date", "Return Date", "Fine")
tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center", width=100 if col != "ID" else 50)

tree.tag_configure('fine', background='red')
style = ttk.Style()
style.configure("Treeview.Heading", font=('Arial', 10, 'bold'), background='blue', foreground='white')
tree.pack(side="left", fill="both")

scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
tree.configure(yscroll=scrollbar.set)
scrollbar.pack(side="right", fill="y")

refresh_book_dropdown()
refresh_table()

root.mainloop()
