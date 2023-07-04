# This python script is for KataGo. You might need to change some of the code to make it work for other bots.
import io
import os
import pickle
import re
import subprocess
import time

import requests

import infoProcess
import sgfProcess

using_ray = True
main_dir = "/home/kenny/Desktop/"
bot_name = "katago"
userid = "Katago"
passwd = "..."
# Should be careful if you want to save password locally as I do.
try:
    import ray
except:
    using_ray = False

opps_to_recommend = []
pass_games = []
recommends = {}  # {game id:'Q16',...} All games are saved here

if os.path.exists(os.path.join(main_dir, "dgs_bots", bot_name, f"dgs_recommended")):
    with open(
        os.path.join(main_dir, "dgs_bots", bot_name, f"dgs_recommended"), "r"
    ) as f:
        recommended = eval(f.read())
else:
    recommended = []

if os.path.exists(
    os.path.join(main_dir, "dgs_bots", bot_name, f"lastProcessedFinishedGameID")
):
    with open(
        os.path.join(main_dir, "dgs_bots", bot_name, f"lastProcessedFinishedGameID"),
        "r",
    ) as f:
        lastProcessedFinishedGameID = int(f.read())
else:
    lastProcessedFinishedGameID = None


def login_and_get_cookies():
    r = requests.get(
        f"https://www.dragongoserver.net/login.php?quick_mode=1&userid={userid}&passwd={passwd}"
    )
    if r.status_code != 200:
        print("Error logging in, retrying...")
        print(r.text)
        time.sleep(5)
        return login_and_get_cookies()
    with open(os.path.join(main_dir, f"dgs_cookies_{bot_name}.pkl"), "wb") as f:
        pickle.dump(r.cookies, f)
    return r.cookies


# replace this after you get the bot's id
MYID = eval(
    requests.get("https://www.dragongoserver.net/quick_do.php?obj=user&cmd=info").text
)["id"]

try:
    with open(os.path.join(main_dir, f"dgs_cookies_{bot_name}.pkl"), "rb") as f:
        cookies = pickle.load(f)
    r = requests.get(
        "https://www.dragongoserver.net/quick_status.php?quick_mode=1", cookies=cookies
    )
    if r.text.startswith("[#Error:"):
        raise Exception
except:
    print("retrying login...")
    cookies = login_and_get_cookies()
    r = requests.get(
        "https://www.dragongoserver.net/quick_status.php?quick_mode=1", cookies=cookies
    )

if os.path.exists(os.path.join(main_dir, "dgs_bots", bot_name, f"searchInfo")):
    searchInfo = infoProcess.loadInfo(
        os.path.join(main_dir, "dgs_bots", bot_name, f"searchInfo")
    )
else:
    searchInfo = {}


def processFinishedGames():
    # Try process finished games

    finishedGames = eval(
        requests.get(
            "https://www.dragongoserver.net/quick_do.php?obj=game&cmd=list&view=finished",
            cookies=cookies,
        ).text
    )
    assert finishedGames["list_header"][0] == "id"
    finishedIDs = [
        finishedGames["list_result"][i][0]
        for i in range(len(finishedGames["list_result"]))
    ]
    blackIDIndex = finishedGames["list_header"].index("black_user.id")
    whiteIDIndex = finishedGames["list_header"].index("white_user.id")
    blackIDs = [
        finishedGames["list_result"][i][blackIDIndex]
        for i in range(len(finishedGames["list_result"]))
    ]
    whiteIDs = [
        finishedGames["list_result"][i][whiteIDIndex]
        for i in range(len(finishedGames["list_result"]))
    ]
    for gameID, blackID, whiteID in zip(finishedIDs, blackIDs, whiteIDs):
        if gameID == lastProcessedFinishedGameID:
            break
        sgf = sgfProcess.downloadsgf(gameID)
        sgfProcess.addInfo(sgf, searchInfo)
        sstream = io.StringIO("")
        sgf.recursivePrintSgf(sstream)
        subject = f"Game {gameID} analysis from bot {bot_name}"
        message = f"The bot {bot_name} has collected search information while playing the game {gameID} with you and has created a sgf. The main branch of the sgf contains the winrate and lead for each of the bot's moves as well as recommend for your moves. Copy the sgf below and paste it into any viewer to see the analysis. If you have any advice about this feature, please drop me a mail.\n\n"
        message += sstream.read()
        if blackID == MYID:
            requests.get(
                f"https://www.dragongoserver.net/quick_do.php?obj=message&cmd=send_msg&ouid={whiteID}&subj={subject}&msg={message}",
                cookies=cookies,
            )
        else:
            requests.get(
                f"https://www.dragongoserver.net/quick_do.php?obj=message&cmd=send_msg&ouid={blackID}&subj={subject}&msg={message}",
                cookies=cookies,
            )


