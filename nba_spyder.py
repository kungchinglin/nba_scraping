from urllib.request import urlopen
from bs4 import BeautifulSoup
from bs4 import Comment
import sqlite3
import pandas as pd
import re

#Create database

conn = sqlite3.connect('spider.sqlite')
cur = conn.cursor()


cur.execute('''CREATE TABLE IF NOT EXISTS Players
    (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    Player_name TEXT UNIQUE)''')

cur.execute('''CREATE TABLE IF NOT EXISTS Teams
    (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    Team_name TEXT UNIQUE)''')

cur.execute('''CREATE TABLE IF NOT EXISTS Traditional
    (Year INTEGER, Player_id INTEGER, Pos TEXT, Age INTEGER, Team_id INTEGER,
     G INTEGER, GS INTEGER, MP INTEGER, FG INTEGER, FGA INTEGER, FGP FLOAT,
     ThreeP INTEGER, ThreePA INTEGER, ThreePP FLOAT, TwoP INTEGER, TwoPA INTEGER,
     TwoPP FLOAT, eFGP FLOAT, FT INTEGER, FTA INTEGER, FTP FLOAT, ORB INTEGER, DRB INTEGER,
     TRB INTEGER, AST INTEGER, STL INTEGER, BLK INTEGER, TOV INTEGER, PF INTEGER, PTS INTEGER,  UNIQUE(Year, Player_id, Team_id))''')

cur.execute('''CREATE TABLE IF NOT EXISTS Advanced
    (Year INTEGER, Player_id INTEGER, Pos TEXT, Age INTEGER, Team_id INTEGER,
     G INTEGER, MP INTEGER, PER FLOAT, TSP FLOAT, ThreePAr FLOAT, FTr FLOAT,
     ORBP FLOAT, DRBP FLOAT, TRBP FLOAT, ASTP FLOAT, STLP FLOAT, BLKP FLOAT,
     TOVP FLOAT, USGP FLOAT, OWS FLOAT, DWS FLOAT, WS FLOAT, WS_over48 FLOAT,
     OBPM FLOAT, DBPM FLOAT, BPM FLOAT, VORP FLOAT,  UNIQUE(Year, Player_id, Team_id))''')

cur.execute('''CREATE TABLE IF NOT EXISTS Shooting
    (Year INTEGER, Player_id INTEGER, Pos TEXT, Age INTEGER, Team_id INTEGER,
     G INTEGER, MP INTEGER, FGP FLOAT, DIST FLOAT, 
     TwoPAP FLOAT, Zero_3AP FLOAT, Three_10AP FLOAT,
     Ten_16AP FLOAT, Sixteen_3PAP FLOAT, ThreePAP FLOAT,
     TwoPFGP FLOAT, Zero_3FGP FLOAT, Three_10FGP FLOAT,
     Ten_16FGP FLOAT, Sixteen_3PFGP FLOAT, ThreePFGP FLOAT ,
     TwoP_Ast_P FLOAT, ThreeP_Ast_P FLOAT, Dunk_AP FLOAT, Dunk_Num INTEGER,
     Corner3_AP FLOAT, Corner3_Num INTEGER, Heave_Att INTEGER, Heave_FG INTEGER,   UNIQUE(Year, Player_id, Team_id))''')

cur.execute('''CREATE TABLE IF NOT EXISTS Awards
    (Year INTEGER, Player_id INTEGER, Award TEXT)''')

conn.commit()

#NBA-ABA merger happened in 1976. For simplicity, we will only acquire data starting from 1976-77 season, which is coded as year 1977.

Base_url = "https://www.basketball-reference.com/leagues/NBA_{year}_{mode}.html"

Base_url_award = "https://www.basketball-reference.com/leagues/NBA_{year}.html"

#Many different modes


traditional_mode = {

"mode" : "totals",

"most_current_year" : 2020,

"mode_starting_year" : 1977,

"mode_table" : 'Traditional'}

advanced_mode = {

"mode" : "advanced",

"most_current_year" : 2020,

"mode_starting_year" : 1977,

"mode_table" : 'Advanced'}



