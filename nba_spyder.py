from urllib.request import urlopen
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd


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


conn.commit()


#NBA-ABA merger happened in 1976. For simplicity, we will only acquire data starting from 1976-77 season, which is coded as year 1977.

Base_url = "https://www.basketball-reference.com/leagues/NBA_{year}_{mode}.html"

mode = "totals"

most_current_year = 2020

#Start where it is left off. If it is empty, then we start from 1977.

cur.execute('''SELECT MAX(Year) FROM Traditional''')
starting_year = cur.fetchone()[0]
if starting_year is None:
    starting_year = 1977

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

    conn.commit()      
    print("We have done saving data for year {}".format(year))

conn.commit()





#If player_stat[i][3] == 'TOT', then we should get rid of that. (Traded to another team)
#If there is no attempt, then the percentage will be an empty string. Take note of that.


