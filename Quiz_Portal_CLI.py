import pandas as pd
import sqlite3 as sq
import os
import re
import csv
import time
import threading
import signal
import bcrypt
from pynput import keyboard
from pynput.keyboard import Key, KeyCode, Listener


def get_hashed_password(plain_text_password):
    # Hash a password for the first time
    #   (Using bcrypt, the salt is saved into the hash itself)
    return bcrypt.hashpw(plain_text_password.encode('utf-8'), bcrypt.gensalt())


def check_password(plain_text_password, hashed_password):
    # Check hashed password. Using bcrypt, the salt is saved into the hash itself
    return bcrypt.checkpw(plain_text_password.encode('utf-8'), hashed_password.encode('utf-8'))


class TimeoutException (Exception):
    pass


def signalHandler(signum, frame):
    raise TimeoutException()


def countdown():
    global time_remaining
    while time_remaining > 0:
        mins, secs = divmod(time_remaining, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(' '*20, 'Time remaining: ', timer, end='\r')
        time.sleep(1)
        time_remaining -= 1


login_db = sq.connect("project1_quiz_cs384")
cur = login_db.cursor()
# cur.execute('drop table project1_registration')
# cur.execute('drop table project1_marks')
cur.execute('create table if not exists project1_registration(Name,Roll NOT NULL,Password,Whatsapp number VARCHAR(12),PRIMARY KEY(Roll))')
cur.execute('create table if not exists project1_marks(Roll NOT NULL,quiz_num,total_marks,PRIMARY KEY(Roll,quiz_num))')
print("Enter your login details!")
roll = input("Username : ")
password = input("Password: ")
hashed_password = get_hashed_password(password)
name = ""
wpno = ""

user = cur.execute(
    'select * from project1_registration where Roll=?', (roll,)).fetchall()
if(len(user) == 0):
    print("You need to register yourself first!")
    print("Username:", roll)
    print("Password:", password)
    name = input("Name: ")
    wpno = input("Whatsapp number: ")
    cur.execute('insert into project1_registration values (?,?,?,?)',
                (name, roll, hashed_password, wpno))
else:
    while(not check_password(password, user[0][2])):
        print("Please enter correct password or -1 if forgotten")
        password = input("Password: ")
        if(password == '-1'):
            password = input("Enter new password:")
            cur.execute(
                'update project1_registration set password=?', (get_hashed_password(password),))
            break
    name = user[0][0]
    wpno = user[0][3]
login_db.commit()

quiz_file = os.listdir('quiz_wise_questions')
print('Choose one quiz from the following quizzes:')
for i in range(len(quiz_file)):
    print(i+1, '-', quiz_file[i])
print('Enter your choice(eg 1 for', quiz_file[0], ')')
choice = input('Enter number:')
original_quiz_file = quiz_file[int(choice)-1]
quiz_file = os.path.join('quiz_wise_questions', quiz_file[int(choice)-1])
quiz_data = pd.read_csv(quiz_file)
timer = quiz_data.columns.values[10]
timer = re.split('[=m]', timer)[2]
time_remaining = int(timer)*60
# time_remaining = 20

t1 = threading.Thread(target=countdown)
signal.signal(signal.SIGALRM, signalHandler)
signal.alarm(time_remaining)
t1.start()
total_score = 0
max_possible_score = 0
quiz_ques_attempt = 0
correct_attempt = 0
wrong_attempt = 0
individual_reponses = []
for i in range(len(quiz_data)):
    max_possible_score += int(quiz_data['marks_correct_ans'][i])
try:
    for i in range(len(quiz_data)):
        os.system('clear')
        ans = ''
        print('Question ', i+1, ') ', quiz_data['question'][i])
        print('Option 1) ', '-', quiz_data['option1'][i])
        print('Option 2) ', '-', quiz_data['option2'][i])
        print('Option 3) ', '-', quiz_data['option3'][i])
        print('Option 4) ', '-', quiz_data['option4'][i])
        print('Credits if Correct Option: +',
              quiz_data['marks_correct_ans'][i])
        print('Negative Marking:', quiz_data['marks_wrong_ans'][i])
        print('Is compulsory: ', quiz_data['compulsory'][i])
        if(quiz_data['compulsory'][i] == 'y'):
            while ans != '1' and ans != '2' and ans != '3' and ans != '4':
                print('Enter choice 1,2,3,4:')
                ans = input()
        else:
            while ans != '1' and ans != '2' and ans != '3' and ans != '4' and ans != 'S':
                print('Enter choice 1,2,3,4,S: S is to skip question')
                ans = input()
        correct_ans = (quiz_data['correct_option'][i])
        individual_reponses.append([i+1, quiz_data['question'][i], quiz_data['option1'][i], quiz_data['option2'][i], quiz_data['option3'][i], quiz_data['option4']
                                    [i], quiz_data['correct_option'][i], quiz_data['marks_correct_ans'][i], quiz_data['marks_wrong_ans'][i], quiz_data['compulsory'][i], ans])

        if(ans == 'S' or ans == 's'):
            pass
        elif(correct_ans == int(ans)):
            quiz_ques_attempt += 1
            correct_attempt += 1
            total_score += int(quiz_data['marks_correct_ans'][i])
        else:
            quiz_ques_attempt += 1
            wrong_attempt += 1
            total_score += int(quiz_data['marks_wrong_ans'][i])
    time_remaining = 1
    signal.alarm(0)

except TimeoutException as exc:
    pass
finally:
    os.system('clear')
    signal.alarm(0)
    # t2.join()
    print("Time Up! Your quiz has been autosubmitted")
    print('Total quiz questions: ', len(quiz_data))
    print('Total Quiz Questions Attempted: ', quiz_ques_attempt)
    print("Total Correct Question: ", correct_attempt)
    print("Total Wrong Questions: ", wrong_attempt)
    print("Total Marks: ", total_score, '/', max_possible_score)

t1.join()
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
    writer.writerows(individual_reponses)
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
