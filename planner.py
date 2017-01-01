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

class Planner:
	def __init__(self):
		self.assignmentsDictionary = {}
		self.populate_assignments()
		self.sleepBeginHour = 22
		self.sleepEndHour = 8
		self.sleepBeginMinute = 0
		self.sleepEndMinute = 0
		self.sleepMinutes = 600
		self.eventsDictionary = {}

	def get_calendar_credentials(self):
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

	def get_task_credentials(self):
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

	def populate_assignments(self, maxTasks = 100):
		self.assignmentsDictionary.clear()
		task_credentials = self.get_task_credentials()
		http = task_credentials.authorize(httplib2.Http())
		service = discovery.build('tasks', 'v1', http=http)
		tasks = service.tasks().list(tasklist='@default', maxResults = maxTasks, showCompleted = False).execute()
		for task in tasks['items']:
			if task['title'] != "":
				self.assignmentsDictionary[task['title']] = (task['id'], task['due'] if 'due' in task else None)

	def list_events(self, numEvents = 10):
		calendar_credentials = self.get_calendar_credentials()
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


	def add_task(self, name, due):
		if name is "":
			return None
		task_credentials = self.get_task_credentials()
		http = task_credentials.authorize(httplib2.Http())
		service = discovery.build('tasks', 'v1', http=http)

		due = due.isoformat() #+ str(".000Z")
		task = {'title': name, 'due': due} #fix date
		result = service.tasks().insert(tasklist='@default', body=task).execute()
		self.assignmentsDictionary[name] = (result['id'], due)
		return result['id']


	def complete_task(self, taskName):
		if len(self.assignmentsDictionary) == 0:
			self.populate_assignments()
		if taskName is "" or taskName not in self.assignmentsDictionary:
			print("Sorry, we couldn't delete the task " + taskName + ".")
			return
		taskID = self.assignmentsDictionary[taskName][0]
		task_credentials = self.get_task_credentials()
		http = task_credentials.authorize(httplib2.Http())
		service = discovery.build('tasks', 'v1', http=http)
		task = service.tasks().get(tasklist='@default', task=taskID).execute()
		task['status'] = 'completed'
		result = service.tasks().update(tasklist='@default', task=task['id'], body=task).execute()
		print("Successfully completed. " + result['completed'])

	def list_pending_tasks(self, maxTasks = 100):
		self.assignmentsDictionary.clear()
		task_credentials = self.get_task_credentials()
		http = task_credentials.authorize(httplib2.Http())
		service = discovery.build('tasks', 'v1', http=http)
		tasks = service.tasks().list(tasklist='@default', maxResults = maxTasks, showCompleted = False).execute()
		for task in tasks['items']:
			if task['title'] != "":
				self.assignmentsDictionary[task['title']] = (task['id'], task['due'] if 'due' in task else None)
				print(task['title'])
		if len(self.assignmentsDictionary) == 0:
			print("You have no pending tasks.")

	def add_calendar_event(self, name, location, description, start, end):
		calendar_credentials = self.get_calendar_credentials()
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
		return event['id']

	def get_next_events(self, now, due, assignmentToIgnore, numEvents = 100):
		calendar_credentials = self.get_calendar_credentials()
		http = calendar_credentials.authorize(httplib2.Http())
		service = discovery.build('calendar', 'v3', http=http)

		eventsResult = service.events().list(
			calendarId='primary', timeMin=now, timeMax = due, singleEvents=True,
			orderBy='startTime').execute()
		events = eventsResult.get('items', [])
		eventList = list()
		self.eventsDictionary.clear()
		for event in events:
			if "Work on" in event['summary']:
				if event['description'] not in self.eventsDictionary:
					self.eventsDictionary[event['description']] = list()
				self.eventsDictionary[event['description']].append(event['id'])
				if event['description'] == assignmentToIgnore:
					continue
			start = event['start'].get('dateTime', event['start'].get('date'))
			end = event['end'].get('dateTime', event['end'].get('date'))
			sdt = dateutil.parser.parse(start)
			edt = dateutil.parser.parse(end)
			eventList.append((sdt, edt))
			times = sdt.strftime('%y/%m/%d %I:%M') + " to " + edt.strftime('%I:%M')
			#print(times, event['summary'])
		return eventList

	def print_eventsDictionary(self):
		for event in self.eventsDictionary:
			print(event)
			print(self.eventsDictionary[event])

	def populate_event_list(self, startDate, due, assignmentToIgnore = ""):
		now = None
		if startDate == "":
			now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
		else:
			now = datetime(int(startDate.split("/")[2]), int(startDate.split("/")[0]), int(startDate.split("/")[1]), tzinfo=tz.tzlocal())
			if now < datetime.now(pytz.utc):
				now = datetime.now(pytz.utc)
			now = now.isoformat()

		events = self.get_next_events(now, due.isoformat(), assignmentToIgnore)
		today = datetime.now(pytz.utc)
		today = today.astimezone(tz.tzlocal())
		event1 = (today + timedelta(hours = 1), today + timedelta(hours = 1.1)) #THIS DOESN'T QUITE WORK!
		event2 = (today + timedelta(hours = 1.2), today + timedelta(hours = 1.3))
		events.append(event1)
		events.append(event2)
		return events

	def schedule_assignment(self, index, due, time1, timeToComplete, attentionSpan, breakTime, minWorkTime, travelTime, events):
		workSessions = list()
		start = time1

		while(timeToComplete.total_seconds() > 0):
			if index < len(events):
				time2 = events[index][0] - travelTime
			else:
				time2 = time1 + minWorkTime + timedelta(hours = 1)

			if time2 < time1 and time2 > start:
				time1 = time2
			if time1.day != time2.day or time2.hour > self.sleepBeginHour:
				if time1.hour < self.sleepEndHour:
					time1 -= timedelta(hours = 24)
				sleepTonightBegin = time1.replace(hour = self.sleepBeginHour, minute = self.sleepBeginMinute, second = 0)
				sleepTonightEnd = sleepTonightBegin + timedelta(minutes = self.sleepMinutes)
				events.insert(index, (sleepTonightBegin, sleepTonightEnd))
				continue
			
			freetime = time2 - time1
			
			if (freetime >= minWorkTime):
				workTime = attentionSpan if time2 - time1 > attentionSpan else time2 - time1
				workTime = timeToComplete if workTime > timeToComplete else workTime
				workStartTime = time1
				workEndTime = workStartTime + workTime
				if workStartTime.hour >= self.sleepEndHour and workEndTime.hour < self.sleepBeginHour and workEndTime.hour >= self.sleepEndHour:
					#print(workStartTime.hour)
					workSessions.append((workStartTime, workEndTime))
					events.insert(index, (workStartTime, workEndTime))
					timeToComplete -= workTime
					time1 = workEndTime + breakTime
				else:
					time1 = events[index][1] + travelTime
			
			else:
				if index < len(events):
					time1 = events[index][1] + travelTime

			index += 1

		if workSessions[len(workSessions) - 1][1] > due:
			for item in workSessions:
				print("Start: " + str(item[0]))
				print("End: " + str(item[1]))
			return None

		return (workSessions, index, events, time1)

	def total_assignment_time(self, events):
		calendar_credentials = self.get_calendar_credentials()
		http = calendar_credentials.authorize(httplib2.Http())
		service = discovery.build('calendar', 'v3', http=http)
		totalTime = timedelta(minutes = 0)
		for event in events:
			event = service.events().get(calendarId='primary', eventId=event).execute()
			sdt = dateutil.parser.parse(event['start'].get('dateTime'))
			edt = dateutil.parser.parse(event['end'].get('dateTime'))
			totalTime += (edt - sdt)
		return totalTime


	def find_assignment_to_reschedule(self, name, startDate, due, timeToComplete, attentionSpan, breakTime, minWorkTime, travelTime, time1):
		task_credentials = self.get_task_credentials()
		http = task_credentials.authorize(httplib2.Http())
		taskService = discovery.build('tasks', 'v1', http=http)
		calendar_credentials = self.get_calendar_credentials()
		http = calendar_credentials.authorize(httplib2.Http())
		calendarService = discovery.build('calendar', 'v3', http=http)
		for assignment in self.eventsDictionary:
			task = taskService.tasks().get(tasklist='@default', task=assignment).execute()
			firstEvent = calendarService.events().get(calendarId='primary', eventId=self.eventsDictionary[assignment][0]).execute()
			sdt = dateutil.parser.parse(firstEvent['start'].get('dateTime', firstEvent['start'].get('date')))
			if sdt >= due:
				continue
			else:
				summary = firstEvent['summary']
				due_reschedule = dateutil.parser.parse(task['due'])
				less_events = self.populate_event_list(startDate, due_reschedule, assignment)
				timeToComplete2 = self.total_assignment_time(self.eventsDictionary[assignment])
				all_events = self.reschedule_assignments(less_events, name, due, due_reschedule, timeToComplete, timeToComplete2, attentionSpan, breakTime, minWorkTime, travelTime, time1)
				if all_events is not None:
					for event in self.eventsDictionary[assignment]:
						calendarService.events().delete(calendarId='primary', eventId=event).execute()
					taskID = self.add_task(name, due)
					for item in all_events[0]:
						print("Start: " + str(item[0]))
						print("End: " + str(item[1]))
						calendarID = self.add_calendar_event("Work on " + name, "", taskID, item[0], item[1])
					for item in all_events[1]:
						print("Rescheduled start: " + str(item[0]))
						print("Rescheduled end: " + str(item[1]))
						calendarID = self.add_calendar_event(summary, "", assignment, item[0], item[1])
					return
		print("Sorry; could not reschedule anything, unfortunately.")

	def reschedule_assignments(self, less_events, name, due1, due2, timeToComplete1, timeToComplete2, attentionSpan, breakTime, minWorkTime, travelTime, time1):
		scheduled = self.schedule_assignment(0, due1, time1, timeToComplete1, attentionSpan, breakTime, minWorkTime, travelTime, less_events)	
		if scheduled is None:
			return None

		originalWorkSessions, index, events, time1 = scheduled
		travelTime = timedelta(minutes = 15)
		attentionSpan = timedelta(hours = 3)
		breakTime = timedelta(hours = 0.25)
		minWorkTime = timedelta(minutes = 15)

		second_scheduled = self.schedule_assignment(index, due2, time1, timeToComplete2, attentionSpan, breakTime, minWorkTime, travelTime, less_events)
		if second_scheduled is None:
			return

		return (originalWorkSessions, second_scheduled[0])


	def add_assignment(self, name, year, month, day, timeToComplete, attentionSpan, breakTime, startDate, minWorkTime = 15, travelTime = 15):

		due = datetime(year, month, day, tzinfo=tz.tzlocal())
		travelTime = timedelta(minutes = travelTime)
		time1 = None
		if startDate == "":
			time1 = datetime.now(pytz.utc) + travelTime
			time1 = time1.astimezone(tz.tzlocal())
		else:
			time1 = datetime(int(startDate.split("/")[2]), int(startDate.split("/")[0]), int(startDate.split("/")[1]), tzinfo=tz.tzlocal())
			if time1 < (datetime.now(pytz.utc) + travelTime).astimezone(tz.tzlocal()):
				time1 = (datetime.now(pytz.utc) + travelTime).astimezone(tz.tzlocal())

		events = self.populate_event_list(startDate, due)
		timeToComplete = timedelta(hours = timeToComplete)
		attentionSpan = timedelta(hours = attentionSpan)
		breakTime = timedelta(hours = breakTime)
		minWorkTime = timedelta(minutes = minWorkTime)

		workSessions = self.schedule_assignment(0, due, time1, timeToComplete, attentionSpan, breakTime, minWorkTime, travelTime, events)

		if workSessions is None:
			print("Sorry; no time for this with your constraints!")
			pref = raw_input("Sorry; no time for this with your constraints! We recommend that you try decreasing attention span, break time, and min work times. But we can also reschedule other events if possible. Type yes to reschedule.")
			if (pref == "yes"):
				self.find_assignment_to_reschedule(name, startDate, due, timeToComplete, attentionSpan, breakTime, minWorkTime, travelTime, time1)
		else:
			print("Printing time sessions: ")
			taskID = self.add_task(name, due)
			for item in workSessions[0]:
				print("Start: " + str(item[0]))
				print("End: " + str(item[1]))
				calendarID = self.add_calendar_event("Work on " + name, "", taskID, item[0], item[1])

	def change_sleep_times():
		if self.sleepBeginHour > 12:
			print("Currently, you sleep at " + str(sleepBeginHour % 12) + ":" + str(sleepBeginMinute) + " PM and wake up at " + str(sleepEndHour) + ":" + str(sleepEndMinute) + " AM.") #format minute string
		else:
			print("Currently, you sleep at " + str(sleepBeginHour) + ":" + str(sleepBeginMinute) + " AM and wake up at " + str(sleepEndHour) + ":" + str(sleepEndMinute) + " AM.")
		while True:
			try:
				sleepBeginString = raw_input("What time do you normally go to sleep? Use 24-hr time in format HH:MM. Example: 22:00 for 10 PM.\n")
				self.sleepBeginHour = int(sleepBeginString.split(":")[0])
				self.sleepBeginMinute = int(sleepBeginString.split(":")[1])
				if self.sleepBeginHour > 24 or self.sleepBeginHour < 0:
					continue
				if self.sleepBeginMinute > 59 or self.sleepBeginMinute < 0:
					continue
				break
			except ValueError:
				print("Please enter an valid time.")
		while True:
			try:
				sleepEndString = raw_input("What time do you normally wake up? Use 24-hr time in format HH:MM. Example: 8:00 for 8 AM. You can't wake up after noon.\n")
				self.sleepEndHour = int(sleepEndString.split(":")[0])
				self.sleepEndMinute = int(sleepEndString.split(":")[1])
				if self.sleepEndHour >= 12 or self.sleepEndHour < 0:
					continue
				if self.sleepEndMinute > 59 or self.sleepEndMinute < 0:
					continue
				break
			except ValueError:
				print("Please enter a valid time.")
		wakeUpMinutes = sleepEndMinute + 60 * sleepEndHour
		asleepMinutes = sleepBeginMinute + 60 * sleepBeginHour
		self.sleepMinutes = (wakeUpMinutes - asleepMinutes) if wakeUpMinutes > asleepMinutes else (24 * 60 - asleepMinutes + wakeUpMinutes)


