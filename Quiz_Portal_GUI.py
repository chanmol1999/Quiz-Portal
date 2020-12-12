import tkinter as tk
import os
import time
import pandas as pd
import datetime
import csv
import tkinter.font as TkFont
from tkinter.messagebox import *
from tkinter.filedialog import *
import sqlite3 as sq
import bcrypt


def get_hashed_password(plain_text_password):
    # Hash a password for the first time
    #   (Using bcrypt, the salt is saved into the hash itself)
    return bcrypt.hashpw(plain_text_password.encode('utf-8'), bcrypt.gensalt())


def check_password(plain_text_password, hashed_password):
    # Check hashed password. Using bcrypt, the salt is saved into the hash itself
    return bcrypt.checkpw(plain_text_password.encode('utf-8'), hashed_password.encode('utf-8'))


def countdown(quiz_data, top, time_label):
    global count
    mins, secs = divmod(count, 60)
    timer = '{:02d}:{:02d}'.format(mins, secs)
    if top.winfo_exists():
        time_label.config(text=timer)
    count -= 1
    if count > 0:
        # call countdown again after 1000ms (1s)
        root.after(1000, countdown, quiz_data, top, time_label)
    else:
        submit_quiz(quiz_data, top)


def quit(top):
    top.destroy()
    root.destroy()


def save_quiz_response(option_selected):
    global index, record_response
    if (option_selected.get()) in (['1', '2', '3', '4', '5']):
        record_response[index] = option_selected.get()


def next_question(quiz_data, top, question_label):
    # top.destroy()
    global index
    if index == len(quiz_data)-1:
        index = 0
    else:
        index = index+1
    # quiz_print(quiz_data)4
    update_quiz(question_label, quiz_data, top)


def previous_question(quiz_data, top, question_label):
    # top.destroy()
    global index
    if index == 0:
        index = len(quiz_data)-1
    else:
        index = index - 1
    # quiz_print(quiz_data)
    update_quiz(question_label, quiz_data, top)


