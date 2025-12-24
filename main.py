import json
from tkinter import *
from tkinter import messagebox

TASKS_FILE = "tasks.json"
WISHES_FILE = "wishes.json"


# -----------------------------
# Models
# -----------------------------
class Task:
    def __init__(
        self,
        id,
        title,
        description,
        points,
        status="PENDING",
        rating=None,
        reviewed_by=None,
        created_by=None,
    ):
        self.id = id
        self.title = title
        self.description = description
        self.points = int(points)
        self.status = status
        self.rating = rating
        self.reviewed_by = reviewed_by
        self.created_by = created_by

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "points": self.points,
            "status": self.status,
            "rating": self.rating,
            "reviewed_by": self.reviewed_by,
            "created_by": self.created_by,
        }

    @staticmethod
    def from_dict(d):
        return Task(
            d.get("id", ""),
            d.get("title", ""),
            d.get("description", ""),
            d.get("points", 0),
            d.get("status", "PENDING"),
            d.get("rating", None),
            d.get("reviewed_by", None),
            d.get("created_by", None),
        )


class Wish:
    def __init__(self, id, name, min_level, status="PENDING"):
        self.id = id
        self.name = name
        self.min_level = int(min_level)
        self.status = status  # PENDING / APPROVED / REJECTED

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "min_level": self.min_level,
            "status": self.status,
        }

    @staticmethod
    def from_dict(d):
        return Wish(
            d.get("id", ""),
            d.get("name", ""),
            d.get("min_level", 1),
            d.get("status", "PENDING"),
        )


# -----------------------------
# Storage
# -----------------------------
class StorageService:
    @staticmethod
    def load_json(path, default):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    @staticmethod
    def save_json(path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)


