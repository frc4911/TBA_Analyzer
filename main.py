import requests
import json
import re   # regex library
import sqlite3

# DEFINITIONS ==========================================
parameters = {"X-TBA-Auth-Key": "OazegQCZzJBXjtEqb8Weqb6VgzQ8VPINCNfm8pGyjVbSSXRyyW3df8l3ZMXRhAnE"}

# state values for controlling database activity
dbmakenew    = 1   # create a new database
dberase      = 1   # drop all tables in database
dbinsertdata = 1   # fill the database with useful information

# what information to retrieve
eventname = "2018pncmp"
eventyear = "2018"

# database information
dbfile = '2018pncmpdb'

# create and/or open database file ================================
conn = sqlite3.connect(dbfile)
cursor = conn.cursor()
print("Database opened")

# reset the database ===============================================
if dberase == 1:
	# dump the existing database tables
	cursor.execute('''DROP TABLE IF EXISTS competitions''')
	cursor.execute('''DROP TABLE IF EXISTS teams''')
	cursor.execute('''DROP TABLE IF EXISTS teamcomps''')
	cursor.execute('''DROP TABLE IF EXISTS matches''')
	cursor.execute('''DROP TABLE IF EXISTS matchalliances''')
	cursor.execute('''DROP TABLE IF EXISTS teammatches''')
	conn.commit()
	print("Database tables dropped")

# create database tables and structure =============================
if dbmakenew == 1:
	# create db structure
	sql_create_competitions_table = '''CREATE TABLE IF NOT EXISTS competitions(
										compkey TEXT PRIMARY KEY,
										compcity TEXT,
										compstate TEXT,
										compctry TEXT,
										compdate TEXT,
										compcode TEXT,
										compname TEXT
									)'''
	sql_create_teams_table = '''CREATE TABLE IF NOT EXISTS teams(
									teamkey TEXT PRIMARY KEY, 
									teamnum INTEGER,
									teamnick TEXT,
									teamryear INTEGER,
									teamcity TEXT,
									teamstate TEXT,
									teamctry TEXT,
									teamweb TEXT
								)'''
	sql_create_teamcomps_table = '''CREATE TABLE IF NOT EXISTS teamcomps(
										compkey TEXT,
										teamkey TEXT,
										alliancenum INTEGER,
										alliancepicknum INTEGER,
										alliancestr TEXT,
										highestlevel TEXT,
										highestlevelwins INTEGER,
										qualwins INTEGER,
										quallosses INTEGER,
										qualties INTEGER,
										qualdqs INTEGER,
										qualrank INTEGER,
										qualrankscore INTEGER,
										qualclimbpoints INTEGER,
										qualautopoints INTEGER,
										qualownpoints INTEGER,
										qualvaultpoints INTEGER,
										qualstatus TEXT,
										PRIMARY KEY (compkey, teamkey),
										FOREIGN KEY (compkey) REFERENCES competitions (compkey)
										ON DELETE CASCADE ON UPDATE NO ACTION,
										FOREIGN KEY (teamkey) REFERENCES teams (teamkey)
										ON DELETE CASCADE ON UPDATE NO ACTION
								)'''
	sql_create_matches_table = '''CREATE TABLE IF NOT EXISTS matches(
									matchkey TEXT PRIMARY KEY,
									compkey TEXT,
									complevel TEXT,
									number INTEGER,
									bluescore INTEGER, 
									redscore INTEGER,
									winner TEXT
								)'''
	sql_create_matchalliances_table = '''CREATE TABLE IF NOT EXISTS matchalliances(
										matchkey TEXT,
										alliance TEXT,
										autopoints INTEGER,
										autorankpoints TEXT,
										autoscaleownsecs INTEGER,
										autoswitchownsecs INTEGER,
										endgamepoints INTEGER,
										ftbrankpoint TEXT,
										foulcount INTEGER,
										foulpoints INTEGER,
										rankingpoints INTEGER,
										teleownpoints INTEGER,
										telepoints INTEGER,
										telescaleownsecs INTEGER,
										teleswitchownsecs INTEGER,
										vaultpoints INTEGER,
										PRIMARY KEY (matchkey, alliance),
										FOREIGN KEY (matchkey) REFERENCES matches (matchkey)
										ON DELETE CASCADE ON UPDATE NO ACTION
									)'''
	sql_create_teammatches_table = '''CREATE TABLE IF NOT EXISTS teammatches(
										teamkey TEXT, 
										matchkey TEXT, 
										alliance TEXT,
										robotnum INTEGER,
										auto TEXT,
										endgame TEXT,
										win INTEGER,
										PRIMARY KEY (teamkey, matchkey),
										FOREIGN KEY (teamkey) REFERENCES teams (teamkey)
										ON DELETE CASCADE ON UPDATE NO ACTION,
										FOREIGN KEY (matchkey) REFERENCES matches (matchkey)
										ON DELETE CASCADE ON UPDATE NO ACTION
									)'''
	
	cursor.execute(sql_create_competitions_table)
	cursor.execute(sql_create_teams_table)
	cursor.execute(sql_create_teamcomps_table)
	cursor.execute(sql_create_matches_table)
	cursor.execute(sql_create_matchalliances_table)
	cursor.execute(sql_create_teammatches_table)
	conn.commit()
	print("Database Tables created")

