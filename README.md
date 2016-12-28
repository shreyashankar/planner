# planner
A "smart" planner that determines when to study, work on assignments, etc.

## Install dependencies
Make sure you have python 2.7 installed. If you don't, you can install it online. For Windows people, check out http://www.howtogeek.com/197947/how-to-install-python-on-windows/!

Install pip:
Mac OSX users: run `sudo easy_install pip` in Terminal.
Windows users: see http://stackoverflow.com/questions/4750806/how-do-i-install-pip-on-windows -- download `get-pip.py` and run `python get-pip.py` as mentioned in stackoverflow.

In terminal or command prompt, run `sudo pip install --upgrade google-api-python-client` or follow instructions in https://developers.google.com/api-client-library/python/start/installation.

## Run python program
Download the contents in this folder as a zip file. Navigate to the folder you downloaded to in Terminal or Command Prompt:
`cd Downloads/planner-master`

Run `python planner.py`!

## Switch users
Remove the file `~/.credentials/tasks-python-quickstart.json` and rerun the program. On Mac OSX, you can execute:
`$ rm ~/.credentials/tasks-python-quickstart.json`

## Common errors

`AttributeError: 'Module_six_moves_urllib_parse' object has no attribute 'urlparse'`
First, find pip's install location with the command:
`$ pip show six | grep "Location:" | cut -d " " -f2`
Next, add the following line to your `~/.bashrc file`, replacing `<pip_install_path>` with pip's install location you found above:
`export PYTHONPATH=$PYTHONPATH:<pip_install_path>`
Finally, reload your `~/.bashrc` file:
`$ source ~/.bashrc`
Credits to Google (https://developers.google.com/google-apps/tasks/quickstart/python) for the nice instructions.

## If you have any errors or comments, please email shreya@cs.stanford.edu!