shooting_mode = {

"mode" : "shooting",

"most_current_year" : 2020,

"mode_starting_year" : 1997,

"mode_table" : 'Shooting'} 


def store_data_awards(check_database = 'True'):

    print("Warning: There are two Bobby Jones in the database. One is a HOFer, while the other only lasted for two seasons. All the awards were given to the HOFer Bobby Jones.")

    most_current_year = 2020
    starting_year = None

    if check_database == True:
        cur.execute('''SELECT MAX(Year) FROM Awards''')
        starting_year = cur.fetchone()[0]

    if starting_year is None:
        starting_year = 1977

    award_list = ['all-nba_1', 'all-nba_2', 'all-nba_3', 'all-defensive_1', 'all-defensive_2', 'all-rookie_1', 'all-rookie_2', 'all_star_game_rosters_1', 'all_star_game_rosters_2']

    for year in range(starting_year, most_current_year + 1):

        phandle = urlopen(Base_url_award.format(year = year))

        p_soup = BeautifulSoup(phandle, features = "html.parser")

        #div_id: all-nba_1, all-nba_2, all-nba_3, all-defensive_1, all-defensive_2, all-rookie_1, all-rookie_2, all_star_game_rosters_1, all_star_game_rosters_2

        #Find comments

        comments = p_soup.find_all(string=lambda text: isinstance(text, Comment))
        for c in comments:
            c_soup = BeautifulSoup(c, features = "html.parser")
            for award in award_list:
                divs = c_soup.find_all('div', {'id':award})
                for div in divs:
                    players = div.find_all('a')
                    for player in players:
                        Player_name = player.getText()
                        #Get player_id

                        cur.execute('SELECT id FROM Players WHERE Player_name = ? ', ( Player_name, ))
                        possible_candidate = cur.fetchone()
                        if possible_candidate is None:
                            new_player_name = Player_name+"*"
                            cur.execute('SELECT id FROM Players WHERE Player_name = ? ', ( new_player_name, ))
                            possible_candidate = cur.fetchone()

                        Player_id = possible_candidate[0]

                        cur.execute('''INSERT OR IGNORE INTO Awards (Year, Player_id, Award) VALUES (?,?,?) ''',(year, Player_id, award))
            
        conn.commit()      
        print("Finished saving data for year {}".format(year))
    conn.close()
    
#store_data_awards()


