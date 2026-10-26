import tkinter as tk

def on_submit():
    name = name_entry.get()
    age = age_entry.get()
    email = email_entry.get()

    # TODO: validate name, age, and email before accepting them
    status_label.config(text="Registration successful!", fg="#2E9E6D")

root = tk.Tk()
root.title("Registration Form")
root.geometry("360x340")

tk.Label(root, text="Full Name").pack(pady=(16, 2))
name_entry = tk.Entry(root, width=30)
name_entry.pack()

tk.Label(root, text="Age").pack(pady=(12, 2))
age_entry = tk.Entry(root, width=30)
age_entry.pack()

tk.Label(root, text="Email").pack(pady=(12, 2))
email_entry = tk.Entry(root, width=30)
email_entry.pack()

tk.Button(root, text="Submit", command=on_submit).pack(pady=20)
status_label = tk.Label(root, text="")
status_label.pack()

root.mainloop()