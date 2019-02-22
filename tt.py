import argparse
import json
import os
import time

import appdirs
#import argcomplete

DB_PATH = os.path.join(appdirs.user_data_dir("tt", "", roaming=True), "ttDb.json")
#DB_PATH = r"ttDb_test.json"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def getActivites(db):
    activities = set()
    for activity in db:
        activities.update(activity["name"])
    return list(activities)

def getActivityName(activityName):
    return " / ".join(activityName)

def secondsToStr(s):
    s = int(s + 0.5)
    h = int(s/3600)
    s -= h * 3600
    m = int(s/60)
    s -= m * 60
    ret = "{}s".format(s)
    if m > 0:
        ret = "{}m ".format(m) + ret
    if h > 0:
        ret = "{}h ".format(h) + ret
    return ret

def writeDb(db):
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=4)

def findActivityParents(db, activityIndex):
    parents = []
    for subListLen in range(len(db[activityIndex]["name"]), 0, -1):
        subName = db[activityIndex]["name"][:subListLen]
        for i in range(activityIndex, -1, -1):
            if not "finished" in db[i] and db[i]["name"] == subName:
                parents.append(db[i])
    parents.reverse()
    return parents

def infoCommand(args, db):
    if len(db) == 0:
        print("No activities logged.")
    else:
        activities = None
        for _i, activity in enumerate(reversed(db)):
            i = len(db) - 1 - _i
            if not "finished" in activity:
                activities = findActivityParents(db, i)
                break
        else:
            print("No current activity.")

        if activities:
            print("Current activity: {}".format(getActivityName(activities[-1]["name"])))
            for activity in activities:
                print("{} for {}".format(getActivityName(activity["name"]), secondsToStr(time.time() - activity["started"])))

def pushActivity(activityName, db, comment=None):
    parent = None
    for activity in reversed(db):
        if not "finished" in activity:
            parent = activity
            break

    name = []
    if parent:
        name = parent["name"][:]
    name.append(activityName)

    activity = {
        "name": name,
        "started": int(time.time()),
    }
    if comment:
        activity["comment"] = comment

    db.append(activity)

def pushCommand(args, db):
    for i, activity in enumerate(args.activity):
        if i == len(args.activity) - 1: # only add comment for last element
            pushActivity(activity, db, args.comment)
        else:
            pushActivity(activity, db)

    writeDb(db)

    infoCommand(args, db)

def popCommand(args, db):
    popStart = None
    for _i, activity in enumerate(reversed(db)):
        i = len(db) - 1 - _i
        if not "finished" in activity and (not args.activity or args.activity == activity["name"][-1]):
            popStart = i
            break

    if popStart != None:
        for i in range(popStart, len(db)):
            if not "finished" in db[i]:
                db[i]["finished"] = int(time.time())
                print("Finished activity {} after {}".format(getActivityName(db[i]["name"]), secondsToStr(time.time() - db[i]["started"])))

        writeDb(db)

        infoCommand(args, db)
    else:
        print("No current activity.")

def activitiesCommand(args, db):
    activities = map(lambda act: getActivityName(act["name"]), db)
    for activityName in sorted(activities):
        print(activityName)

class ActivityCompleter(object):
    def __init__(self, db):
        self.activities = getActivites(db)

    def __call__(self, **kwargs):
        return self.activities

def main():
    if os.path.isfile(DB_PATH):
        with open(DB_PATH) as f:
            db = json.load(f)
    else:
        db = []

    parser = argparse.ArgumentParser(prog="tt", description="Time tracker")
    parser.set_defaults(func=infoCommand)
    subparsers = parser.add_subparsers(dest="command", help="command")

    parserInfo = subparsers.add_parser("info", help="Print current activity (and duration)")
    parserInfo.set_defaults(func=infoCommand)

    activityCompleter = ActivityCompleter(db)

    parserPush = subparsers.add_parser("push", help="push activity on the activity stack")
    parserPush.add_argument("activity", nargs="+", help="A list of activities")#.completer = activityCompleter
    parserPush.add_argument("--comment", "-c", help="Additional comment for the activity")
    parserPush.set_defaults(func=pushCommand)

    parserPop = subparsers.add_parser("pop", help="pop activity from the activity stack")
    parserPop.add_argument("activity", nargs="?", help="May be an activity by name")#.completer = activityCompleter
    parserPop.add_argument("--comment", "-c", help="Additional comment for the activity")
    parserPop.set_defaults(func=popCommand)

    parserActivities = subparsers.add_parser("activities", help="List known activities")
    parserActivities.set_defaults(func=activitiesCommand)

    #argcomplete.autocomplete(parser)
    args = parser.parse_args()
    args.func(args, db)

if __name__ == "__main__":
    main()