# Add database information =============================================
if dbinsertdata == 1:
	# load competition information
	compdata = requests.get('https://www.thebluealliance.com/api/v3/events/2018/simple', params=parameters)  # type of response is requests.models.Response
	# convert data to list format using built-in json method
	complist = compdata.json()
	for comp in complist:
		compkey   = comp["key"]
		compcity  = comp["city"]
		compstate = comp["state_prov"]
		compctry  = comp["country"]
		compdate  = comp["end_date"]
		compcode  = comp["event_code"]
		compname  = comp["name"]
		sqldata = (compkey, compcity, compstate, compctry, compdate, compcode, compname)
		sql = '''INSERT INTO competitions VALUES (?, ?, ?, ?, ?, ?, ?)'''
		cursor.execute(sql,sqldata)
		conn.commit()
	print('Competitions entered for', eventyear)
	
	# query TBA for team list for the event
	teamdata = requests.get('https://www.thebluealliance.com/api/v3/event/' + eventname + '/teams', params=parameters)  # type of response is requests.models.Response
	# convert data to list format using built-in json method
	teamlist = teamdata.json()
	# pull out data for each team
	for team in teamlist:
		teamnum   = team["team_number"]
		teamkey   = team["key"]
		teamnick  = team["nickname"]
		teamryear = team["rookie_year"]
		teamcity  = team["city"]
		teamstate = team["state_prov"]
		teamctry  = team["country"]
		teamweb   = team["website"]
		
		print('Entering data for', str(teamnum), teamnick)
		sqldata = (teamkey, teamnum, teamnick, teamryear, teamcity, teamstate, teamctry, teamweb)
		sql = '''INSERT INTO teams VALUES(?, ?, ?, ?, ?, ?, ?, ?)'''
		cursor.execute(sql, sqldata)
		conn.commit()
		# visual verification that the team was added
		print('     Team information entered')
		
		# load team competition information
		teamcompdata = requests.get('https://www.thebluealliance.com/api/v3/team/' + teamkey + '/events/' + eventyear + '/statuses', params=parameters)  # type of response is requests.models.Response
		# convert data to dict format using built-in json method
		teamcompdict = teamcompdata.json()
		tckeys = teamcompdict.keys()
		for compkey in tckeys:
			comp = teamcompdict[compkey]
			if comp is not None:
				# check for playoff data first
				if comp["playoff_status_str"] != "--":
					alliancenum      = comp["alliance"]["number"]
					alliancepicknum  = comp["alliance"]["pick"]
					alliancestr      = comp["alliance_status_str"]
					highestlevel     = comp["playoff"]["level"]
					highestlevelwins = comp["playoff"]["record"]["wins"]
				else:
					alliancenum     = 0
					alliancepicknum = 0
					alliancestr     = "Team " + teamkey + " was not selected for playoffs"
					highestlevel    = "qm"
					highestlevelwins = 0
				qualwins   = comp["qual"]["ranking"]["record"]["wins"]
				quallosses = comp["qual"]["ranking"]["record"]["losses"]
				qualties   = comp["qual"]["ranking"]["record"]["ties"]
				qualdqs    = comp["qual"]["ranking"]["dq"]
				qualrank   = comp["qual"]["ranking"]["rank"]
				qualrankscore   = comp["qual"]["ranking"]["sort_orders"][0]
				qualclimbpoints = comp["qual"]["ranking"]["sort_orders"][1]
				qualautopoints  = comp["qual"]["ranking"]["sort_orders"][2]
				qualownpoints   = comp["qual"]["ranking"]["sort_orders"][3]
				qualvaultpoints = comp["qual"]["ranking"]["sort_orders"][4]
				qualstatus      = comp["qual"]["status"]
			
				sqldata = (compkey, teamkey, alliancenum, alliancepicknum, alliancestr, highestlevel, highestlevelwins, qualwins, quallosses, qualties, qualdqs, qualrank, qualrankscore, qualclimbpoints, qualautopoints, qualownpoints, qualvaultpoints, qualstatus)
				sql = '''INSERT INTO teamcomps VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
				cursor.execute(sql, sqldata)
				conn.commit()
			else:
				print("Skipped competition " + compkey + " - no data yet")
		# verification that the teamcomp data was added
		print('     Team Competition data entered')

		# add match data for each team =======================================================
		teammatches = requests.get('https://www.thebluealliance.com/api/v3/team/' + teamkey + '/matches/' + eventyear, params=parameters)  # type of response is requests.models.Response
		
		teammatchlist = teammatches.json()
	
		for match in teammatchlist:
			# Check to make sure the match has not already been entered
			tmatchkey   = match["key"]
			sql = '''SELECT count(*) FROM matches WHERE matchkey = ?;'''
			cursor.execute(sql, (tmatchkey,))
			matchexists = cursor.fetchone()[0]
			if matchexists == 0:
				# The match has not been entered so move on to entering a new match
				bluescore = match["alliances"]["blue"]["score"]
				if bluescore > -1:  # stop if score is -1 because match hasn't happened
					redscore   = match["alliances"]["red"]["score"]
					matchkey   = match["key"]
					matchred1  = match["alliances"]["red"]["team_keys"][0]
					matchred2  = match["alliances"]["red"]["team_keys"][1]
					matchred3  = match["alliances"]["red"]["team_keys"][2]
					matchblue1 = match["alliances"]["blue"]["team_keys"][0]
					matchblue2 = match["alliances"]["blue"]["team_keys"][1]
					matchblue3 = match["alliances"]["blue"]["team_keys"][2]
					complevel  = match["comp_level"]
					compkey    = match["event_key"]
					number   = match["match_number"]
					winner   = match["winning_alliance"]
					# start on blue team data
					bautopoints     = match["score_breakdown"]["blue"]["autoPoints"]
					bautorankpoints = match["score_breakdown"]["blue"]["autoQuestRankingPoint"]
					bautorobot1 = match["score_breakdown"]["blue"]["autoRobot1"]
					bautorobot2 = match["score_breakdown"]["blue"]["autoRobot2"]
					bautorobot3 = match["score_breakdown"]["blue"]["autoRobot3"]
					bautoscaleownsecs  = match["score_breakdown"]["blue"]["autoScaleOwnershipSec"]
					bautoswitchownsecs = match["score_breakdown"]["blue"]["autoSwitchOwnershipSec"]
					bendgamerobot1  = match["score_breakdown"]["blue"]["endgameRobot1"]
					bendgamerobot2  = match["score_breakdown"]["blue"]["endgameRobot2"]
					bendgamerobot3  = match["score_breakdown"]["blue"]["endgameRobot3"]
					bendgamepoints  = match["score_breakdown"]["blue"]["endgamePoints"]
					bftbrankpoint   = match["score_breakdown"]["blue"]["faceTheBossRankingPoint"]
					bfoulcount      = match["score_breakdown"]["blue"]["foulCount"]
					bfoulpoints     = match["score_breakdown"]["blue"]["foulPoints"]
					brankingpoints     = match["score_breakdown"]["blue"]["rp"]
					bteleownpoints     = match["score_breakdown"]["blue"]["teleopOwnershipPoints"]
					btelepoints        = match["score_breakdown"]["blue"]["teleopPoints"]
					btelescaleownsecs  = match["score_breakdown"]["blue"]["teleopScaleOwnershipSec"]
					bteleswitchownsecs = match["score_breakdown"]["blue"]["teleopSwitchOwnershipSec"]
					bvaultpoints       = match["score_breakdown"]["blue"]["vaultPoints"]
					# start on red team data
					rautopoints     = match["score_breakdown"]["red"]["autoPoints"]
					rautorankpoints = match["score_breakdown"]["red"]["autoQuestRankingPoint"]
					rautorobot1 = match["score_breakdown"]["red"]["autoRobot1"]
					rautorobot2 = match["score_breakdown"]["red"]["autoRobot2"]
					rautorobot3 = match["score_breakdown"]["red"]["autoRobot3"]
					rautoscaleownsecs  = match["score_breakdown"]["red"]["autoScaleOwnershipSec"]
					rautoswitchownsecs = match["score_breakdown"]["red"]["autoSwitchOwnershipSec"]
					rendgamerobot1  = match["score_breakdown"]["red"]["endgameRobot1"]
					rendgamerobot2  = match["score_breakdown"]["red"]["endgameRobot2"]
					rendgamerobot3  = match["score_breakdown"]["red"]["endgameRobot3"]
					rendgamepoints  = match["score_breakdown"]["red"]["endgamePoints"]
					rftbrankpoint   = match["score_breakdown"]["red"]["faceTheBossRankingPoint"]
					rfoulcount      = match["score_breakdown"]["red"]["foulCount"]
					rfoulpoints     = match["score_breakdown"]["red"]["foulPoints"]
					rrankingpoints     = match["score_breakdown"]["red"]["rp"]
					rteleownpoints     = match["score_breakdown"]["red"]["teleopOwnershipPoints"]
					rtelepoints        = match["score_breakdown"]["red"]["teleopPoints"]
					rtelescaleownsecs  = match["score_breakdown"]["red"]["teleopScaleOwnershipSec"]
					rteleswitchownsecs = match["score_breakdown"]["red"]["teleopSwitchOwnershipSec"]
					rvaultpoints       = match["score_breakdown"]["red"]["vaultPoints"]
				
					# insert match data into database
					sqldata = (matchkey, compkey, complevel, number, bluescore, redscore, winner)
					sql = '''INSERT INTO matches VALUES (?, ?, ?, ?, ?, ?, ?)'''
					cursor.execute(sql, sqldata)
					conn.commit()
					print("      Match information entered")
				
					# insert team/match data into database
					if winner == "red":
						redwin  = 0
						bluewin = 1
					else:
						redwin  = 1
						bluewin = 0
					sqldata  = [(matchred1, matchkey, "red", 1, rautorobot1, rendgamerobot1, redwin),
								(matchred2, matchkey, "red", 2, rautorobot2, rendgamerobot2, redwin),
								(matchred3, matchkey, "red", 3, rautorobot3, rendgamerobot3, redwin),
								(matchblue1, matchkey, "blue", 1, bautorobot1, bendgamerobot1, bluewin),
								(matchblue2, matchkey, "blue", 2, bautorobot2, bendgamerobot2, bluewin),
								(matchblue3, matchkey, "blue", 3, bautorobot2, bendgamerobot2, bluewin)]
					sql ='''INSERT INTO teammatches VALUES(?, ?, ?, ?, ?, ?, ?)'''
					cursor.executemany(sql, sqldata)
					print("     Team/match information entered")
				
					# insert match alliance data into database
					sqldata = (matchkey, "red", rautopoints, rautorankpoints, rautoscaleownsecs, rautoswitchownsecs, rendgamepoints, rftbrankpoint, rfoulcount, rfoulpoints, rrankingpoints, rteleownpoints, rtelepoints, rtelescaleownsecs, rteleswitchownsecs, rvaultpoints)
					sql = '''INSERT INTO matchalliances VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
					cursor.execute(sql, sqldata)
					sqldata = (matchkey, "blue", bautopoints, bautorankpoints, bautoscaleownsecs, bautoswitchownsecs, bendgamepoints, bftbrankpoint, bfoulcount, bfoulpoints, brankingpoints, bteleownpoints, btelepoints, btelescaleownsecs, bteleswitchownsecs, bvaultpoints)
					sql = '''INSERT INTO matchalliances VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
					cursor.execute(sql, sqldata)
					conn.commit()
					print("      Match/alliance information entered")
			else:
				print("skipped match " + matchkey + " - already in database")
	print("Finished processing team " + teamkey)
conn.close
print("end")