# -----------------------------
# App
# -----------------------------
class KidTaskApp:
    def __init__(self):
        self.root = Tk()
        self.root.title("KidTask")
        self.root.geometry("900x560")

        self.tasks = []
        self.wishes = []
        self.load_data()

        self.child_points = 0
        self.child_level = 1

        self.header = Frame(self.root)
        self.header.pack(fill=X, pady=6)

        self.navbar = Frame(self.root)
        self.navbar.pack(fill=X, pady=4)

        self.content = Frame(self.root)
        self.content.pack(fill=BOTH, expand=True)

        self.current_role = None
        self.show_role_selection()

        self.root.mainloop()

    # ---------- data ----------
    def load_data(self):
        tdata = StorageService.load_json(TASKS_FILE, [])
        wdata = StorageService.load_json(WISHES_FILE, [])
        self.tasks = [Task.from_dict(x) for x in tdata]
        self.wishes = [Wish.from_dict(x) for x in wdata]

    def save_data(self):
        StorageService.save_json(TASKS_FILE, [t.to_dict() for t in self.tasks])
        StorageService.save_json(WISHES_FILE, [w.to_dict() for w in self.wishes])

    # ---------- helpers ----------
    def clear_frame(self, frame):
        for w in frame.winfo_children():
            w.destroy()

    def clear_all(self):
        self.clear_frame(self.header)
        self.clear_frame(self.navbar)
        self.clear_frame(self.content)

    def set_header(self, title):
        self.clear_frame(self.header)
        Label(self.header, text=title, font=("Arial", 18, "bold")).pack(pady=4)

    def set_nav(self, buttons):
        self.clear_frame(self.navbar)
        for text, cmd in buttons:
            Button(self.navbar, text=text, width=20, command=cmd).pack(side=LEFT, padx=4)
        Button(self.navbar, text="Switch Role", width=14, command=self.show_role_selection).pack(
            side=RIGHT, padx=4
        )

    def recalc_progress(self):
        self.child_points = sum(t.points for t in self.tasks if t.status == "APPROVED")
        self.child_level = 1 + (self.child_points // 50)

    def next_task_id(self):
        nums = []
        for t in self.tasks:
            if isinstance(t.id, str) and t.id.startswith("t"):
                try:
                    nums.append(int(t.id[1:]))
                except ValueError:
                    pass
        return f"t{(max(nums) + 1) if nums else 1}"

    def next_wish_id(self):
        nums = []
        for w in self.wishes:
            if isinstance(w.id, str) and w.id.startswith("w"):
                try:
                    nums.append(int(w.id[1:]))
                except ValueError:
                    pass
        return f"w{(max(nums) + 1) if nums else 1}"

    # -----------------------------
    # Role Selection
    # -----------------------------
    def show_role_selection(self):
        self.clear_all()
        self.set_header("KidTask – Select Role")

        box = Frame(self.content)
        box.pack(pady=40)

        Label(box, text="Choose your role:", font=("Arial", 14)).pack(pady=10)

        def choose(role):
            self.current_role = role
            self.show_dashboard()

        Button(box, text="Child", width=30, command=lambda: choose("Child")).pack(pady=6)
        Button(box, text="Parent", width=30, command=lambda: choose("Parent")).pack(pady=6)
        Button(box, text="Teacher", width=30, command=lambda: choose("Teacher")).pack(pady=6)

    # -----------------------------
    # Dashboard (role-based)
    # -----------------------------
    def show_dashboard(self):
        self.clear_all()
        self.set_header(f"KidTask Dashboard – {self.current_role}")

        if self.current_role == "Child":
            self.set_nav(
                [
                    ("Tasks", self.show_tasks),
                    ("Wishes", self.show_wishes),
                    ("Progress", self.show_progress),
                ]
            )
            self.show_tasks()
        else:
            # Parent/Teacher
            self.set_nav(
                [
                    ("Review Tasks", self.show_reviews),
                    ("Add Task", self.add_task_dialog_for_parent),
                    ("Review Wishes", self.show_wish_reviews),  # NEW
                    ("Progress (Child)", self.show_progress),
                ]
            )
            self.show_reviews()

    # -----------------------------
    # Child: Tasks
    # -----------------------------
    def show_tasks(self):
        if self.current_role != "Child":
            messagebox.showinfo("Info", "Tasks screen is available for Child role.")
            return

        self.clear_frame(self.content)

        top = Frame(self.content)
        top.pack(fill=X, pady=6)
        Label(top, text="Tasks", font=("Arial", 14, "bold")).pack(side=LEFT, padx=8)

        self.tasks_list = Listbox(self.content, height=16)
        self.tasks_list.pack(fill=BOTH, expand=True, padx=10, pady=6)

        for t in self.tasks:
            extra = ""
            if t.created_by:
                extra += f" | by {t.created_by}"
            if t.status == "APPROVED" and t.rating is not None:
                extra += f" | rating={t.rating} by {t.reviewed_by}"
            self.tasks_list.insert(END, f"[{t.status}] {t.title} - {t.points} pts{extra}")

        btns = Frame(self.content)
        btns.pack(pady=6)

        Button(
            btns,
            text="Mark Selected as COMPLETED_PENDING_REVIEW",
            command=self.mark_task_completed,
            width=46,
        ).pack()

        Label(
            self.content,
            text="Tip: After marking completed, switch to Parent/Teacher to approve & rate.",
            font=("Arial", 10, "italic"),
        ).pack(pady=4)

    def mark_task_completed(self):
        sel = self.tasks_list.curselection() if hasattr(self, "tasks_list") else ()
        if not sel:
            messagebox.showinfo("Info", "Select a task first.")
            return

        idx = sel[0]
        task = self.tasks[idx]

        if task.status == "APPROVED":
            messagebox.showinfo("Info", "This task is already APPROVED.")
            return

        task.status = "COMPLETED_PENDING_REVIEW"
        task.rating = None
        task.reviewed_by = None
        self.save_data()
        self.show_tasks()
        messagebox.showinfo("Done", "Task is now COMPLETED_PENDING_REVIEW.")

    # -----------------------------
    # Child: Wishes
    # -----------------------------
    def show_wishes(self):
        if self.current_role != "Child":
            messagebox.showinfo("Info", "Wishes screen is available for Child role.")
            return

        self.clear_frame(self.content)

        top = Frame(self.content)
        top.pack(fill=X, pady=6)
        Label(top, text="Wishes", font=("Arial", 14, "bold")).pack(side=LEFT, padx=8)
        Button(top, text="Add Wish", command=self.add_wish_dialog).pack(side=RIGHT, padx=8)

        self.wishes_list = Listbox(self.content, height=16)
        self.wishes_list.pack(fill=BOTH, expand=True, padx=10, pady=6)

        self.recalc_progress()
        for w in self.wishes:
            visible = self.child_level >= w.min_level
            tag = "VISIBLE" if visible else "LOCKED"
            self.wishes_list.insert(
                END, f"[{w.status}] {w.name} (min level {w.min_level}) -> {tag}"
            )

        Label(
            self.content,
            text=f"Current child level = {self.child_level}. Wishes with minLevel > level are LOCKED.",
            font=("Arial", 10, "italic"),
        ).pack(pady=4)

    def add_wish_dialog(self):
        win = Toplevel(self.root)
        win.title("Add Wish")

        Label(win, text="Wish name:").grid(row=0, column=0, sticky="w", pady=4, padx=6)
        e_name = Entry(win, width=34)
        e_name.grid(row=0, column=1, pady=4, padx=6)

        Label(win, text="Min level:").grid(row=1, column=0, sticky="w", pady=4, padx=6)
        e_lvl = Entry(win, width=12)
        e_lvl.grid(row=1, column=1, sticky="w", pady=4, padx=6)

        def save():
            name = e_name.get().strip()
            if not name:
                messagebox.showerror("Error", "Wish name is required.")
                return
            try:
                lvl = int(e_lvl.get())
            except ValueError:
                messagebox.showerror("Error", "Min level must be an integer.")
                return

            new_id = self.next_wish_id()
            self.wishes.append(Wish(new_id, name, lvl, status="PENDING"))
            self.save_data()
            win.destroy()
            self.show_wishes()

        Button(win, text="Save", command=save, width=18).grid(row=2, column=0, columnspan=2, pady=10)

    # -----------------------------
    # Parent/Teacher: Add Task
    # -----------------------------
    def add_task_dialog_for_parent(self):
        if self.current_role not in ("Parent", "Teacher"):
            messagebox.showinfo("Info", "Only Parent/Teacher can add tasks here.")
            return
        self.add_task_dialog(created_by=self.current_role)

    def add_task_dialog(self, created_by=None):
        win = Toplevel(self.root)
        win.title("Add Task")

        Label(win, text="Title:").grid(row=0, column=0, sticky="w", pady=4, padx=6)
        e_title = Entry(win, width=34)
        e_title.grid(row=0, column=1, pady=4, padx=6)

        Label(win, text="Description:").grid(row=1, column=0, sticky="w", pady=4, padx=6)
        e_desc = Entry(win, width=34)
        e_desc.grid(row=1, column=1, pady=4, padx=6)

        Label(win, text="Points:").grid(row=2, column=0, sticky="w", pady=4, padx=6)
        e_points = Entry(win, width=12)
        e_points.grid(row=2, column=1, sticky="w", pady=4, padx=6)

        def save():
            title = e_title.get().strip()
            desc = e_desc.get().strip()
            if not title:
                messagebox.showerror("Error", "Title is required.")
                return
            try:
                pts = int(e_points.get())
            except ValueError:
                messagebox.showerror("Error", "Points must be an integer.")
                return

            new_id = self.next_task_id()
            self.tasks.append(
                Task(new_id, title, desc, pts, status="PENDING", created_by=created_by)
            )
            self.save_data()
            win.destroy()
            self.show_reviews()

        Button(win, text="Save", command=save, width=18).grid(row=3, column=0, columnspan=2, pady=10)

    # -----------------------------
    # Parent/Teacher: Task Reviews
    # -----------------------------
    def show_reviews(self):
        if self.current_role not in ("Parent", "Teacher"):
            messagebox.showinfo("Info", "Review screen is for Parent/Teacher roles.")
            return

        self.clear_frame(self.content)

        top = Frame(self.content)
        top.pack(fill=X, pady=6)
        Label(top, text="Task Reviews", font=("Arial", 14, "bold")).pack(side=LEFT, padx=8)

        pending = [t for t in self.tasks if t.status == "COMPLETED_PENDING_REVIEW"]

        self.review_list = Listbox(self.content, height=14)
        self.review_list.pack(fill=BOTH, expand=True, padx=10, pady=6)

        for t in pending:
            self.review_list.insert(END, f"[{t.status}] {t.title} - {t.points} pts (id={t.id})")

        controls = Frame(self.content)
        controls.pack(fill=X, padx=10, pady=6)

        Label(controls, text="Rating (1-5):").pack(side=LEFT)
        self.rating_var = StringVar(value="5")
        Entry(controls, textvariable=self.rating_var, width=6).pack(side=LEFT, padx=6)

        Button(controls, text="Approve Selected", command=self.approve_selected_task, width=20).pack(side=LEFT, padx=6)
        Button(controls, text="Refresh", command=self.show_reviews, width=12).pack(side=LEFT, padx=6)

        if not pending:
            Label(self.content, text="No tasks pending review.", font=("Arial", 11, "italic")).pack(pady=10)

    def approve_selected_task(self):
        sel = self.review_list.curselection() if hasattr(self, "review_list") else ()
        if not sel:
            messagebox.showinfo("Info", "Select a task first.")
            return

        pending = [t for t in self.tasks if t.status == "COMPLETED_PENDING_REVIEW"]
        idx = sel[0]
        if idx < 0 or idx >= len(pending):
            messagebox.showerror("Error", "Invalid selection.")
            return
        task = pending[idx]

        try:
            rating = int(self.rating_var.get())
        except ValueError:
            messagebox.showerror("Error", "Rating must be an integer 1-5.")
            return
        if rating < 1 or rating > 5:
            messagebox.showerror("Error", "Rating must be between 1 and 5.")
            return

        task.status = "APPROVED"
        task.rating = rating
        task.reviewed_by = self.current_role
        self.save_data()
        self.show_reviews()
        messagebox.showinfo("Approved", f"Task approved with rating {rating}.")

    # -----------------------------
    # Parent/Teacher: Wish Reviews (NEW)
    # -----------------------------
    def show_wish_reviews(self):
        if self.current_role not in ("Parent", "Teacher"):
            messagebox.showinfo("Info", "Wish review is for Parent/Teacher roles.")
            return

        self.clear_frame(self.content)

        top = Frame(self.content)
        top.pack(fill=X, pady=6)
        Label(top, text="Wish Reviews", font=("Arial", 14, "bold")).pack(side=LEFT, padx=8)

        self.wish_review_list = Listbox(self.content, height=14)
        self.wish_review_list.pack(fill=BOTH, expand=True, padx=10, pady=6)

        for w in self.wishes:
            self.wish_review_list.insert(
                END, f"[{w.status}] {w.name} (min level {w.min_level}) (id={w.id})"
            )

        controls = Frame(self.content)
        controls.pack(fill=X, padx=10, pady=6)

        Button(controls, text="Approve Selected", width=18, command=self.approve_selected_wish).pack(side=LEFT, padx=6)
        Button(controls, text="Reject Selected", width=18, command=self.reject_selected_wish).pack(side=LEFT, padx=6)
        Button(controls, text="Refresh", width=12, command=self.show_wish_reviews).pack(side=LEFT, padx=6)

        if not self.wishes:
            Label(self.content, text="No wishes created yet.", font=("Arial", 11, "italic")).pack(pady=10)

        Label(
            self.content,
            text="Tip: Child creates wishes as PENDING. Parent/Teacher can APPROVE or REJECT them here.",
            font=("Arial", 10, "italic"),
        ).pack(pady=6)

    def approve_selected_wish(self):
        sel = self.wish_review_list.curselection() if hasattr(self, "wish_review_list") else ()
        if not sel:
            messagebox.showinfo("Info", "Select a wish first.")
            return
        idx = sel[0]
        if idx < 0 or idx >= len(self.wishes):
            messagebox.showerror("Error", "Invalid selection.")
            return
        self.wishes[idx].status = "APPROVED"
        self.save_data()
        self.show_wish_reviews()
        messagebox.showinfo("Approved", "Wish approved.")

    def reject_selected_wish(self):
        sel = self.wish_review_list.curselection() if hasattr(self, "wish_review_list") else ()
        if not sel:
            messagebox.showinfo("Info", "Select a wish first.")
            return
        idx = sel[0]
        if idx < 0 or idx >= len(self.wishes):
            messagebox.showerror("Error", "Invalid selection.")
            return
        self.wishes[idx].status = "REJECTED"
        self.save_data()
        self.show_wish_reviews()
        messagebox.showinfo("Rejected", "Wish rejected.")

    # -----------------------------
    # Progress
    # -----------------------------
    def show_progress(self):
        self.recalc_progress()
        self.clear_frame(self.content)

        box = Frame(self.content)
        box.pack(pady=40)

        Label(box, text="Child Progress", font=("Arial", 16, "bold")).pack(pady=8)
        Label(box, text=f"Total Points (APPROVED): {self.child_points}", font=("Arial", 14)).pack(pady=4)
        Label(box, text=f"Level: {self.child_level}", font=("Arial", 14)).pack(pady=4)

        outer = Frame(box, width=420, height=24, bg="#dddddd")
        outer.pack(pady=16)
        outer.pack_propagate(False)

        remainder = self.child_points % 50
        pct = min(remainder / 50.0, 1.0)
        inner_w = int(420 * pct)
        inner = Frame(outer, width=inner_w, bg="#4caf50")
        inner.pack(side=LEFT, fill=Y)

        Label(box, text="Each 50 approved points increases level by 1.", font=("Arial", 10, "italic")).pack(pady=6)


if __name__ == "__main__":
    KidTaskApp()