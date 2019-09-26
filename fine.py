import requests
import subprocess
from time import sleep
r = requests.get('https://www.dragongoserver.net/login.php?quick_mode=1&userid=LeelaZeroVisit1&passwd=fRrnNftaeXFqN7P')
cookies=r.cookies
games_to_recommend=['1289886','1276521','1289851','1289995','1290003','1290249','1289880','1289879']
while 1:
	r = requests.get('https://www.dragongoserver.net/quick_status.php?quick_mode=1',cookies=cookies)
	lines=r.text.splitlines()
	game_id_list=[]
	for i in lines:
		if i[1] == 'G':
			game_id_list.append(i[5:12])# saved in str type
	print(game_id_list)
	games={}
	for game_id in game_id_list:
		info=eval(requests.get('https://www.dragongoserver.net/quick_do.php?obj=game&cmd=info&gid='+game_id,cookies=cookies).text)
		r = requests.get('https://www.dragongoserver.net/sgf.php?gid='+game_id)
		games[game_id]=[r.text,info['move_id'],info['move_color']]
	sz19moves={}
	sz13moves={}
	sz9moves={}
	for game_id,(game,move_id,myturn) in games.items():
		index=game.find('SZ[')# SZ[13] or SZ[9]
		size=int(game[index+3:game.find(']',index)])
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
				if i[2]==']':
					continue
				a=ord(i[2]);b=ord(i[3])-96
				moves.append(i[0]+' '+(chr(a-32) if a<105 else chr(a-31)) + str(size+1-b))
			elif i[0:2]=='AB':
				index=2
				while len(i)-3>=index and i[index]=='[':
					a=ord(i[index+1]);b=ord(i[index+2])-96
					moves.append('B '+(chr(a-32) if a<105 else chr(a-31)) + str(size+1-b))
					index+=4
		if size == 19:
			sz19moves[game_id]=[moves,myturn,move_id]
		elif size == 13:
			sz13moves[game_id]=[moves,myturn,move_id]
		else:
			sz9moves[game_id]=[moves,myturn,move_id]
	recommends={}#{id:'Q16',...} All games to save are here
	with open('/home/kenny/Desktop/dgs_recommended','r') as f:
		recommended=eval(f.read())
	# size 19 first
	if sz19moves!={}:
		a='time_settings 0 6 1\n'
		for _,(i,myturn,_1) in sz19moves.items():
			a+='clear_board\n'
			for j in i:
				a+='play '+j+'\n'
			a+='genmove '+myturn+'\nshowboard\n'
		command='/home/kenny/Desktop/leela-zero/build/leelaz -g -w /home/kenny/Desktop/lzbest.gz -t 16 --noponder'
		with open('/tmp/test','w') as f:
			f.write(a)
		with open('/tmp/test','r') as f:
			result=subprocess.Popen(command,shell=True,stdin=f,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		stdout=result.stdout.read().decode().splitlines()
		stderr=result.stderr.read().decode()
		print(stderr)
		stderr=stderr.splitlines()
		play_moves=[]
		winrates=[]
		for i in stdout:
			if len(i)>2 and i[0]=='=':
				play_moves.append(i[2:])
		index=0
		sz19game_ids=list(sz19moves.keys())
		for i in range(len(stderr)-2):
			if stderr[i]=='':
				a=stderr[i+1]
				if len(a)<10 or a[0] !=' ' or a[2]==' ':
					continue
				winrates.append(a[19:26])
				a=a[58:]
				recommends[sz19game_ids[index]]=a.split()[1]
				print(index,a.split())
				index+=1
		for i,play,winrate in zip(sz19game_ids,play_moves,winrates):
			print (i,play)
			move_id=sz19moves[i][2]
			try:
				a=recommended[i]
			except KeyError:
				r = requests.get('https://www.dragongoserver.net/quick_do.php?obj=game&cmd=move&gid='+i+'&move='+play.lower()+'&fmt=board&move_id='+str(move_id)+'&msg=LeelaZero\'s winrate:'+winrate+'\nI have a feature to show LZ\'s recommend for last move. If you want to enable it, send a message to me.',cookies=cookies)
			else:
				print(i in games_to_recommend)
				if i in games_to_recommend:
					r = requests.get('https://www.dragongoserver.net/quick_do.php?obj=game&cmd=move&gid='+i+'&move='+play.lower()+'&fmt=board&move_id='+str(move_id)+'&msg=LeelaZero\'s winrate:'+winrate+'\nSometimes the recommend doesn\'t work well.\nRecommend for your last move from LZ:'+a,cookies=cookies)
				else:
					r = requests.get('https://www.dragongoserver.net/quick_do.php?obj=game&cmd=move&gid='+i+'&move='+play.lower()+'&fmt=board&move_id='+str(move_id)+'&msg=LeelaZero\'s winrate:'+winrate+'\nI have a feature to show LZ\'s recommend for last move. If you want to enable it, send a message to me.',cookies=cookies)
			recommended[i]=recommends[i]
	#size 13
	if sz13moves!={}:
		a='time_settings 0 6 1\n'
		for _,(i,myturn,_1) in sz13moves.items():
			a+='clear_board\n'
			for j in i:
				a+='play '+j+'\n'
			a+='genmove '+myturn+'\nshowboard\n'
		command='/home/kenny/Desktop/leela-zero13/build/leelaz -g -w /home/kenny/Desktop/lzbest13.gz -t 16 --noponder'
		with open('/tmp/test','w') as f:
			f.write(a)
		with open('/tmp/test','r') as f:
			result=subprocess.Popen(command,shell=True,stdin=f,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		stdout=result.stdout.read().decode().splitlines()
		stderr=result.stderr.read().decode()
		print(stderr)
		stderr=stderr.splitlines()
		play_moves=[]
		winrates=[]
		for i in stdout:
			if len(i)>2 and i[0]=='=':
				play_moves.append(i[2:])
		index=0
		sz13game_ids=list(sz13moves.keys())
		for i in range(len(stderr)-2):
			if stderr[i]=='':
				a=stderr[i+1]
				if len(a)<10 or a[0] !=' ' or a[2]==' ':
					continue
				winrates.append(a[19:26])
				a=a[58:]
				print(index,a.split())
				recommends[sz13game_ids[index]]=a.split()[1]
				index+=1
		for i,play,winrate in zip(sz13game_ids,play_moves,winrates):
			print (i,play)
			move_id=sz13moves[i][2]
			try:
				a=recommended[i]
			except KeyError:
				r = requests.get('https://www.dragongoserver.net/quick_do.php?obj=game&cmd=move&gid='+i+'&move='+play.lower()+'&fmt=board&move_id='+str(move_id)+'&msg=LeelaZero\'s winrate:'+winrate+'\nI have a feature to show LZ\'s recommend for last move. If you want to enable it, send a message to me.',cookies=cookies)
			else:
				if i in games_to_recommend:
					r = requests.get('https://www.dragongoserver.net/quick_do.php?obj=game&cmd=move&gid='+i+'&move='+play.lower()+'&fmt=board&move_id='+str(move_id)+'&msg=LeelaZero\'s winrate:'+winrate+'\nSometimes the recommend doesn\'t work well.\nRecommend for your last move from LZ:'+a,cookies=cookies)
				else:
					r = requests.get('https://www.dragongoserver.net/quick_do.php?obj=game&cmd=move&gid='+i+'&move='+play.lower()+'&fmt=board&move_id='+str(move_id)+'&msg=LeelaZero\'s winrate:'+winrate+'\nI have a feature to show LZ\'s recommend for last move. If you want to enable it, send a message to me.',cookies=cookies)
			recommended[i]=recommends[i]
	#size 9
	if sz9moves!={}:
		a='time_settings 0 6 1\n'
		for _,(i,myturn,_1) in sz9moves.items():
			a+='clear_board\n'
			for j in i:
				a+='play '+j+'\n'
			a+='genmove '+myturn+'\nshowboard\n'
		command='/home/kenny/Desktop/leela-zero9/build/leelaz -g -w /home/kenny/Desktop/lz9x9.gz -t 16 --noponder'
		with open('/tmp/test','w') as f:
			f.write(a)
		with open('/tmp/test','r') as f:
			result=subprocess.Popen(command,shell=True,stdin=f,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		stdout=result.stdout.read().decode().splitlines()
		stderr=result.stderr.read().decode()
		print(stderr)
		stderr=stderr.splitlines()
		play_moves=[]
		winrates=[]
		for i in stdout:
			if len(i)>2 and i[0]=='=':
				play_moves.append(i[2:])
		index=0
		sz9game_ids=list(sz9moves.keys())
		for i in range(len(stderr)-2):
			if stderr[i]=='':
				a=stderr[i+1]
				if len(a)<10 or a[0] !=' ' or a[2]==' ':
					continue
				winrates.append(a[19:26])
				a=a[58:]
				recommends[sz9game_ids[index]]=a.split()[1]
				print(index,a.split())
				index+=1
		for i,play,winrate in zip(sz9game_ids,play_moves,winrates):
			print (i,play)
			move_id=sz9moves[i][2]
			try:
				a=recommended[i]
			except KeyError:
				r = requests.get('https://www.dragongoserver.net/quick_do.php?obj=game&cmd=move&gid='+i+'&move='+play.lower()+'&fmt=board&move_id='+str(move_id)+'&msg=LeelaZero\'s winrate:'+winrate+'\nI have a feature to show LZ\'s recommend for last move. If you want to enable it, send a message to me.',cookies=cookies)
			else:
				if i in games_to_recommend:
					r = requests.get('https://www.dragongoserver.net/quick_do.php?obj=game&cmd=move&gid='+i+'&move='+play.lower()+'&fmt=board&move_id='+str(move_id)+'&msg=LeelaZero\'s winrate:'+winrate+'\nSometimes the recommend doesn\'t work well.\nRecommend for your last move from LZ:'+a,cookies=cookies)
				else:
					r = requests.get('https://www.dragongoserver.net/quick_do.php?obj=game&cmd=move&gid='+i+'&move='+play.lower()+'&fmt=board&move_id='+str(move_id)+'&msg=LeelaZero\'s winrate:'+winrate+'\nI have a feature to show LZ\'s recommend for last move. If you want to enable it, send a message to me.',cookies=cookies)
			recommended[i]=recommends[i]
	with open('/home/kenny/Desktop/dgs_recommended','w') as f:
		f.write(str(recommended))
	sleep(60)