def welcome():
	print("\nEnter the number that corresponds to one of the following choices and enter, or only press enter to quit.")
	print("1. List pending tasks")
	print("2. List upcoming events")
	print("3. Add a task and schedule times to work on it")
	print("4. Mark a task as completed")
	print("5. Reset sleep schedule (default is 10 pm bedtime, 7 am wake-up time)")


def main():
	p = Planner()
	test = raw_input("is this a test: ")
	if (test == "y"):
		#p.add_assignment("long assignment", 2017, 1, 10, 10, 2, 2, "1/1/2017", 15, 15)
		p.add_assignment("small assignment", 2017, 1, 2, 6, 2, 1, "1/1/2017", 15, 15)
		#p.print_eventsDictionary()
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
				p.list_pending_tasks(num)
			except ValueError:
				p.list_pending_tasks()
		elif choice == 2:
			numEvents = raw_input("What is the maximum number of events you'd like to see? Press enter for a default of 10.\n")
			try:
				num = int(numEvents)
				p.list_events(num)
			except ValueError:
				p.list_events()
		elif choice == 3:
			assignment = raw_input("Enter name of assignment/task to add: ")
			dueDate = raw_input("Enter the date that this is due (MM/DD/YYYY): ")
			year = dueDate.split("/")[2]
			month = dueDate.split("/")[0]
			day = dueDate.split("/")[1]
			timeToComplete = raw_input("How long will this take to complete in hours? ")
			attentionSpan = raw_input("What is your attention span in hours? ")
			breakTime = raw_input("How much time do you need to break for between study sessions (in hours)? ")
			minWorkTime = raw_input("What is the minimum number of minutes you'd like to work for at a stretch? ")
			travelTime = raw_input("What is the amount of time in minutes required to travel to the next event? This is used as a buffer between events existing on your calendar and study sessions being planned. ")
			startDate = raw_input("Enter the date you would like to start working on this (MM/DD/YYYY) or blank for today: ") #make sure start time is after today
			p.add_assignment(assignment, int(year), int(month), int(day), float(timeToComplete), float(attentionSpan), float(breakTime), startDate, float(minWorkTime), float(travelTime))
		elif choice == 4:
			task = raw_input("What is the name of the task you'd like to mark as completed?\n")
			p.complete_task(task)
		elif choice == 5:
			p.change_sleep_times()

	print("\nThanks for using the planner!")



if __name__ == '__main__':
    main()