def submit_quiz(quiz_data, top):
    # next_question(quiz_data,top,option_selected)
    if not top.winfo_exists():
        return
    global count, max_possible_score, total_score, individual_responses, correct_attempt, quiz_ques_attempt, wrong_attempt, login_db, original_quiz_file, roll
    count = 0
    top.destroy()
    total_score = 0
    quiz_ques_attempt = 0
    correct_attempt = 0
    wrong_attempt = 0
    for i in range(len(quiz_data)):
        ans = int(record_response[i])
        correct_ans = int((quiz_data['correct_option'][i]))
        if ans == 5 or ans == 0:
            ans = "Skipped"
        individual_responses.append([i+1, quiz_data['question'][i], quiz_data['option1'][i], quiz_data['option2'][i], quiz_data['option3'][i], quiz_data['option4']
                                     [i], quiz_data['correct_option'][i], quiz_data['marks_correct_ans'][i], quiz_data['marks_wrong_ans'][i], quiz_data['compulsory'][i], ans])
        if(ans == 'Skipped'):
            pass
        elif(correct_ans == ans):
            quiz_ques_attempt += 1
            correct_attempt += 1
            total_score += int(quiz_data['marks_correct_ans'][i])
        else:
            quiz_ques_attempt += 1
            wrong_attempt += 1
            total_score += int(quiz_data['marks_wrong_ans'][i])
    top = Toplevel(root)
    top.geometry('400x400')
    Label(top, text="Your quiz has been submitted", font=(
        'Helvetica', 16, 'bold')).place(relx=0.5, rely=0.1, anchor=CENTER)
    score_label = Label(top, text="Your score = "+str(total_score) +
                        '/'+str(max_possible_score), font=('Helvetica', 15, 'bold'))
    score_label.place(relx=0.5, rely=0.3, anchor=CENTER)
    Label(top, text="Correctly Attempted = " + str(correct_attempt),
          font=('Helvetica', 14, 'bold')).place(relx=0.5, rely=0.4, anchor=CENTER)
    Label(top, text="Total Quiz Questions = " + str(len(quiz_data)),
          font=('Helvetica', 14, 'bold')).place(relx=0.5, rely=0.5, anchor=CENTER)
    Label(top, text="Total wrong = " + str(wrong_attempt),
          font=('Helvetica', 14, 'bold')).place(relx=0.5, rely=0.6, anchor=CENTER)

    exit_label = Button(top, text="Exit")
    exit_label.place(relx=0.5, rely=0.8, anchor=CENTER)
    exit_label.config(command=lambda: quit(top))
    cur.execute('INSERT OR REPLACE INTO project1_marks values(?,?,?)',
                (roll, original_quiz_file, total_score))
    login_db.commit()
    cd = os.path.join(os.getcwd(), 'individual_responses')
    file_individual = os.path.join(cd, re.split(
        r'\.', original_quiz_file)[0]+'_'+roll+'.csv')
    with open(file_individual, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(['ques_no', 'question', 'option1', 'option2', 'option3', 'option4',
                         'correct_option', 'marks_correct_ans', 'marks_wrong_ans', 'compulsory', 'marked_choice'])
        writer.writerows(individual_responses)
    df = pd.read_csv(file_individual)
    df1 = {}
    df1['Total'] = [correct_attempt, wrong_attempt, len(
        quiz_data)-quiz_ques_attempt, total_score, max_possible_score]
    df1['Legend'] = ['Correct choices', 'Wrong choices',
                     'Unattempted', 'Marks Obtained', 'Total Quiz Marks']
    data_frame = pd.DataFrame(
        [df1['Total'], df1['Legend']], index=['Total', 'Legend']).T
    df_final = [df, data_frame]
    df_fin = pd.concat(df_final, axis=1)
    df_fin.set_index('ques_no', inplace=True)
    df_fin.to_csv(file_individual)

    quiz_file = os.listdir('quiz_wise_questions')
    for files in quiz_file:
        user = cur.execute(
            'select * from project1_marks where quiz_num=?', (files,)).fetchall()
        scores_file = os.path.join(os.getcwd(), 'quiz_wise_responses')
        scores_file = os.path.join(scores_file, 'scores_'+files)
        if len(user) != 0:
            with open(scores_file, 'w') as file:
                writer = csv.writer(file)
                writer.writerow(['Roll', 'quiz_num', 'Total marks'])
                writer.writerows(user)
    login_db.close()


def update_quiz(question_label, quiz_data, top):
    global index, radio_button, option_selected
    for i in radio_button:
        i.destroy()
    question_label.config(text="Q"+str(index+1)+") " + quiz_data['question'][index] + (' '*20) + "m: +" + str(
        quiz_data['marks_correct_ans'][index]) + ', ' + str(quiz_data['marks_wrong_ans'][index]))
    y = 0.1
    values = {}
    values[quiz_data['option1'][index]] = 1
    values[quiz_data['option2'][index]] = 2
    values[quiz_data['option3'][index]] = 3
    values[quiz_data['option4'][index]] = 4
    if quiz_data['compulsory'][index] == 'y':
        values['Skip This'] = 5
    option_selected = StringVar(None, str(record_response[index]))
    for (text, value) in values.items():
        y += 0.1
        rb = Radiobutton(top, text=text, variable=option_selected,
                         value=value, font=('Helvetica', 11, 'bold'))
        rb.place(relx=0.4, rely=y)
        radio_button.append(rb)


def quiz_print(quiz_data):
    global root, index, option_selected, count
    top = Toplevel(root)
    top.geometry('950x600')
    y = 0.1
    question_label = Label(top, text="Q"+str(index+1)+") " + quiz_data['question'][index] + (' '*20) + "m: +" + str(
        quiz_data['marks_correct_ans'][index]) + ', ' + str(quiz_data['marks_wrong_ans'][index]), font=('Helvetica', 13, 'bold'))
    question_label.place(relx=0.5, rely=y, anchor=CENTER)
    time_label = Label(top, text="", font=('Helvetica', 10, 'bold'))
    time_label.place(relx=0.9, rely=0.05, anchor=CENTER)
    y += 0.6
    save_label = Button(top, text="Save Response",
                        font=('Helvetica', 13, 'bold'))
    save_label.place(relx=0.5, rely=y, anchor=CENTER)
    y += 0.1
    next_label = Button(top, text="Next", font=('Helvetica', 13, 'bold'))
    next_label.place(relx=0.8, rely=y, anchor=CENTER)
    previous_label = Button(top, text="Previous",
                            font=('Helvetica', 13, 'bold'))
    previous_label.place(relx=0.2, rely=y, anchor=CENTER)
    y = y+0.1
    submit_label = Button(top, text="Submit", font=('Helvetica', 12, 'bold'))
    submit_label.place(relx=0.5, rely=y, anchor=CENTER)
    timer = quiz_data.columns.values[10]
    timer = re.split('[=m]', timer)[2]
    count = int(timer)*60
    countdown(quiz_data, top, time_label)
    update_quiz(question_label, quiz_data, top)

    next_label.config(command=lambda: next_question(
        quiz_data, top, question_label))
    previous_label.config(command=lambda: previous_question(
        quiz_data, top, question_label))
    submit_label.config(command=lambda: submit_quiz(quiz_data, top))
    save_label.config(command=lambda: save_quiz_response(option_selected))


def quiz_begin(top, v, quiz_file):
    top.destroy()
    global root, index, record_response, max_possible_score, roll, total_score, login_db, individual_responses, correct_attempt, wrong_attempt, quiz_ques_attempt, original_quiz_file
    index = 0
    record_response = {}
    choice = v.get()
    original_quiz_file = quiz_file[int(choice)-1]
    quiz_file = os.path.join('quiz_wise_questions', quiz_file[int(choice)-1])
    quiz_data = pd.read_csv(quiz_file)
    timer = quiz_data.columns.values[10]
    timer = re.split('[=m]', timer)[2]
    time_remaining = int(timer)*60
    for i in range(len(quiz_data)):
        max_possible_score += int(quiz_data['marks_correct_ans'][i])
        record_response[i] = 0
    quiz_print(quiz_data)


def start_quiz(top):
    top.destroy()
    global root
    quiz_file = os.listdir('quiz_wise_questions')
    values = {}
    for i in range(len(quiz_file)):
        values[quiz_file[i]] = str(i+1)
    top = Toplevel(root)
    top.geometry("450x450")
    v = StringVar(top, "1")
    Label(top, text="Choose one quiz from the below quizzes",
          font=('Helvetica', 13, 'bold')).pack(side=TOP, ipady=20)
    for (text, value) in values.items():
        Radiobutton(top, text=text, variable=v, value=value, font=(
            'Helvetica', 12, 'bold')).pack(side=TOP, ipady=15)
    ok = Button(top, text='Click to Start', font=('Helvetica', 12, 'bold'))
    ok.pack(side=TOP, padx=25, pady=25)
    ok.config(command=lambda: quiz_begin(top, v, quiz_file))


def register_first(top, roll, password, name_entry, wp_entry):
    global cur, name, wpno, login_db
    name = name_entry.get()
    wpno = wp_entry.get()
    cur.execute('insert into project1_registration values (?,?,?,?)',
                (name_entry.get(), roll, password, wp_entry.get()))
    login_db.commit()
    start_quiz(top)


def check_already_registered(top, user_name_entry, password_entry):

    global root, user, cur, roll, password
    roll = user_name_entry.get()
    password = get_hashed_password(password_entry.get())
    print(password)
    user = cur.execute(
        'select * from project1_registration where Roll=?', (roll,)).fetchall()
    print(user)
    if(len(user) == 0):
        top.destroy()
        top = Toplevel(root)
        top.geometry('450x450')
        Label(top, text="You need to register first!", font=(
            'Helvetica', 11, 'bold')).place(relx=0.5, rely=0.1, anchor=CENTER)
        name_label = Label(top, text="Name", font=('Helvetica', 12, 'bold'))
        name_label.place(relx=0.2, rely=0.2, anchor=CENTER)
        name_entry = Entry(top, bd=5, font=('Helvetica', 12, 'bold'))
        name_entry.place(relx=0.6, rely=0.2, anchor=CENTER)
        wp_label = Label(top, text="Whatsapp Number",
                         font=('Helvetica', 10, 'bold'))
        wp_label.place(relx=0.2, rely=0.3, anchor=CENTER)
        wp_entry = Entry(top, bd=5, font=('Helvetica', 12, 'bold'))
        wp_entry.place(relx=0.6, rely=0.3, anchor=CENTER)
        ok = Button(top, text='Register', font=('Helvetica', 12, 'bold'))
        ok.place(relx=0.5, rely=0.6, anchor=CENTER)
        ok.config(command=lambda: register_first(
            top, roll, password, name_entry, wp_entry))
    else:
        if not check_password(password_entry.get(), user[0][2]):
            top.destroy()
            tk.messagebox.showinfo("Login", "You have entered wrong password")
            login_register()
        else:
            start_quiz(top)


def login_register():
    top = Toplevel(root)
    top.geometry("450x450")
    user_name_label = Label(top, text="User Name",
                            font=('Helvetica', 12, 'bold'))
    user_name_label.place(relx=0.2, rely=0.2, anchor=CENTER)
    user_name_entry = Entry(top, bd=5, font=('Helvetica', 12, 'bold'))
    user_name_entry.place(relx=0.6, rely=0.2, anchor=CENTER)
    password_label = Label(top, text="Password",
                           font=('Helvetica', 12, 'bold'))
    password_label.place(relx=0.2, rely=0.3, anchor=CENTER)
    password_entry = Entry(top, bd=5, font=('Helvetica', 12, 'bold'), show='*')
    password_entry.place(relx=0.6, rely=0.3, anchor=CENTER)
    ok = Button(top, text='LOGIN', font=('Helvetica', 14, 'bold'))
    ok.place(relx=0.5, rely=0.6, anchor=CENTER)
    ok.config(command=lambda: check_already_registered(
        top, user_name_entry, password_entry))


root = Tk()
root.geometry('500x500')
root.title('Quiz Portal')
Label(root, text="Welcome to Quiz Portal!", font=(
    'Helvetica', 16, 'bold')).place(relx=0.5, rely=0.3, anchor=CENTER)
login = Button(root, text="Start Quiz", font=('Helvetica', 12, 'bold'))
login.place(relx=0.5, rely=0.5, anchor=CENTER)
login.config(command=lambda: login_register())
Label(root, text="Developed by Anmol Chaddha", font=(
    'Helvetica', 10, 'bold')).place(relx=0.5, rely=0.9, anchor=CENTER)


login_db = sq.connect("project1_quiz_cs384")
cur = login_db.cursor()
# cur.execute('drop table project1_registration')
# cur.execute('drop table project1_marks')
cur.execute('create table if not exists project1_registration(Name,Roll NOT NULL,Password,Whatsapp number VARCHAR(12),PRIMARY KEY(Roll))')
cur.execute('create table if not exists project1_marks(Roll NOT NULL,quiz_num,total_marks,PRIMARY KEY(Roll,quiz_num))')
max_possible_score = 0
total_score = 0
quiz_ques_attempt = 0
correct_attempt = 0
wrong_attempt = 0
roll = 0
individual_responses = []
radio_button = []
original_quiz_file = ''
count = 0
option_selected = StringVar()
root.mainloop()
