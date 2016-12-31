# add event to calendar: put in due date and time, estimated time to completion, how i want to segment by


from __future__ import print_function
import httplib2
import os
import sys
import pytz
import copy

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from Tkinter import *

import datetime
import dateutil.parser
from datetime import tzinfo, timedelta, datetime
from dateutil import tz

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
CALENDAR_SCOPES = 'https://www.googleapis.com/auth/calendar'
TASK_SCOPES = 'https://www.googleapis.com/auth/tasks'
CALENDAR_CLIENT_SECRET_FILE = 'calendar_client_secret.json'
TASK_CLIENT_SECRET_FILE = 'task_client_secret.json'
CALENDAR_APPLICATION_NAME = 'Google Calendar API Python Quickstart'
TASK_APPLICATION_NAME = 'Google Task API Python Quickstart'

assignments = {}
sleepBeginHour = 22
sleepBeginMinute = 0
sleepEndHour = 8
sleepEndMinute = 0
sleepMinutes = 600
e = ""
s = ""


def get_calendar_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CALENDAR_CLIENT_SECRET_FILE, CALENDAR_SCOPES)
        flow.user_agent = CALENDAR_APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def get_task_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'tasks-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(TASK_CLIENT_SECRET_FILE, TASK_SCOPES)
        flow.user_agent = TASK_APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def list_events(tex, numEvents = 10):
	calendar_credentials = get_calendar_credentials()
	http = calendar_credentials.authorize(httplib2.Http())
	service = discovery.build('calendar', 'v3', http=http)

	now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
	print('Getting the upcoming 10 events')
	eventsResult = service.events().list(
		calendarId='primary', timeMin=now, maxResults=numEvents, singleEvents=True,
		orderBy='startTime').execute()
	events = eventsResult.get('items', [])

	if not events:
		print('No upcoming events found.')
	
	for event in events:
		start = event['start'].get('dateTime', event['start'].get('date'))
		end = event['end'].get('dateTime', event['end'].get('date'))

		sdt = dateutil.parser.parse(start)
		edt = dateutil.parser.parse(end)
		times = sdt.strftime('%I:%M') + " to " + edt.strftime('%I:%M')

		if 'location' not in event:
			tex.insert(END, times + ": " + event['summary'] + "\n")
			tex.see(END)
			#print(times, event['summary'])
		else:
			tex.insert(END, times + ": " + event['summary'] + " at " + event['location'] + "\n")
			tex.see(END)
			#print(times, event['summary'], event['location'])


def add_task(name, due):
	if name is "":
		return
	task_credentials = get_task_credentials()
	http = task_credentials.authorize(httplib2.Http())
	service = discovery.build('tasks', 'v1', http=http)

	due = due.isoformat() #+ str(".000Z")
	task = {'title': name, 'due': due} #fix date
	result = service.tasks().insert(tasklist='@default', body=task).execute()
	assignments[name] = (result['id'], due)
	print(result['id'])

def populate_assignments(maxTasks = 100):
	assignments.clear()
	task_credentials = get_task_credentials()
	http = task_credentials.authorize(httplib2.Http())
	service = discovery.build('tasks', 'v1', http=http)
	tasks = service.tasks().list(tasklist='@default', maxResults = maxTasks, showCompleted = False).execute()
	for task in tasks['items']:
		if task['title'] != "":
			assignments[task['title']] = (task['id'], task['due'] if 'due' in task else None)

def complete_task(tex, taskName):
	if len(assignments) == 0:
		populate_assignments()
	if taskName is "" or taskName not in assignments:
		#print("Sorry, we couldn't delete the task " + taskName + ".")
		tex.insert(END, "Sorry, we couldn't delete the task " + taskName + ".\n")
		tex.see(END)
		return
	taskID = assignments[taskName][0]
	task_credentials = get_task_credentials()
	http = task_credentials.authorize(httplib2.Http())
	service = discovery.build('tasks', 'v1', http=http)
	task = service.tasks().get(tasklist='@default', task=taskID).execute()
	task['status'] = 'completed'
	result = service.tasks().update(tasklist='@default', task=task['id'], body=task).execute()
	#print("Successfully completed. " + result['completed'])
	tex.insert(END, "Successfully completed. " + result['completed'] + "\n")
	tex.see(END)

