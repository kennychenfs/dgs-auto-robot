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
import os
import re
import requests
import subprocess

r = requests.get(
    f"https://www.dragongoserver.net/login.php?quick_mode=1&userid={userid}&passwd={passwd}"
)
cookies = r.cookies
opps_to_recommend = []
pass_games = []
recommends = {}  # {game id:'Q16',...} All games are saved here

with open(os.path.join(main_dir, f"dgs_recommended_{bot_name}"), "r") as f:
    recommended = eval(f.read())
r = requests.get(
    "https://www.dragongoserver.net/quick_status.php?quick_mode=1", cookies=cookies
)
lines = r.text.splitlines()
game_id_list = []
message_id_to_remove = []
end_game_message_list = []
message_list = []
for i in lines:
    m = re.match(r"'G',[^\d]*(\d+),", i)
    if m is not None:
        game_id_list.append(int(m.group(1)))  # saved in str type
        continue
    m = re.match(r"'M',[^\d]*(\d+),[^\,]*,'([^']*)',", i)
    if m is not None:
        message_id = m.group(1)
        message = m.group(2)
        if message == "Game result":
            message_id_to_remove.append(message_id)
            end_game_message_list.append(message_id)
        elif message == "Your waiting room game has been joined":
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
    with open("/tmp/" + game_id, "w") as f:
        f.write(sgf)
    games[game_id] = [info["move_id"], info["move_color"], info["move_opp"]]


def play(games, command):
    if games == {}:
        return
    recommend_for_last_move = ""
    for game_id, (move_id, myturn, _) in games.items():
        recommend_for_last_move += "loadsgf /tmp/" + game_id + "\n"
        recommend_for_last_move += "genmove_debug " + myturn + "\n"
    with open(f"/tmp/dgs_bot_{bot_name}_commands", "w") as f:
        f.write(recommend_for_last_move)
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
                                stderr.find("W", index)
                                + 1 : stderr.find("S", index)
                                - 2
                            ]
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
            stderr.find("--  ", index) + 4 : stderr.find("\n", index)
        ]
        recommends[ids[num]] = recommend_for_last_move.split()[1]
        num += 1
    for line in stdout.split("\n"):
        if line.strip("= ") == "":
            continue
        play_moves.append(line.strip("= "))
    print(visits)
    print(winrates)
    to_get = []
    for id, play, winrate, lead in zip(ids, play_moves, winrates, leads):
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

    print("\n".join(to_get))
    if using_ray:

        @ray.remote
        def get(url, id):
            if requests.get(url, cookies=cookies).status_code == 200:
                recommended[id] = recommends[id]

        ray.get([get.remote(url, id) for url, id in to_get])
    else:
        for url, id in to_get:
            if requests.get(url, cookies=cookies).status_code == 200:
                recommended[id] = recommends[id]


play(games, "your command here")
with open(os.path.join(main_dir, f"dgs_recommended_{bot_name}"), "w") as f:
    f.write(str(recommended))

bg = "\x1b[48;5;"
color = "\x1b[38;5;"
end = "m"
reset = "\x1b[0m"
if pass_games != []:
    print(
        bg + "1" + end + "WARNING!!!" + reset + "here's the games which include pass:",
        pass_games,
    )
