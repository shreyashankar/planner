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
from datetime import tzinfo, timedelta, datetime, time
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
		self.sleepBeginMinute = 30
		self.sleepEndMinute = 30
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

		if due != "":
			eventsResult = service.events().list(calendarId='primary', timeMin=now, timeMax = due, singleEvents=True, orderBy='startTime').execute()
		else:
			eventsResult = service.events().list(
			calendarId='primary', timeMin=now, maxResults = numEvents, singleEvents=True,
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

	def populate_event_list(self, startDate, due = "", assignmentToIgnore = ""):
		now = None
		if startDate == "":
			now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
		else:
			now = datetime(int(startDate.split("/")[2]), int(startDate.split("/")[0]), int(startDate.split("/")[1]), tzinfo=tz.tzlocal())
			if now < datetime.now(pytz.utc):
				now = datetime.now(pytz.utc)
			now = now.isoformat()
		if due != "":
			due = due.isoformat()

		events = self.get_next_events(now, due, assignmentToIgnore)
		today = datetime.now(pytz.utc)
		today = today.astimezone(tz.tzlocal())
		event1 = (today + timedelta(days = 15), today + timedelta(days = 16)) #THIS DOESN'T QUITE WORK!
		event2 = (today + timedelta(days = 17), today + timedelta(days = 18))
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

			print("time 1: " + str(time1))
			print("time 2: " + str(time2))

			if time2 < time1 and time2 > start:
				# time2 = time1
				# print("time 1 updated: " + str(time1))
				# print("time 2 updated: " + str(time2))
				time1 = events[index][1] + travelTime
				index += 1
				continue
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
				if workStartTime.hour >= self.sleepEndHour and workEndTime.hour <= self.sleepBeginHour and workEndTime.hour >= self.sleepEndHour:
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
		travelTime = timedelta(minutes = 30)
		attentionSpan = timedelta(hours = 3)
		breakTime = timedelta(hours = 0.25)
		minWorkTime = timedelta(minutes = 15)

		second_scheduled = self.schedule_assignment(index, due2, time1, timeToComplete2, attentionSpan, breakTime, minWorkTime, travelTime, less_events)
		if second_scheduled is None:
			return

		return (originalWorkSessions, second_scheduled[0])

	def modify_parameters_or_reschedule(self, name, due, timeToComplete, attentionSpan, breakTime, time1, minWorkTime, travelTime, startDate):
		as_diff = timedelta(hours = 3) - attentionSpan
		bt_diff = breakTime - timedelta(hours = 0.5)
		mwt_diff = minWorkTime - timedelta(minutes = 15)
		tt_diff = travelTime - timedelta(minutes = 30)
		reprompt = False
		inp = ""

		print("Sorry; no time for this with your constraints! Trying to figure out the best course of action...")

		if max(as_diff, bt_diff, mwt_diff, tt_diff).total_seconds() <= 0:
			pref = raw_input("Sorry; no time for this with your constraints! We can reschedule other study sessions if possible. Type yes to reschedule. ")
			if (pref == "yes"):
				self.find_assignment_to_reschedule(name, startDate, due, timeToComplete, attentionSpan, breakTime, minWorkTime, travelTime, time1)

		if as_diff == max(as_diff, bt_diff, mwt_diff, tt_diff):
			newAttentionSpan = timedelta(hours = 0)
			while newAttentionSpan <= attentionSpan:
				inp = raw_input("Your specified attention span is too low. Please enter a higher attention span in hours, or press enter to reschedule. ")
				if inp == "":
					break
				newAttentionSpan = timedelta(hours = float(inp))
			if inp != "":
				attentionSpan = newAttentionSpan
				reprompt = True
		
		elif bt_diff == max(as_diff, bt_diff, mwt_diff, tt_diff) and reprompt == False:
			newBreakTime = timedelta.max
			while newBreakTime >= breakTime:
				inp = raw_input("Your specified break time is too high. Please enter a lower break time in hours. ")
				if inp == "":
					break
				newBreakTime = timedelta(hours = float(inp))
			if inp != "":
				breakTime = newBreakTime
				reprompt = True
		
		elif mwt_diff == max(as_diff, bt_diff, mwt_diff, tt_diff) and reprompt == False:
			newMinWorkTime = timedelta.max
			while newMinWorkTime >= minWorkTime:
				inp = raw_input("Your specified minimum working time is too high. Please enter a lower minimum working time in minutes. ")
				if inp == "":
					break
				newMinWorkTime = timedelta(minutes = float(inp))
			if inp != "":
				minWorkTime = newMinWorkTime
				reprompt = True

		elif tt_diff == max(as_diff, bt_diff, mwt_diff, tt_diff) and reprompt == False:
			newTravelTime = timedelta.max
			while newTravelTime >= travelTime:
				inp = raw_input("Your specified travel time is too high. Please enter a lower travel time in minutes. ")
				if inp == "":
					break
				newTravelTime = timedelta(minutes = float(inp))
			if inp != "":
				travelTime = newTravelTime
				reprompt = True

		if reprompt:
			self.add_assignment_helper(name, due, timeToComplete, attentionSpan, breakTime, time1, minWorkTime , travelTime)
		else:
			pref = raw_input("Sorry; no time for this with your constraints! We can reschedule other study sessions if possible. Type 'yes' to reschedule. Type 'reprompt' if you want to be reprompted to change paramenters again. ")
			if (pref == "yes"):
				self.find_assignment_to_reschedule(name, startDate, due, self.ttc, self.ats, self.bt, self.mwt, self.tt, time1)
			if (pref == "reprompt"):
				modify_parameters_or_reschedule(name, due, self.ttc, self.ats, self.bt, time1, self.mwt, self.tt, startDate)

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

		timeToComplete = timedelta(hours = timeToComplete)
		attentionSpan = timedelta(hours = attentionSpan)
		breakTime = timedelta(hours = breakTime)
		minWorkTime = timedelta(minutes = minWorkTime)
		self.ttc = timeToComplete
		self.ats = attentionSpan
		self.bt = breakTime
		self.mwt = minWorkTime
		self.tt = travelTime

		if due < time1:
			print("Due date must be after start date. Please retry.")
			return
		elif due - time1 < timeToComplete:
			print("There will never be enough time to complete this because the time to complete the task is too large. Please retry.")
			return

		self.add_assignment_helper(name, due, timeToComplete, attentionSpan, breakTime, time1, minWorkTime , travelTime, startDate)

	def add_assignment_helper(self, name, due, timeToComplete, attentionSpan, breakTime, time1, minWorkTime, travelTime, startDate):
		
		if timeToComplete.total_seconds() < 0 or attentionSpan.total_seconds() <= 0 or breakTime.total_seconds() < 0 or minWorkTime.total_seconds() < 0:
			print("Please make sure parameters are nonzero and attentionSpan is >= 0.")
			return

		events = self.populate_event_list(startDate, due)

		workSessions = self.schedule_assignment(0, due, time1, timeToComplete, attentionSpan, breakTime, minWorkTime, travelTime, events)

		if workSessions is None:
			self.modify_parameters_or_reschedule(name, due, timeToComplete, attentionSpan, breakTime, time1, minWorkTime, travelTime, startDate)
		else:
			print("Printing time sessions: ")
			taskID = self.add_task(name, due)
			for item in workSessions[0]:
				print("Start: " + str(item[0]))
				print("End: " + str(item[1]))
				calendarID = self.add_calendar_event("Work on " + name, "", taskID, item[0], item[1])

	def change_sleep_times(self):
		if self.sleepBeginHour > 12:
			print("Currently, you sleep at " + str(self.sleepBeginHour % 12) + ":" + str(self.sleepBeginMinute) + " PM and wake up at " + str(self.sleepEndHour) + ":" + str(self.sleepEndMinute) + " AM.") #format minute string
		else:
			print("Currently, you sleep at " + str(self.sleepBeginHour) + ":" + str(self.sleepBeginMinute) + " AM and wake up at " + str(self.sleepEndHour) + ":" + str(self.sleepEndMinute) + " AM.")
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
		wakeUpMinutes = self.sleepEndMinute + 60 * self.sleepEndHour
		asleepMinutes = self.sleepBeginMinute + 60 * self.sleepBeginHour
		self.sleepMinutes = (wakeUpMinutes - asleepMinutes) if wakeUpMinutes > asleepMinutes else (24 * 60 - asleepMinutes + wakeUpMinutes)

	def find_range_times(self, meetingTime, num, travelTime, startTime, endTime, time1):
		start = time1
		workSessions = list()
		currentDayStart = (datetime.now(pytz.utc)).astimezone(tz.tzlocal())
		currentDayStart = currentDayStart.replace(hour = startTime.hour, minute = startTime.minute, second = 0)
		if start < currentDayStart:
			start = currentDayStart
		else:
			start += timedelta(hours = 24)
			start = start.replace(hour = startTime.hour, minute = startTime.minute, second = 0)

		while num > 0:
			currentDayStart = start
			currentDayStart = currentDayStart.replace(hour = startTime.hour, second = 0)
			currentDayStart = currentDayStart.replace(minute = startTime.minute)
			currentDayEnd = start
			currentDayEnd = currentDayEnd.replace(hour = endTime.hour, second = 0)
			currentDayEnd = currentDayEnd.replace(minute = endTime.minute)

			events = self.get_next_events((currentDayStart - travelTime).isoformat(), (currentDayEnd + travelTime).isoformat(), "")

			currStart = currentDayStart
			currEnd = currStart + meetingTime

			while currEnd <= currentDayEnd and num >0:
				free = True
				for event in events:
					if event[1] > currentDayStart - travelTime and event[0] < currentDayEnd + travelTime:
						free = False
						break
				if free:
					workSessions.append((currStart, currEnd))
					num -= 1
				currStart += travelTime
				currEnd = currStart + meetingTime

			start += timedelta(hours = 24)

		return workSessions

	def find_top_meeting_times(self, name, startDate, meetingTime, num, travelTime, startTime, endTime):
		travelTime = timedelta(minutes = travelTime)
		meetingTime = timedelta(hours = meetingTime)
		setTime = False
		if startTime != "":
			startTime = time(int(startTime.split(":")[0]), int(startTime.split(":")[1]), tzinfo = tz.tzlocal())
			endTime = time(int(endTime.split(":")[0]), int(endTime.split(":")[1]), tzinfo = tz.tzlocal())
			setTime = True
		time1 = None
		if startDate == "":
			time1 = datetime.now(pytz.utc) + travelTime
			time1 = time1.astimezone(tz.tzlocal())
		else:
			time1 = datetime(int(startDate.split("/")[2]), int(startDate.split("/")[0]), int(startDate.split("/")[1]), tzinfo=tz.tzlocal())
			if time1 < (datetime.now(pytz.utc) + travelTime).astimezone(tz.tzlocal()):
				time1 = (datetime.now(pytz.utc) + travelTime).astimezone(tz.tzlocal())

		if setTime:
			workSessions = self.find_range_times(meetingTime, num, travelTime, startTime, endTime, time1)

		else:
			last = False
			optimal = True if raw_input("Type 'y' if you want to schedule this assignment close to your other events on your calendar (to minimize total travel time for the day). ") == 'y' else False
			workSessions = list()
			start = time1
			index = 0
			events = self.populate_event_list(startDate)
			while num > 0:
				if index < len(events):
					time2 = events[index][0] - travelTime
				else:
					time2 = time1 + timedelta(hours = 1)

				if time2 < time1 and time2 > start:
					time1 = events[index][1] + travelTime
					index += 1
					continue
				if time1.day != time2.day or time2.hour > self.sleepBeginHour:
					if time1.hour < self.sleepEndHour:
						time1 -= timedelta(hours = 24)
					sleepTonightBegin = time1.replace(hour = self.sleepBeginHour, minute = self.sleepBeginMinute, second = 0)
					sleepTonightEnd = sleepTonightBegin + timedelta(minutes = self.sleepMinutes)
					events.insert(index, (sleepTonightBegin, sleepTonightEnd))
					continue
				
				freetime = time2 - time1
				
				if (freetime >= meetingTime):
					workStartTime = time1
					workEndTime = workStartTime + meetingTime
					if last == False and workStartTime.hour >= self.sleepEndHour and workEndTime.hour <= self.sleepBeginHour and workEndTime.hour >= self.sleepEndHour:
						workSessions.append((workStartTime, workEndTime))
						events.insert(index, (workStartTime, workEndTime))
						num -= 1
						if optimal:
							last = True				
					else:
						last = False
					time1 = events[index][1] + travelTime
				
				else:
					last = False
					if index < len(events):
						time1 = events[index][1] + travelTime

				index += 1

		print("Options: ")
		count = 1
		for possibility in workSessions:
			print(str(count) + ": " + str(possibility[0]) + " to " + str(possibility[1]))
			count += 1
		while True:
			time_index = raw_input("Type the number that corresponds to the time you would like to add to your calendar or just press enter to not add anything. ")
			if time_index == "":
				break
			try:
				time_index = int(time_index)
				calendarID = self.add_calendar_event("Meeting with " + name, "", "", workSessions[time_index - 1][0], workSessions[time_index - 1][1])
				break
			except ValueError:
				print("Try again. Type in a valid number.")




def welcome():
	print("\nEnter the number that corresponds to one of the following choices and enter, or only press enter to quit.")
	print("1. List pending tasks")
	print("2. List upcoming events")
	print("3. Add a task and schedule times to work on it")
	print("4. Mark a task as completed")
	print("5. Reset sleep schedule (default is 10 pm bedtime, 7 am wake-up time)")
	print("6. Find optimal times for a meeting with someone.")


def main():
	p = Planner()
	test = raw_input("is this a test: ")
	if (test == "y"):
		p.find_top_meeting_times("Yusha", "", 1, 5, 15, "12:00", "14:00")
		#p.add_assignment("long assignment", 2017, 1, 10, 10, 2, .25, "1/1/2017", 15, 15)
		#p.add_assignment("long assignment", 2017, 1, 10, 10, 2, 2, "1/1/2017", 15, 15)
		#p.add_assignment("small assignment", 2017, 1, 2, 3, 2, 1, "1/1/2017", 15, 15)
		#p.print_eventsDictionary()
		return

	print("Welcome to the planner!")
	while True:
		welcome()
		choice = raw_input("")
		if choice == "":
			break
		try:
			choice = int(choice)
		except ValueError:
			continue
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
		elif choice == 6:
			name = raw_input("Who are you going to meet with? ")
			hours = raw_input("For how long are you going to meet with " + name + " in hours? ")
			try:
				hours = float(hours)
			except ValueError:
				print("Please enter a valid number (float) of hours.")
				continue
			startDate = raw_input("Enter the date you would like to start looking for meeting times (MM/DD/YYYY) or blank if you want to schedule as soon as possible: ")
			numResults = raw_input("How many meeting times do you want the planner to find for you? Enter an integer. ")
			try:
				numResults = int(numResults)
				if numResults < 0:
					test = int("hi")
			except ValueError:
				print("Please enter a valid positive integer.")
				continue
			travelTime = raw_input("What is the amount of time in minutes required to travel to the next event? This is used as a buffer between events existing on your calendar and a meeting time being planned. ")
			try:
				travelTime = float(travelTime)
			except ValueError:
				print("Please enter a valid number (float).")
				continue
			startTime = raw_input("If you want to meet with " + name + " during a certain time in the day, enter the range's start time here (HH:MM) in 24 hour time or blank to continue: ")
			endTime = ""
			if startTime != "":
				endTime = raw_input("Enter the range's end time here (HH:MM) in 24 hour time: ")
			p.find_top_meeting_times(name, startDate, hours, numResults, travelTime, startTime, endTime)


	print("\nThanks for using the planner!")



if __name__ == '__main__':
    main()