def list_pending_tasks(tex, maxTasks = 100):
	assignments.clear()
	task_credentials = get_task_credentials()
	http = task_credentials.authorize(httplib2.Http())
	service = discovery.build('tasks', 'v1', http=http)
	tasks = service.tasks().list(tasklist='@default', maxResults = maxTasks, showCompleted = False).execute()
	for task in tasks['items']:
		if task['title'] != "":
			assignments[task['title']] = (task['id'], task['due'] if 'due' in task else None)
			#print(task['title'])
			tex.insert(END, task['title'] + "\n")
			tex.see(END)

	if len(assignments) == 0:
		#print("You have no pending tasks.")
		tex.insert(END, "You have no pending tasks.\n")
		tex.see(END)

def add_calendar_event(name, location, description, start, end):
	calendar_credentials = get_calendar_credentials()
	http = calendar_credentials.authorize(httplib2.Http())
	service = discovery.build('calendar', 'v3', http=http)

	event = {
	'summary': name,
	'location': location,
	'description': description,
	'start': {
	'dateTime': start.isoformat(),
	},
	'end': {
	'dateTime': end.isoformat(),
	},
	}
	event = service.events().insert(calendarId='primary', body=event).execute()
	print('Event created: %s' % (event.get('htmlLink')))

def get_next_events(now, numEvents = 100):
	calendar_credentials = get_calendar_credentials()
	http = calendar_credentials.authorize(httplib2.Http())
	service = discovery.build('calendar', 'v3', http=http)

	eventsResult = service.events().list(
		calendarId='primary', timeMin=now, maxResults=numEvents, singleEvents=True,
		orderBy='startTime').execute()
	events = eventsResult.get('items', [])
	eventList = list()
	for event in events:
		start = event['start'].get('dateTime', event['start'].get('date'))
		end = event['end'].get('dateTime', event['end'].get('date'))
		sdt = dateutil.parser.parse(start)
		edt = dateutil.parser.parse(end)
		eventList.append((sdt, edt))
		times = sdt.strftime('%y/%m/%d %I:%M') + " to " + edt.strftime('%I:%M')
		#print(times, event['summary'])
	return eventList

def populate_event_list(startDate):
	now = None
	if startDate == "":
		now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
	else:
		now = datetime(int(startDate.split("/")[2]), int(startDate.split("/")[0]), int(startDate.split("/")[1]), tzinfo=tz.tzlocal())
		if now < datetime.now(pytz.utc):
			now = datetime.now(pytz.utc)
		now = now.isoformat()

	events = get_next_events(now)
	today = datetime.now(pytz.utc)
	today = today.astimezone(tz.tzlocal())
	event1 = (today + timedelta(days = 1), today + timedelta(days = 2)) #THIS DOESN'T QUITE WORK!
	event2 = (today + timedelta(days = 3), today + timedelta(days = 4))
	events.append(event1)
	events.append(event2)
	return events

def add_assignment(name, year, month, day, timeToComplete, attentionSpan, breakTime, startDate, minWorkTime = 15, travelTime = 15):

	due = datetime(year, month, day, tzinfo=datetime.now(pytz.utc).tzinfo)
	due = due.astimezone(tz.tzlocal())
	travelTime = timedelta(minutes = travelTime)
	time1 = None
	if startDate == "":
		time1 = datetime.now(pytz.utc) + travelTime
		time1 = time1.astimezone(tz.tzlocal())
	else:
		time1 = datetime(int(startDate.split("/")[2]), int(startDate.split("/")[0]), int(startDate.split("/")[1]), tzinfo=tz.tzlocal())
		if time1 < datetime.now(pytz.utc) + travelTime:
			time1 = datetime.now(pytz.utc) + travelTime

	events = populate_event_list(startDate)
	workSessions = list()
	timeToComplete = timedelta(hours = timeToComplete)
	attentionSpan = timedelta(hours = attentionSpan)
	breakTime = timedelta(hours = breakTime)
	minWorkTime = timedelta(minutes = minWorkTime)
	index = 0

	while(timeToComplete.total_seconds() > 0):

		#what to do if they are not in order?
		
		time2 = events[index][0] - travelTime
		if time2 < time1:
			time1 = time2
		if time1.day != time2.day or time2.hour > sleepBeginHour:
			sleepTonightBegin = time1.replace(hour = sleepBeginHour, minute = sleepBeginMinute, second = 0)
			sleepTonightEnd = sleepTonightBegin + timedelta(minutes = sleepMinutes)
			events.insert(index, (sleepTonightBegin, sleepTonightEnd))
			continue
		
		freetime = time2 - time1
		
		if (freetime >= minWorkTime):
			workTime = attentionSpan if time2 - time1 > attentionSpan else time2 - time1
			workTime = timeToComplete if workTime > timeToComplete else workTime
			workStartTime = time1
			workEndTime = workStartTime + workTime
			if workStartTime.hour >= sleepEndHour and workEndTime.hour < sleepBeginHour and workEndTime.hour >= sleepEndHour:
				print(workStartTime.hour)
				workSessions.append((workStartTime, workEndTime))
				events.insert(index, (workStartTime, workEndTime))
				timeToComplete -= workTime
				time1 = events[index][1] + breakTime
			else:
				time1 = events[index][1] + travelTime
		
		else:
			time1 = events[index][1] + travelTime
		index += 1

	if workSessions[len(workSessions) - 1][1] > due:
		print("Sorry, you don't have enough time to work on this assignment.")
	else:
		print("Printing time sessions: ")
		for item in workSessions:
			print("Start: " + str(item[0]))
			print("End: " + str(item[1]))
			add_calendar_event("Work on " + name, "", "", item[0], item[1])
		add_task(name, due)

