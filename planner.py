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
sleepBegin = 22
sleepEnd = 7


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

def pull_stuff():
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a list of the next
    10 events on the user's calendar.
    """
    task_credentials = get_task_credentials()
    http = task_credentials.authorize(httplib2.Http())
    service = discovery.build('tasks', 'v1', http=http)

    tasks = service.tasks().list(tasklist='@default').execute()
    for task in tasks['items']:
    	assignments[task['title']] = task['id']
    	# if 'due' in task:
    	# 	print(task['title'], task['due'])
    	# else:
    	# 	print(task['title'])
    print(assignments)

    calendar_credentials = get_calendar_credentials()
    http = calendar_credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
    	#print(event)
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))

        sdt = dateutil.parser.parse(start)
        edt = dateutil.parser.parse(end)
        times = sdt.strftime('%I:%M') + " to " + edt.strftime('%I:%M')

        if 'location' not in event:
        	print(times, event['summary'])
        else:
   			print(times, event['summary'], event['location'])

def list_events(numEvents = 10):
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
			print(times, event['summary'])
		else:
				print(times, event['summary'], event['location'])


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

def complete_task(taskName):
	if len(assignments) == 0:
		populate_assignments()
	if taskName is "" or taskName not in assignments:
		print("Sorry, we couldn't delete the task " + taskName + ".")
		return
	taskID = assignments[taskName][0]
	task_credentials = get_task_credentials()
	http = task_credentials.authorize(httplib2.Http())
	service = discovery.build('tasks', 'v1', http=http)
	task = service.tasks().get(tasklist='@default', task=taskID).execute()
	task['status'] = 'completed'
	result = service.tasks().update(tasklist='@default', task=task['id'], body=task).execute()
	print("Successfully completed. " + result['completed'])

def list_pending_tasks(maxTasks = 100):
	assignments.clear()
	task_credentials = get_task_credentials()
	http = task_credentials.authorize(httplib2.Http())
	service = discovery.build('tasks', 'v1', http=http)
	tasks = service.tasks().list(tasklist='@default', maxResults = maxTasks, showCompleted = False).execute()
	for task in tasks['items']:
		if task['title'] != "":
			assignments[task['title']] = (task['id'], task['due'] if 'due' in task else None)
			print(task['title'])
	if len(assignments) == 0:
		print("You have no pending tasks.")

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

def get_next_events(numEvents = 100):
	calendar_credentials = get_calendar_credentials()
	http = calendar_credentials.authorize(httplib2.Http())
	service = discovery.build('calendar', 'v3', http=http)

	now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
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

def populate_event_list():
	events = get_next_events()
	today = datetime.now(pytz.utc)
	today = today.astimezone(tz.tzlocal())
	event1 = (today + timedelta(days = 365), today + timedelta(days = 366))
	event2 = (today + timedelta(days = 368), today + timedelta(days = 369))
	events.append(event1)
	events.append(event2)
	return events

def add_assignment(name, year, month, day, timeToComplete, attentionSpan, breakTime, minWorkTime = 15):

	due = datetime(year, month, day, tzinfo=datetime.now(pytz.utc).tzinfo)
	due = due.astimezone(tz.tzlocal())

	events = populate_event_list()
	workSessions = list()
	timeToComplete = timedelta(hours = timeToComplete)
	attentionSpan = timedelta(hours = attentionSpan)
	breakTime = timedelta(minutes = breakTime)
	minWorkTime = timedelta(minutes = minWorkTime)
	index = 0
	time1 = datetime.now(pytz.utc) + breakTime
	time1 = time1.astimezone(tz.tzlocal())

	while(timeToComplete.total_seconds() > 0):
		
		time2 = events[index][0] - breakTime
		if time1.day != time2.day or time2.hour > sleepBegin:
			sleepTonightBegin = time1.replace(hour = 22, minute = 0)
			#print(sleepTonightBegin)
			sleepTonightEnd = sleepTonightBegin + timedelta(hours = (24 - sleepBegin + sleepEnd))
			events.insert(index, (sleepTonightBegin, sleepTonightEnd))
			#print(sleepTonightEnd)
			continue
		
		freetime = time2 - time1
		
		if (freetime >= minWorkTime):
			workTime = attentionSpan if time2 - time1 > attentionSpan else time2 - time1
			workTime = timeToComplete if workTime > timeToComplete else workTime
			workStartTime = time1
			workEndTime = workStartTime + workTime
			if workStartTime.hour >= sleepEnd and workEndTime.hour < sleepBegin and workEndTime.hour >= sleepEnd:
				workSessions.append((workStartTime, workEndTime))
				events.insert(index, (workStartTime, workEndTime))
				timeToComplete -= workTime

		time1 = events[index][1] + breakTime
		index += 1

	if workSessions[len(workSessions) - 1][1] > due:
		print("Sorry, you don't have enough time to work on this assignment.")
	else:
		print("Printing time sessions: ")
		for item in workSessions:
			print(item[0])
			print(item[1])
			add_calendar_event("Work on " + name, "", "", item[0], item[1])
		add_task(name, due)

def change_sleep_times():
	if sleepBegin > 12:
		print("Currently, you sleep at " + str(sleepBegin % 12) + " PM and wake up at " + str(sleepEnd) + "AM.")
	else:
		print("Currently, you sleep at " + str(sleepBegin) + " AM and wake up at " + str(sleepEnd) + "AM.")
		while True:
			try:
				sleepBeginString = raw_input("Ahat time do you normally go to sleep? Enter as int, use 24-hr time. Example: 22 for 10 pm.")
				sleepBegin = int(sleepBeginString)
				if sleepBegin > 24 or sleepBegin < 0:
					continue
				break
			except ValueError:
				print("Please enter an integer valid time.")
		while True:
			try:
				sleepEndString = raw_input("What time do you normally wake up? Enter as int, use 24-hr time. Example: 8 for 8 am. You can't wake up after noon.")
				if sleepEnd >= 12 or sleepEnd < 0:
					continue
				break
			except ValueError:
				print("Please enter an integer valid time.")


def welcome():
	print("\nEnter the number that corresponds to one of the following choices and enter, or only press enter to quit.")
	print("1. List pending tasks")
	print("2. List upcoming events")
	print("3. Add a task and schedule times to work on it")
	print("4. Mark a task as completed")
	print("5. Reset sleep schedule (default is 10 pm bedtime, 7 am wake-up time)")


def main():
	test = raw_input("is this a test: ")
	if (test == "y"):
		add_assignment("test assignment", 2017, 1, 5, 10, 2, 15, 15)
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
			breakTime = raw_input("How much time do you need to break for in minutes? ")
			minWorkTime = raw_input("What is the minimum number of minutes you'd like to work for at a stretch? ")
			#startDate = raw_input("when would you like to start working on this assignment? MM/DD/YYYY")
			add_assignment(assignment, int(year), int(month), int(day), int(timeToComplete), int(attentionSpan), int(breakTime), int(minWorkTime))
		elif choice == 4:
			task = raw_input("What is the name of the task you'd like to mark as completed?\n")
			complete_task(task)
		elif choice == 5:
			change_sleep_times()

	print("\nThanks for using the planner!")



if __name__ == '__main__':
    main()