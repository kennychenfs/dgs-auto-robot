import requests
import subprocess
from time import sleep
user=$USER
passward=$PASSWARD
r = requests.get('https://www.dragongoserver.net/login.php?quick_mode=1&userid='+user+'&passwd='+passward)#replace user and passward
cookies=r.cookies
while 1:
	r = requests.get('https://www.dragongoserver.net/quick_status.php?quick_mode=1',cookies=cookies)
	lines=r.text.splitlines()
	game_id_list=[]
	for i in lines:
		if i[1] is 'G':
			game_id_list.append(i[5:12])# saved in str type
	games={}
	for game_id in game_id_list:
		if game_id != '1276521':
			info=eval(requests.get('https://www.dragongoserver.net/quick_do.php?obj=game&cmd=info&gid='+game_id,cookies=cookies).text)
			r = requests.get('https://www.dragongoserver.net/sgf.php?gid='+game_id)
			games[game_id]=[r.text,info['move_id'],info['move_color']]
	sz13moves={}
	sz19moves={}
	for game_id,(game,move_id,myturn) in games.items():
		index=game.find('SZ[')# SZ[13]
		size=int(game[index+3:index+5])
		
		moves=[]# in the format like 'B Q4'
		
		lines=game.splitlines()
		for i in lines:
			if len(i)<3:
				continue
			if i[0]==';':
				if i[1]=='W' or i[1]=='B':
					i=i[1:]
				elif i[1]=='F':
					continue
				else:
					i=i[6:]
				a=ord(i[2]);b=ord(i[3])-96
				moves.append(i[0]+' '+(chr(a-32) if a<105 else chr(a-31)) + str(size+1-b))
			elif i[0:2]=='AB':
				index=2
				while len(i)-3>=index and i[index]=='[':
					a=ord(i[index+1]);b=ord(i[index+2])-96
					moves.append('B '+(chr(a-32) if a<105 else chr(a-31)) + str(size+1-b))
					index+=4
		if size is 13:
			sz13moves[game_id]=[moves,myturn,move_id]
		else:
			sz19moves[game_id]=[moves,myturn,move_id]
	# size 19 first
	if sz19moves!={}:
		a='time_settings 0 11 1\n'#If you want to set time limit
		for _,(i,myturn,_1) in sz19moves.items():
			a+='clear_board\nboardsize 19\n'
			for j in i:
				a+='play '+j+'\n'
			a+='genmove '+myturn+'\nshowboard\n'
		command=''#$Your robot command
		with open('/tmp/test','w') as f:
			f.write(a)
		with open('/tmp/test','r') as f:
			result=subprocess.Popen(command,shell=True,stdin=f,stdout=subprocess.PIPE).stdout
		result=result.read().decode().splitlines()
		play_moves=[]
		for i in result:
			if len(i)>2 and i[0]=='=':
				play_moves.append(i[2:])
		for i,play in zip(sz19moves.keys(),play_moves):
			print (i,play)
			move_id=sz19moves[i][2]
			r = requests.get('https://www.dragongoserver.net/quick_do.php?obj=game&cmd=move&gid='+i+'&move='+play.lower()+'&fmt=board&move_id='+str(move_id),cookies=cookies)
	#size 13
	if sz13moves!={}:
		a='time_settings 0 11 1\n'#If you want to set time limit
		for _,(i,myturn,_1) in sz13moves.items():
			a+='clear_board\nboardsize 13\n'
			for j in i:
				a+='play '+j+'\n'
			a+='genmove '+myturn+'\nshowboard\n'
		command=''#$Your robot command
		with open('/tmp/test','w') as f:
			f.write(a)
		with open('/tmp/test','r') as f:
			result=subprocess.Popen(command,shell=True,stdin=f,stdout=subprocess.PIPE).stdout
		result=result.read().decode().splitlines()
		play_moves=[]
		for i in result:
			if len(i)>2 and i[0]=='=':
				play_moves.append(i[2:])
		for i,play in zip(sz13moves.keys(),play_moves):
			print (i,play)
			move_id=sz13moves[i][2]
			r = requests.get('https://www.dragongoserver.net/quick_do.php?obj=game&cmd=move&gid='+i+'&move='+play.lower()+'&fmt=board&move_id='+str(move_id),cookies=cookies)
	sleep(60)