def change_sleep_times():
	global sleepBeginHour
	global sleepBeginMinute
	global sleepEndHour
	global sleepEndMinute
	global sleepMinutes
	if sleepBeginHour > 12:
		print("Currently, you sleep at " + str(sleepBeginHour % 12) + ":" + str(sleepBeginMinute) + " PM and wake up at " + str(sleepEndHour) + ":" + str(sleepEndMinute) + " AM.") #format minute string
	else:
		print("Currently, you sleep at " + str(sleepBeginHour) + ":" + str(sleepBeginMinute) + " AM and wake up at " + str(sleepEndHour) + ":" + str(sleepEndMinute) + " AM.")
	while True:
		try:
			sleepBeginString = raw_input("What time do you normally go to sleep? Use 24-hr time in format HH:MM. Example: 22:00 for 10 PM.\n")
			sleepBeginHour = int(sleepBeginString.split(":")[0])
			sleepBeginMinute = int(sleepBeginString.split(":")[1])
			if sleepBeginHour > 24 or sleepBeginHour < 0:
				continue
			if sleepBeginMinute > 59 or sleepBeginMinute < 0:
				continue
			break
		except ValueError:
			print("Please enter an valid time.")
	while True:
		try:
			sleepEndString = raw_input("What time do you normally wake up? Use 24-hr time in format HH:MM. Example: 8:00 for 8 AM. You can't wake up after noon.\n")
			sleepEndHour = int(sleepEndString.split(":")[0])
			sleepEndMinute = int(sleepEndString.split(":")[1])
			if sleepEndHour >= 12 or sleepEndHour < 0:
				continue
			if sleepEndMinute > 59 or sleepEndMinute < 0:
				continue
			break
		except ValueError:
			print("Please enter a valid time.")
	wakeUpMinutes = sleepEndMinute + 60 * sleepEndHour
	asleepMinutes = sleepBeginMinute + 60 * sleepBeginHour
	sleepMinutes = (wakeUpMinutes - asleepMinutes) if wakeUpMinutes > asleepMinutes else (24 * 60 - asleepMinutes + wakeUpMinutes)

def welcome():
	print("\nEnter the number that corresponds to one of the following choices and enter, or only press enter to quit.")
	print("1. List pending tasks")
	print("2. List upcoming events")
	print("3. Add a task and schedule times to work on it")
	print("4. Mark a task as completed")
	print("5. Reset sleep schedule (default is 10 pm bedtime, 7 am wake-up time)")

def welcome_buttons(bop, tex):
	Button(bop, text="1. List pending tasks", command=callback(1, tex)).pack()
	Button(bop, text="2. List upcoming events", command=callback(2, tex)).pack()
	Button(bop, text="3. Add a task and schedule times to work on it", command=callback(3, tex)).pack()
	Button(bop, text="4. Mark a task as completed", command=callback(4, tex)).pack()
	Button(bop, text="5. Reset sleep schedule (default is 10 pm bedtime, 7 am wake-up time)", command=callback(5, tex)).pack()
	#Button(bop, text="6. Clear screen.)", command=callback(6, tex)).pack()

def callback(id, tex):
    return lambda : cbc(id, tex)

def submitcallback(id, tex):
	if id == 1:
		return lambda : tasks_gui(tex)
	elif id == 2:
		return lambda : events_gui(tex)
	elif id == 4:
		return lambda : complete_task_gui(tex)

def complete_task_gui(tex):
	global e
	global b
	task = e.get()
	complete_task(tex, task)
	e.delete(0, END)
	b.destroy()

def tasks_gui(tex):
	global e
	global b
	try:
		num = int(e.get())
		list_pending_tasks(tex, num)
	except ValueError:
		list_pending_tasks(tex)
	e.delete(0, END)
	b.destroy()