lines = r.text.splitlines()
game_id_list = []
message_id_to_remove = []
end_game_message_list = []
message_list = []
for i in lines:
    m = re.match(r"'G',[^\d]*(\d+),", i)
    if m is not None:
        game_id_list.append(m.group(1))  # saved in str type
        continue
    m = re.match(r"'M',[^\d]*(\d+),[^\,]*,'([^']*)',", i)
    if m is not None:
        message_id = m.group(1)
        message = m.group(2)
        if message == "Game result":
            message_id_to_remove.append(message_id)
            end_game_message_list.append(message_id)
        elif message == "Your waiting room game has been joined.":
            message_id_to_remove.append(message_id)
        elif message == "Game invitation accepted":
            message_id_to_remove.append(message_id)
        continue
for message_id in end_game_message_list:
    r = eval(
        requests.get(
            "https://www.dragongoserver.net/quick_do.php?obj=message&cmd=info&mid="
            + message_id,
            cookies=cookies,
        ).text
    )
    try:
        recommended.pop(str(r["game_id"]))
    except KeyError:
        pass
if message_id_to_remove != []:
    r = "https://www.dragongoserver.net/quick_do.php?obj=message&cmd=delete_msg&mid="
    for message_id in message_id_to_remove:
        r = r + message_id + ","
    r = r[:-1]
    print(r)
    r = requests.get(r, cookies=cookies)
# start
print(f"{bot_name} is running, game list:", game_id_list)
if game_id_list == []:
    exit(0)
games = {}
if using_ray:

    @ray.remote
    def getsgf(url):
        return requests.get(url).text

    @ray.remote
    def getinfo(url):
        return eval(requests.get(url, cookies=cookies).text)

    results = ray.get(
        [
            getinfo.remote(
                f"https://www.dragongoserver.net/quick_do.php?obj=game&cmd=info&gid={game_id}"
            )
            for game_id in game_id_list
        ]
        + [
            getsgf.remote(f"https://www.dragongoserver.net/sgf.php?gid={game_id}")
            for game_id in game_id_list
        ]
    )
else:

    def getsgf(url):
        return requests.get(url).text

    def getinfo(url):
        return eval(requests.get(url, cookies=cookies).text)

    results = [
        getinfo(
            f"https://www.dragongoserver.net/quick_do.php?obj=game&cmd=info&gid={game_id}"
        )
        for game_id in game_id_list
    ] + [
        getsgf(f"https://www.dragongoserver.net/sgf.php?gid={game_id}")
        for game_id in game_id_list
    ]
infos = results[: len(game_id_list)]
sgfs = results[-len(game_id_list) :]
combined = list(zip(infos, sgfs, game_id_list))
combined.sort(key=lambda x: x[0]["size"])
# sort by board size so that KataGo will spend less time switching between different board sizes
res = []
for info, sgf, game_id in combined:
    res.append([info, sgf, game_id])
infos, sgfs, game_id_list = zip(*res)
for info, sgf, game_id in zip(infos, sgfs, game_id_list):
    if sgf.find(";W[]\n;B[]") != -1 or sgf.find(";B[]\n;W[]") != -1:
        pass_games.append(game_id)
        continue
    with open(f"/tmp/{game_id}", "w") as f:
        f.write(sgf)
    games[game_id] = [
        info["move_id"],
        info["move_color"],
        info["move_opp"],
        info["size"],
        info["handicap"],
    ]