def store_data(mode_dict):

    mode = mode_dict["mode"]
    most_current_year = mode_dict["most_current_year"]
    mode_starting_year = mode_dict["mode_starting_year"]
    mode_table = mode_dict["mode_table"]

    #Start where it is left off. If it is empty, then we start from the starting year.

    #Find table to work with.
    if mode_table == 'Traditional':
        cur.execute('''SELECT MAX(Year) FROM Traditional''')
        starting_year = cur.fetchone()[0]

    if mode_table == 'Advanced':
        cur.execute('''SELECT MAX(Year) FROM Advanced''')
        starting_year = cur.fetchone()[0]        

    if mode_table == 'Shooting':
        cur.execute('''SELECT MAX(Year) FROM Shooting''')
        starting_year = cur.fetchone()[0]      


    if starting_year is None:
        starting_year = mode_starting_year

    for year in range(starting_year, most_current_year + 1):

        phandle = urlopen(Base_url.format(year = year, mode = mode))

        p_soup = BeautifulSoup(phandle, features = "html.parser")

        #Get the header

        #header = [th.getText() for th in p_soup.find_all('tr')[0].find_all('th')]

        #header = header[1:]


        rows = p_soup.find_all('tr')[1:]

        player_stat = [[td.getText() for td in row.find_all('td')] for row in rows]

        for player in player_stat:
            #There are rows where nothing is stored because they use it as a separator.
            if len(player) == 0:
                continue

            Player_name = player[0]

            cur.execute('''INSERT OR IGNORE INTO Players (Player_name) 
                VALUES ( ? )''', ( Player_name, ) )
            cur.execute('SELECT id FROM Players WHERE Player_name = ? ', (Player_name, ))
            Player_id = cur.fetchone()[0]

            Team_name = player[3]

            #We will not store the data if the player is traded mid-season. We store data on individual teams.
            if Team_name == 'TOT':
                continue

            cur.execute('''INSERT OR IGNORE INTO Teams (Team_name) 
                VALUES ( ? )''', ( Team_name, ) )
            cur.execute('SELECT id FROM Teams WHERE Team_name = ? ', (Team_name, ))
            Team_id = cur.fetchone()[0]
            

            if mode_table == 'Traditional':

                data = player[:]
                data.insert(0,year)
                data[1] = Player_id
                data[4] = Team_id
                data = tuple(data)

                cur.execute('''INSERT OR IGNORE INTO Traditional (Year, Player_id, Pos, Age, Team_id,
                G, GS, MP, FG, FGA, FGP,
                ThreeP, ThreePA, ThreePP, TwoP, TwoPA,
                TwoPP, eFGP, FT, FTA, FTP, ORB, DRB,
                TRB, AST, STL, BLK, TOV, PF, PTS) 
                    VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )''', data )  

            if mode_table == 'Advanced':
                data = player[:]
                #There are two entries where nothing is entered. Get rid of them.
                data.pop(23)
                data.pop(18)
                data.insert(0,year)
                data[1] = Player_id
                data[4] = Team_id
                data = tuple(data)

                cur.execute('''INSERT OR IGNORE INTO Advanced (Year, Player_id, Pos, Age, Team_id,
                G, MP, PER, TSP, ThreePAr, FTr, ORBP, DRBP, TRBP, ASTP, STLP, BLKP,
                 TOVP, USGP, OWS, DWS, WS, WS_over48, OBPM, DBPM, BPM, VORP) 
                    VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )''', data ) 

            if mode_table == 'Shooting':
                data = player[:]
                #There are two entries where nothing is entered. Get rid of them.
                indices = [8,15,22,25,28,31]
                for index in sorted(indices, reverse = True):
                    del data[index]
                data.insert(0,year)
                data[1] = Player_id
                data[4] = Team_id
                data = tuple(data)

                cur.execute('''INSERT OR IGNORE INTO Shooting (Year, Player_id, Pos, Age, Team_id,
                G, MP, FGP, DIST, TwoPAP, Zero_3AP, Three_10AP,
                Ten_16AP, Sixteen_3PAP, ThreePAP, TwoPFGP, Zero_3FGP, Three_10FGP,
                Ten_16FGP, Sixteen_3PFGP, ThreePFGP, TwoP_Ast_P, ThreeP_Ast_P, Dunk_AP, Dunk_Num,
                Corner3_AP, Corner3_Num, Heave_Att, Heave_FG) 
                    VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )''', data )             


        conn.commit()      
        print("Finished saving data for year {}".format(year))

    conn.commit()
    conn.close()




#store_data(shooting_mode)

def test_to_find_structure():

    year = 2020
    phandle = urlopen(Base_url_award.format(year = year))

    p_soup = BeautifulSoup(phandle, features = "html.parser")


    #div_id: all-nba_1, all-nba_2, all-nba_3, all-defensive_1, all-defensive_2, all-rookie_1, all-rookie_2, all_star_game_rosters_1, all_star_game_rosters_2

    #Find comments

    comments = p_soup.find_all(string=lambda text: isinstance(text, Comment))
    for c in comments:
        c_soup = BeautifulSoup(c, features = "html.parser")

        divs = c_soup.find_all('div', {'id':'all-nba_1'})
        for div in divs:
            players = div.find_all('a')
            for player in players:
                print(player.getText())
            
        #tables = c_soup.find_all('table')
        #for table in tables:
        #    print("Printing table:",table)
        #print("===========")
        #c.extract()
    




    #Get the header
    #header = [th.getText() for th in p_soup.find_all('tr')[1].find_all('th')]

    #header = header[1:]

    #print(header)

    #rows = p_soup.find_all('tr')[1:]

    #player_stat = [[td.getText() for td in row.find_all('td')] for row in rows]

    #print(player_stat[:3])

#test_to_find_structure()