def events_gui(tex):
	global e
	global b
	try:
		num = int(e.get())
		list_events(tex, num)
	except ValueError:
		list_events(tex)
	e.delete(0, END)
	b.destroy()

def rawinputequiv():
	global e
	global s
	s = e.get()

def cbc(option, tex):
	global b
	#s = 'At {} f is {}\n'.format(id, id**id/0.987)
	#s = e.get() + "\n"
	s = ""
	tex.delete(1.0, END)
	tex.insert(END, s)
	tex.see(END)
	if option == 1:
		s += "What is the maximum number of tasks you'd like to see? Press enter for a default of 100.\n\n"
		tex.insert(END, s)
		tex.see(END)
		b = Button(top, text = 'Submit', command = submitcallback(option, tex))
		b.pack(side = BOTTOM)
	elif option == 2:
		s += "What is the maximum number of events you'd like to see? Press enter for a default of 10.\n\n"
		tex.insert(END, s)
		tex.see(END)
		b = Button(top, text = 'Submit', command = submitcallback(option, tex))
		b.pack(side = BOTTOM)
	elif option == 3:
		s += "Enter name of assignment/task to add: "
		tex.insert(END, s)
		tex.see(END)

	elif option == 4:
		s += "What is the name of the task you'd like to mark as completed?\n"
		tex.insert(END, s)
		tex.see(END)
		b = Button(top, text = 'Submit', command = submitcallback(option, tex))
		b.pack(side = BOTTOM)


		# try:
		# 	num = int(10)
		# 	list_pending_tasks(tex, num)
		# except ValueError:
		# 	list_pending_tasks(tex)

def main():
	global e
	global top
	top = Tk()

	e = Entry(top)
	e.pack(side=BOTTOM)
	e.focus_set()
	tex = Text(master=top)
	tex.pack(side=RIGHT)
	
	bop = Frame()
	bop.pack(side=LEFT)
	welcome_buttons(bop, tex)
	# for k in range(1,10):
	# 	tv = 'Say {}'.format(k)
	# 	b = Button(bop, text=tv, command=cbc(k, tex))
	# 	b.pack()

	Button(bop, text='Exit', command=top.destroy).pack()
	top.mainloop()


	test = raw_input("is this a test: ")
	if (test == "y"):
		add_assignment("test assignment", 2017, 1, 10, 10, 2, 3, "1/1/2016", 15, 15)
		return

	print("Welcome to the planner!")
	while True:
		choice = "choice"
		while choice != "1" and choice != "2" and choice != "3" and choice != "4" and choice != "5" and choice != "":
			welcome()
			choice = raw_input("")
		if choice == "":
			break
		choice = int(choice)
		print()
		if choice == 1:
			numTasks = raw_input("What is the maximum number of tasks you'd like to see? Press enter for a default of 100.\n")
			try:
				num = int(numTasks)
				list_pending_tasks(num)
			except ValueError:
				list_pending_tasks()
		elif choice == 2:
			numEvents = raw_input("What is the maximum number of events you'd like to see? Press enter for a default of 10.\n")
			try:
				num = int(numEvents)
				list_events(num)
			except ValueError:
				list_events()
		elif choice == 3:
			assignment = raw_input("Enter name of assignment/task to add: ")
			dueDate = raw_input("Enter the date that this is due (MM/DD/YYYY): ")
			year = dueDate.split("/")[2]
			month = dueDate.split("/")[0]
			day = dueDate.split("/")[1]
			timeToComplete = raw_input("How long will this take to complete in hours? ")
			attentionSpan = raw_input("What is your attention span in hours? ")
			breakTime = raw_input("How much time do you need to break for between back-to-back study sessions (in hours)? ")
			minWorkTime = raw_input("What is the minimum number of minutes you'd like to work for at a stretch? ")
			travelTime = raw_input("What is the amount of time in minutes required to travel to the next event? This is used as a buffer between events existing on your calendar and study sessions being planned. ")
			startDate = raw_input("Enter the date you would like to start working on this (MM/DD/YYYY) or blank for today: ") #make sure start time is after today
			add_assignment(assignment, int(year), int(month), int(day), float(timeToComplete), float(attentionSpan), float(breakTime), startDate, float(minWorkTime), float(travelTime))
		elif choice == 4:
			task = raw_input("What is the name of the task you'd like to mark as completed?\n")
			complete_task(task)
		elif choice == 5:
			change_sleep_times()

	print("\nThanks for using the planner!")



if __name__ == '__main__':
    main()
