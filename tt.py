import argparse
import json
import os
import time

# TODO:
# * Make "tt" without a subcommand print the same output as "tt info"
# * Let "tt info" print the duration of each individual activity on the stack
#   e.g. for work / break
#   work for 4h
#   break for 20m
# * Handle DB_PATH properly: https://pypi.org/project/appdirs/
# * Add activity completion: https://argcomplete.readthedocs.io/en/latest/

DB_PATH = r"C:\Users\Joel\ttDb.json"

def getActivites(db):
    activities = []
    for activity in db:
        activities.append(activity["name"])

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

def infoCommand(args, db):
    if len(db) == 0:
        print("No activities logged.")
    else:
        for activity in reversed(db):
            if not "finished" in activity:
                print("Current activity: {}".format(getActivityName(activity["name"])))
                print("Begun {} ago.".format(secondsToStr(time.time() - activity["started"])))
                break
        else:
            print("No current activity.")

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
        print(popStart, len(db))
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

def main():
    parser = argparse.ArgumentParser(prog="tt", description="Time tracker")
    subparsers = parser.add_subparsers(dest="command", help="command")
    subparsers.required = True

    parserInfo = subparsers.add_parser("info", help="Print current activity (and duration)")
    parserInfo.set_defaults(func=infoCommand)

    parserPush = subparsers.add_parser("push", help="push activity on the activity stack")
    parserPush.add_argument("activity", nargs="+", help="A list of activities")
    parserPush.add_argument("--comment", "-c", help="Additional comment for the activity")
    parserPush.set_defaults(func=pushCommand)

    parserPop = subparsers.add_parser("pop", help="pop activity from the activity stack")
    parserPop.add_argument("activity", nargs="?", help="May be an activity by name")
    parserPop.add_argument("--comment", "-c", help="Additional comment for the activity")
    parserPop.set_defaults(func=popCommand)

    parserActivities = subparsers.add_parser("activities", help="List known activities")
    parserActivities.set_defaults(func=activitiesCommand)

    args = parser.parse_args()

    if os.path.isfile(DB_PATH):
        with open(DB_PATH) as f:
            db = json.load(f)
    else:
        db = []

    args.func(args, db)

if __name__ == "__main__":
    main()
