#Python3

import sqlite3
import pandas as pd
import numpy as np


conn = sqlite3.connect('spider.sqlite')

player_trad_stmt = ''' SELECT * from Traditional T 
                JOIN Players P 
                on T.Player_id = P.id 
                where T.Year between {year_start} and {year_end}'''

player_adv_stmt = ''' SELECT * from Advanced Adv 
                JOIN Players P 
                on Adv.Player_id = P.id 
                where Adv.Year between {year_start} and {year_end}'''




#Let's join the award table again to get prediction for the next year's award

player_trad_plus_award_new_stmt = '''SELECT * from Players P
                                    join (Traditional T
                                        left join Awards A
                                        on (T.Player_id = A.Player_id and A.Year = T.year)
                                        left join Awards A1
                                        on (T.Player_id = A1.Player_id and A1.Year = T.year + 1))
                                    on (T.Player_id = P.id)
                                    where T.Year between {year_start} and {year_end} '''


year_start = 1980
year_end = 2019

#df_player_trad = pd.read_sql_query(player_trad_stmt.format(year_start = year_start, year_end = year_end), conn)

df_player_trad = pd.read_sql_query(player_trad_stmt.format(year_start = year_start, year_end = year_end), conn)
df_player_adv = pd.read_sql_query(player_adv_stmt.format(year_start = year_start, year_end = year_end), conn)

#Start processing rows



#Drop id column and position. To cluster players, we want to find players similar to stars. Possibly they would have few minutes.
#Do we need to talk about performance relative to the team? It is basically for the young players on bad teams.

def GetMPG(row):
    return row['MP']/row['G']


#We only look at players who play more than 10 mpg and 10 games.

def DF_stat_preprocess(df):
    df2 = df.drop(columns =['id'], inplace = False)
    df2['MPG'] = df2.apply(GetMPG, axis = 1)
    df2 = df2[df2['MPG']>10]
    df2 = df2[df2['G']>10]
    return df2


df_player_trad = DF_stat_preprocess(df_player_trad)
df_player_adv = DF_stat_preprocess(df_player_adv)



#For players traded mid-season, I suppose it makes sense to NOT combine their stats. It can be argued that the player has similar impact as the star under certain circumstances.


#For traditional stats, we look at per-36. For advanced, we should not look at total winshare. Also, we can drop box plus-minus because it is described by OBPM + DBPM.

df_player_adv.drop(columns = ['WS', 'BPM'], inplace = True)
df_player_adv['OWS'] /= df_player_adv['MP']
df_player_adv['DWS'] /= df_player_adv['MP']







#Per 36 stats:
df_player_trad['PTS/36'] = 36*df_player_trad['PTS']/df_player_trad['MP']
df_player_trad['RB/36'] = 36*df_player_trad['TRB']/df_player_trad['MP']
df_player_trad['AST/36'] = 36*df_player_trad['AST']/df_player_trad['MP']
df_player_trad['STL/36'] = 36*df_player_trad['STL']/df_player_trad['MP']
df_player_trad['BLK/36'] = 36*df_player_trad['BLK']/df_player_trad['MP']
df_player_trad['TOV/36'] = 36*df_player_trad['TOV']/df_player_trad['MP']
df_player_trad['PF/36'] = 36*df_player_trad['PF']/df_player_trad['MP']

#There are NaN and inf in pre-36 stats. It's because some players only played seconds in the season.

df_player_trad.replace([np.inf,'inf'], np.nan, inplace = True)
df_player_trad.fillna(0,inplace=True)

df_player_adv.replace([np.inf,'inf'], np.nan, inplace = True)
df_player_adv.fillna(0,inplace=True)

df_player_trad.drop(columns = ['Age','G','GS','PTS','TRB','AST','STL','BLK','TOV','PF','MP'],inplace = True)

df_player_adv.drop(columns = ['Age','G','MP'], inplace = True)


df_player_trad['FTP'] = pd.to_numeric(df_player_trad['FTP'])
df_player_trad['ThreePP'] = pd.to_numeric(df_player_trad['ThreePP'])



#=============================================
#What do we drop? Where do we normalize? For logistic regression, is it not necessary to normalize?


#============================================
#Normalize columns
def Normalize_and_drop(df):
    Player_names = df['Player_name']
    Team_ids = df['Team_id']
    Player_ids = df['Player_id']
    Years = df['Year']
    Positions = df['Pos']

    df_nor = df.drop(columns = ['Year','Player_name','Team_id','Player_id', 'MPG','Pos'])

    df_nor = (df_nor-df_nor.min())/(df_nor.max()-df_nor.min())
    df_nor['Player_name'] = Player_names
    df_nor['Team_id'] = Team_ids
    df_nor['Player_id'] = Player_ids
    df_nor['Year'] = Years
    df_nor['Pos'] = Positions

    return df_nor

df_player_adv_nor = Normalize_and_drop(df_player_adv)
df_player_trad_nor = Normalize_and_drop(df_player_trad)


#Let's get the data of Lebron James and Kevin Durant.

def FindID(Player_name):

    cur = conn.cursor()

    cur.execute(''' SELECT id from Players where Player_name = ? ''', (Player_name,))

    id = cur.fetchone()


    return id







def Calculate_distance(df, player_name, year):

    ID = FindID(player_name)
    if ID == None:
        ID = FindID(player_name+"*")
        if ID == None:
            print("Can't find the player.")
            return
    
    player_df = df[df['Player_id'] == ID]
    #print(player_df)
    player_year = player_df[player_df['Year'] == year].squeeze()

    if player_year.empty:
        print("The player didn't play that year!")
        return

    Player_names = df['Player_name']
    Years = df['Year']
    Positions = df['Pos']

    df_num = df.drop(columns = ['Year','Player_name','Team_id','Player_id','Pos'])


    row_num = player_year.drop(labels = ['Year','Player_name','Team_id','Player_id', 'Pos'])



    df_num = df_num - row_num

    df_num['Distance'] = df_num.apply(np.linalg.norm, axis = 1)
    df_num['Player_name'] = Player_names
    #df_num['Team_id'] = Team_ids
    #df_num['Player_id'] = Player_ids
    df_num['Year'] = Years
    df_num['Pos'] = Positions

    df_dist = df_num[['Distance','Player_name','Pos','Year']].sort_values(by = ['Distance'])


    print("The closest normalized performance for Player {} in Year {} is as follows:".format(player_name,year))
    print(df_dist.head(30))

    #return df_dist  



#Calculate_distance(df_player_trad_nor, "LeBron James", 2010)
#Calculate_distance(df_player_adv_nor, "Vince Carter", 2017)

while True:
    name = input("Input the player you want to cluster with: ")
    if name == '':
        print('Ending the program...')
        break

    year = int(input("Input the year you want to set as the baseline: "))





    Calculate_distance(df_player_adv_nor, name, year)

