import os.path
import datetime
import pickle
import sys
import smtplib
import tkinter as tk
import sqlite3

import cv2
from PIL import Image, ImageTk
import face_recognition

import util


class App:
    def __init__(self):
        self.sql_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.present = set()
        self.counter = 0
        self.main_window = tk.Tk(className = " Attendance Tracker")
        self.main_window.geometry("1200x800+150+50")

        self.track_button_main_window = util.get_button(self.main_window, 'Start Attendance', 'gray', self.add_webcam, fg='black')
        self.track_button_main_window.place(x=80, y=720)

        self.stop_button_main_window = util.get_button(self.main_window, 'Stop Attendance', 'gray', self.stop_tracking, fg='black')
        self.stop_button_main_window.place(x=480, y=720)

        self.webcam_label = util.get_img_label(self.main_window)
        self.webcam_label.place(x=10, y=0, width=1180, height=700)
        self.db_dir = './db'
        if not os.path.exists(self.db_dir):
            os.mkdir(self.db_dir)

    def add_webcam(self):
        if 'cap' not in self.__dict__:
            self.cap = cv2.VideoCapture(0)
        self._label = self.webcam_label
        util.msg_box('Attendance Tracker has Started!', 'A message will be displayed when you are marked present!')
        self.communiacte()
    def communiacte(self):
        text = ("how much time (in minutes) before you want "
                "to mark people as late? write in the box below then press Enter")
        label = tk.Label(self.main_window, text=text,
                         background="green",
                         foreground="white")
        label.place(anchor="n", relx=.5, y=10)
        box_input = tk.Text(self.main_window, height=1, width=49)
        box_input.place(anchor="n", relx=.5, y=40)
        self.main_window.bind('<Return>', lambda event: self.setup_recording(event, label, box_input))

    def setup_recording(self, event, label, box_input):
        self.late_time = int(box_input.get("1.0", 'end-1c'))
        self.main_window.unbind('<Return>')
        box_input.after(10, box_input.destroy)
        label.after(10, label.destroy)
        self.register_new_user_button_main_window = util.get_button(self.main_window, 'Register New User', 'gray',
                                                                    self.register_new_user, fg='black')
        self.register_new_user_button_main_window.place(x=880, y=720)
        self.start_tracking()


    def start_tracking(self):

        ret, frame = self.cap.read()
        self.counter +=1
        self.most_recent_capture_arr = frame
        img_ = cv2.cvtColor(self.most_recent_capture_arr, cv2.COLOR_BGR2RGB)
        self.most_recent_capture_pil = Image.fromarray(img_)
        imgtk = ImageTk.PhotoImage(image=self.most_recent_capture_pil)
        self._label.imgtk = imgtk
        self._label.configure(image=imgtk)
        if self.counter % 20 == 0:
            name = util.recognize(self.most_recent_capture_arr, self.db_dir)
            if name not in ['unknown_person', 'no_persons_found', "marked"]:
                util.show_message(self.main_window, "Hello, " + name + "!")
                self.present.add(name)
                if self.counter / 300 > self.late_time:
                    self.handle_emails(name, "L")
                    self.log_sql(name, "L")
                else:
                    self.log_sql(name, "P")
        self._label.after(20, self.start_tracking)

    def stop_tracking(self):
        self.mark_absent()
        util.msg_box('Goodbye!', 'Thank you for using Attendance Tracker! Hope you had a wonderful class')
        sys.exit(0)

    def mark_absent(self):
        db_dir = sorted(os.listdir(self.db_dir))
        j = 0
        while j < len(db_dir):
            name = db_dir[j][:-7]
            if name not in self.present:
                self.handle_emails(name, "A")
                self.log_sql(name, "A")
            j += 1
    def register_new_user(self):
        self.register_new_user_window = tk.Toplevel(self.main_window)
        self.register_new_user_window.geometry("1200x620+370+120")

        self.accept_button_register_new_user_window = util.get_button(self.register_new_user_window, 'Accept', 'gray',
                                                                      self.accept_register_new_user, fg="black")
        self.accept_button_register_new_user_window.place(x=750, y=300)

        self.try_again_button_register_new_user_window = util.get_button(self.register_new_user_window, 'Try again', 'gray',
                                                                         self.try_again_register_new_user, fg= "black")
        self.try_again_button_register_new_user_window.place(x=750, y=400)

        self.capture_label = util.get_img_label(self.register_new_user_window)
        self.capture_label.place(x=10, y=0, width=700, height=620)

        self.add_img_to_label(self.capture_label)

        self.entry_text_register_new_user_name = util.get_entry_text(self.register_new_user_window)
        self.entry_text_register_new_user_name.place(x=750, y=140)

        self.text_label_register_new_user_name = util.get_text_label(self.register_new_user_window, 'Please, input username:')
        self.text_label_register_new_user_name.place(x=750, y=100)

        self.entry_text_register_new_user_email = util.get_entry_text(self.register_new_user_window)
        self.entry_text_register_new_user_email.place(x=750, y=240)

        self.text_label_register_new_user_email = util.get_text_label(self.register_new_user_window,'Please, input email address:')
        self.text_label_register_new_user_email.place(x=750, y=200)


    def try_again_register_new_user(self):
        self.register_new_user_window.destroy()


    def add_img_to_label(self, label):
        imgtk = ImageTk.PhotoImage(image=self.most_recent_capture_pil)
        label.imgtk = imgtk
        label.configure(image=imgtk)

        self.register_new_user_capture = self.most_recent_capture_arr.copy()


    def start(self):
        self.main_window.mainloop()


    def accept_register_new_user(self):
        name = self.entry_text_register_new_user_name.get(1.0, "end-1c").strip()
        email = self.entry_text_register_new_user_email.get(1.0, "end-1c").strip()
        self.create_sql_emails(name,email)

        embeddings = face_recognition.face_encodings(self.register_new_user_capture)[0]

        file = open(os.path.join(self.db_dir, '{}.pickle'.format(name)), 'wb')
        pickle.dump(embeddings, file)

        util.msg_box('Success!', 'User was registered successfully !')

        self.register_new_user_window.destroy()

    def handle_emails(self, name, status):
        conn = sqlite3.connect('emails.db')
        cur = conn.cursor()
        cur.execute('SELECT * FROM contacts')
        rows = cur.fetchall()
        conn.close()
        for row in rows:
            if row[0] == name:
                sender_email = "salman.aji802@gmail.com"
                reciever_email = row[1]
                if status == "A":
                    subject = "Attendance Alert: Missed Class"
                    message = ("Dear " + name + ",\nWe noticed you were absent for the class on " + self.sql_name.split("_")[0] + ". Regular attendance "
                    "is essential for your academic success. \nBest, \nSalman")
                if status == "L":
                    subject = "Attendance Alert: Late Class"
                    message = ("Dear " + name + ",\nWe noticed you were late for the class on" +
                               self.sql_name.split("_")[0] + ". Timely attendance "
                                                             "is essential for your academic success. \nBest, \nSalman")


                text = f"Subject: {subject}\n\n{message}"

                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()

                server.login(sender_email, "rvxgzmzyycljznwz")
                server.sendmail(sender_email,reciever_email,text)

    def create_sql_emails(self, name, email):
        conn = sqlite3.connect('emails.db')
        cur = conn.cursor()
        cur.execute('''
                    CREATE TABLE IF NOT EXISTS contacts (
                        name TEXT NOT NULL,
                        email TEXT NOT NULL
                    )
                    ''')
        conn.commit()
        conn.close()
        conn = sqlite3.connect('emails.db')
        cur = conn.cursor()
        cur.execute('INSERT INTO contacts (name, email) VALUES (?, ?)', (name, email))
        conn.commit()
        conn.close()

    def log_sql(self, name, status):
        date_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S").split("_")
        date = date_time[0]
        if status == "A":
            time = "NA"
        else:
            time = date_time[1]
        conn = sqlite3.connect("attendance log/" + self.sql_name)
        cur = conn.cursor()
        cur.execute('''
                    CREATE TABLE IF NOT EXISTS contacts (
                        name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        date TEXT NOT NULL,
                        arrival_time TEXT NOT NULL
                    )
                    ''')
        conn.commit()
        conn.close()
        conn = sqlite3.connect("attendance log/" + self.sql_name)
        cur = conn.cursor()
        cur.execute('INSERT INTO contacts (name, status, date, arrival_time) VALUES (?, ?, ?, ?)', (name, status, date, time))
        conn.commit()
        conn.close()


if __name__ == "__main__":
    app = App()
    app.start()
