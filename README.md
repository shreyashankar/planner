# planner
A "smart" planner that determines when to study, work on assignments, etc. You must have a Google account because it works with Tasks and Calendar.

## Features
- List pending tasks
- List upcoming events
- Schedule a task/assignment and times to work on the task/assignment. You can provide the due date, estimated length of homework (ex: 10 hours), maximum time you can work for at a stretch, and approximately when you sleep. The planner will schedule times for you to work on the assignment such that you complete it before the due date, you can still attend all your other events, and you won't be overwhelmed. 

## Install dependencies
Make sure you have python 2.7 installed. If you don't, you can install it online. For Windows people, check out http://www.howtogeek.com/197947/how-to-install-python-on-windows/!

### pip
Mac OSX users: run `sudo easy_install pip` in Terminal.

Windows users: see http://stackoverflow.com/questions/4750806/how-do-i-install-pip-on-windows -- download `get-pip.py` and run `python get-pip.py` as mentioned in stackoverflow.

### Google API

In terminal or command prompt, run `sudo pip install --upgrade google-api-python-client` or follow instructions in https://developers.google.com/api-client-library/python/start/installation.

### For Windows users who are using built-in machine command prompt, have downloaded Python 2.7 and setup pip:

- You must unzip or otherwise access planner-master internal directory in order for cmd to recognize planner-master in your Downloads folder.
- ImportError no pytz: `pip install pytz`
- ImportError no dateutil-parser: `pip install python-dateutil`
- ImportError no httplib2: `pip install httplib2`

Credits to Valerie Ding for extra Windows instructions.

## Run python program
Download the contents in this folder as a zip file. Navigate to the folder you downloaded to in Terminal or Command Prompt:

`cd Downloads/planner-master`

Run `python planner.py`! You will be prompted to give calendar and task permissions to planner.

## Switch users
Remove the files `~/.credentials/tasks-python-quickstart.json` and `~/.credentials/calendar-python-quickstart.json` and rerun the program. 

On Mac OSX, you can execute:

`$ rm ~/.credentials/tasks-python-quickstart.json`

`$ rm ~/.credentials/calendar-python-quickstart.json`

## Common errors

### `AttributeError: 'Module_six_moves_urllib_parse' object has no attribute 'urlparse'`

First, find pip's install location with the command:

`$ pip show six | grep "Location:" | cut -d " " -f2`

Next, add the following line to your `~/.bashrc file`, replacing `<pip_install_path>` with pip's install location you found above:

`export PYTHONPATH=$PYTHONPATH:<pip_install_path>`

Finally, reload your `~/.bashrc` file:

`$ source ~/.bashrc`

Credits to Google (https://developers.google.com/google-apps/tasks/quickstart/python) for the nice instructions.

### no 'pytz'

Run `pip install pytz`.

### raw_input not defined

This means you are in python 3. Replace all instances of `raw_input` in the code with just `input`.

## If you have any errors or comments, please email shreya@cs.stanford.edu!
