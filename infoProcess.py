# save search info
# {'game_id':[{'winrate':'100', 'lead':'100', 'visit':'100'},None,{...},...],...}


def addInfo(info, gameID, moveIDMinusHandicap, winrate=None, lead=None, recommend=None):
    if gameID not in info:
        info[gameID] = []
    while moveIDMinusHandicap > len(info[gameID]):
        info[gameID].append(None)

    moveIDMinusHandicap -= 1
    if info[gameID][moveIDMinusHandicap] == None:
        info[gameID][moveIDMinusHandicap] = {}
    if winrate != None:
        info[gameID][moveIDMinusHandicap]["winrate"] = str(round(float(winrate)))
    if lead != None:
        info[gameID][moveIDMinusHandicap]["lead"] = str(round(float(lead), 1))
    if recommend != None:
        info[gameID][moveIDMinusHandicap]["recommend"] = str(recommend)
    return info


def loadInfo(filename):
    with open(filename, "r") as f:
        info = eval(f.read())
    return info


def saveInfo(info, filename):
    with open(filename, "w") as f:
        f.write(str(info))