def play(games, command):
    if games == {}:
        return
    commands = ""
    for game_id, (move_id, myturn, _, _, _) in games.items():
        commands += f"loadsgf /tmp/{game_id}\n"
        commands += f"genmove_debug {myturn}\n"
    with open(f"/tmp/dgs_bot_{bot_name}_commands", "w") as f:
        f.write(commands)
    with open(f"/tmp/dgs_bot_{bot_name}_commands", "r") as f:
        result = subprocess.Popen(
            command, shell=True, stdin=f, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    print("bot started")
    stderr = result.stderr.read()
    stdout = result.stdout.read()
    stderr = str(stderr, "utf-8")
    stdout = str(stdout, "utf-8")
    print(stderr)
    visits = []
    play_moves = []
    winrates = []
    leads = []
    num = 0
    index = 0
    ids = list(games.keys())
    while 1:
        # maybe using regex is better
        # This section differs between different bots
        indexvisit = stderr.find("Root visits:", index)
        if indexvisit == -1:
            break
        visits.append(stderr[indexvisit + 13 : stderr.find("\n", indexvisit)])
        index = stderr.find("Tree:\n:", index + 1)
        leads.append(
            float(stderr[stderr.find("L", index) + 1 : stderr.find(")", index)])
        )
        winrates.append(
            str(
                round(
                    (
                        float(
                            stderr[
                                stderr.find("W", index) + 1 : stderr.find("S", index)
                            ].strip("c ")
                        )
                        + 100
                    )
                    / 2,
                    2,
                )
            )
            + "%"
        )
        recommend_for_last_move = stderr[
            stderr.find("--  ", index) + 4 : stderr.find("--  ", index) + 14
        ]
        recommends[ids[num]] = recommend_for_last_move.split()[1]
        num += 1
    for line in stdout.splitlines():
        if line.strip("= ") == "":
            continue
        play_moves.append(line.strip("= "))
    print(visits)
    print(winrates)
    to_get = []
    for id, play, winrate, lead in zip(ids, play_moves, winrates, leads):
        infoProcess.addInfo(
            searchInfo,
            id,
            games[id][0] + 1 - games[id][4],
            winrate,
            lead,
            recommends[id],
        )
        if lead >= 0:  # katago's output means how much it leads
            lead = "it leads by " + str(lead).strip()
        else:
            lead = "you lead by " + str(-lead).strip()
        print(lead, end="")
        print("\n", id, play, recommends[id], winrate)
        move_id = games[id][0]
        opp_id = games[id][2]
        if play == "resign":
            to_get.append(
                f"https://www.dragongoserver.net/quick_do.php?obj=game&cmd=resign&gid={id}&move_id={move_id}"
            )
            recommended.pop(id)
            continue
        url = f"https://www.dragongoserver.net/quick_do.php?obj=game&cmd=move&gid={id}&move={play.lower()}&fmt=board&move_id={move_id}&msg="
        try:
            recommend_for_last_move = recommended[id]
        except KeyError:
            print("Key error")
            if opp_id in opps_to_recommend:
                url += f"Katago's winrate:{winrate}\nKatago thinks {lead} mokus."
            else:
                url += "I provide a service of sending some information, including winrate, how many mokus the bot leads, and recommend for your last move. It's a little annoying indeed. If you want to enable them, send a mail to inform me."
        else:
            print(opp_id in opps_to_recommend)
            if opp_id in opps_to_recommend:
                url += f"Katago's winrate:{winrate}\nKatago thinks {lead} mokus and that you should play at {recommend_for_last_move} last move."
            else:
                url = url[:-5]
        to_get.append([url, id])

    print("\n".join([f"'{id}','{url}'" for url, id in to_get]))
    if using_ray:

        @ray.remote
        def get(url):
            if requests.get(url, cookies=cookies).status_code == 200:
                return True
            return False

        results = ray.get([get.remote(url) for url, _ in to_get])
        for result, id in zip(results, ids):
            if result:
                recommended[id] = recommends[id]
    else:
        for url, id in to_get:
            if requests.get(url, cookies=cookies).status_code == 200:
                recommended[id] = recommends[id]


processFinishedGames()

play(games, "your command here")
with open(os.path.join(main_dir, f"dgs_recommended_{bot_name}"), "w") as f:
    f.write(str(recommended))

# save search info
infoProcess.saveInfo(
    searchInfo, os.path.join(main_dir, "dgs_bots", bot_name, f"searchInfo")
)

bg = "\x1b[48;5;"
color = "\x1b[38;5;"
end = "m"
reset = "\x1b[0m"
if pass_games != []:
    print(
        bg + "1" + end + "WARNING!!!" + reset + "here's the games which include pass:",
        pass_games,
    )
