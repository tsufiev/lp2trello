#!./venv/bin/python

LP_CACHEDIR = "./"

TRELLO_LIST_BACKLOG = 'Backlog'
TRELLO_LIST_IN_PROGRESS = 'In progress'
TRELLO_LIST_REVIEW = 'Review'
TRELLO_LIST_QA_VERIFICATION = 'QA verification'
TRELLO_LIST_DONE = 'Done'

from settings import *

import re
from launchpadlib.launchpad import Launchpad
from launchpadlib.credentials import Credentials
from trello import TrelloClient


def describe(object):
    print 'collections:'
    print object.lp_collections
    print 'entries:'
    print object.lp_entries
    print 'attibutes:'
    print object.lp_attributes
    print 'operations:'
    print object.lp_operations

def get_trello_list(lists, name):
    list = [list for list in lists if list.name == name]
    if len(list) == 0:
        print "No Trello list found" +  name
        exit(0)
    return list[0]

# login to lauchpad
lp = Launchpad.login_anonymously('test', 'production', LP_CACHEDIR)

# login to trello
tr = TrelloClient(api_key=TRELLO_KEY, api_secret=TRELLO_SECRET, token=TRELLO_TOKEN, token_secret=TRELLO_SECRET)

# Extract Trello board
all_boards = tr.list_boards()
boards = [board for board in all_boards if board.name == TRELLO_BOARD]
if len(boards) == 0:
    print "No Trello board found:" + TRELLO_BOARD
    exit(0)
board = boards[0]
print 'Found Board:', board #, dir(board)

# Extract Trello lists
lists = board.open_lists()
list_backlog = get_trello_list(lists, TRELLO_LIST_BACKLOG);
list_in_progress = get_trello_list(lists, TRELLO_LIST_IN_PROGRESS);
list_review = get_trello_list(lists, TRELLO_LIST_REVIEW);
list_qa_verification = get_trello_list(lists, TRELLO_LIST_QA_VERIFICATION);
list_done = get_trello_list(lists, TRELLO_LIST_DONE);
print 'Backlog:', list_backlog
print 'In progress:', list_in_progress
print 'Review:', list_review
print 'QA Verification:', list_qa_verification
print 'Done:', list_done, list_done.id
#print dir(list_done)

# Extract all the cards in all lists for specific trello board
bugs = dict()
cards = board.open_cards()
for card in cards:
    groups = re.search('(\d{7})', card.name);
    if not (groups is None):
        bugs[groups.group(0)] = card
print 'Read Trelllo cards', bugs.keys()

# read Lauchpads project and its bugs
project = lp.projects[LP_PROJECT]
#describe(project);
try:
    tasks = project.searchTasks(tags=LP_TAG)
except:
    print 'No bugs found'

# find new bugs and put to trello
for task in tasks:
    bug = task.bug
    bug_id = str(bug.id)
    print 'LP bug', bug_id, bug.title, task.status, task.assignee
    if not (bug_id in bugs):
        print 'Add to trello:',bug_id
        card = list_backlog.add_card('Bug '+bug_id+': '+task.bug.title, bug.web_link)
        bugs[bug_id] = card

    card = bugs[bug_id]
    #print bug_id, task.status, task.assignee, card
    if task.status == 'Fix Committed':
        card.change_list(list_qa_verification.id)
    elif task.status == 'Fix Released':
        card.change_list(list_done.id)
    elif task.status == 'Review':
        card.change_list(list_review.id)
    elif (task.status == 'New' and task.assignee) or (task.status == 'In Progress'):
        card.change_list(list_in_progress.id)
    elif task.status == 'New' and (task.assignee is None):
        card.change_list(list_backlog.id)

print "Done"
