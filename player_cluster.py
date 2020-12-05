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


year_start = 2010
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
    df2 = df.drop(columns =['id','Pos'], inplace = False)
    df2['MPG'] = df2.apply(GetMPG, axis = 1)
    df2 = df2[df2['MPG']>10]
    df2 = df2[df2['G']>10]
    return df2


df_player_trad = DF_stat_preprocess(df_player_trad)
df_player_adv = DF_stat_preprocess(df_player_adv)


#For players traded mid-season, I suppose it makes sense to NOT combine their stats. It can be argued that the player has similar impact as the star under certain circumstances.


#For traditional stats, we look at per-36. For advanced, we should not look at total winshare. Also, we can drop box plus-minus because it is described by OBPM + DBPM.

df_player_adv.drop(columns = ['WS', 'BPM','OWS','DWS'], inplace = True)
df_player_adv['OWS'] /= df_player_adv['MP']







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

df_player_trad.drop(columns = ['Age','G','GS','MPG','PTS','TRB','AST','STL','BLK','TOV','PF','MP'],inplace = True)

df_player_adv.drop(columns = ['G','MP'], inplace = True)


df_player_trad['FTP'] = pd.to_numeric(df_player_trad['FTP'])
df_player_trad['ThreePP'] = pd.to_numeric(df_player_trad['ThreePP'])



print(df_player_trad.columns.values)

print(df_player_trad.min())

print(df_player_adv.columns.values)
print(df_player_adv.min())


#=============================================
#What do we drop? Where do we normalize? For logistic regression, is it not necessary to normalize?


#============================================
#Normalize columns
def Normalize_and_drop(df):
    Player_names = df['Player_name']
    Team_ids = df['Team_id']
    Player_ids = df['Player_id']
    Years = df['Year']

    df_nor = df.drop(columns = ['Year','Player_name','Team_id','Player_id'])

    df_nor = (df_nor-df_nor.min())/(df_nor.max()-df_nor.min())
    df_nor['Player_name'] = Player_names
    df_nor['Team_id'] = Team_ids
    df_nor['Player_id'] = Player_ids
    df_nor['Year'] = Years

    return df_nor

df_player_adv_nor = Normalize_and_drop(df_player_adv)
df_player_trad_nor = Normalize_and_drop(df_player_trad)

print(df_player_trad_nor.head())
print(df_player_adv_nor.head())









from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import normalize, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_validate

scaler = StandardScaler()

LR = LogisticRegression()

Trad_stat = ["Age", "MPG", "PTS/G", "RB/G", "AST/G", "STL/G", "BLK/G", "BLK/G", "PF/G"]
X = df_player_trad[Trad_stat]
scaler.fit(X)
X = scaler.transform(X)
y = df_player_trad["Award"]
y = y.astype('int')

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.10, random_state=42)


LR.fit(X_train,y_train)

coef = LR.coef_
coef = coef[0]
ind = sorted(range(len(coef)), key = lambda k: abs(coef[k]), reverse=True)


imp_list = [Trad_stat[i] for i in ind]

print("LR test for current year prediction based on per-game stat is",LR.score(X_test, y_test))
print("The importance of coefficients are,", ', '.join(imp_list))

LR2 = LogisticRegression()
Trad_stat_36 = ["Age", "MPG", "PTS/36", "RB/36", "AST/36", "STL/36", "BLK/36", "BLK/36", "PF/36"]
X2 = df_player_trad[Trad_stat_36]
scaler.fit(X2)
X2 = scaler.transform(X2)
y2 = df_player_trad["Award"]
y2 = y2.astype('int')


X_train, X_test, y_train, y_test = train_test_split(X2, y2, test_size=0.10, random_state=42)

LR2.fit(X_train,y_train)

coef = LR2.coef_
coef = coef[0]
ind = sorted(range(len(coef)), key = lambda k: abs(coef[k]), reverse=True)


imp_list = [Trad_stat_36[i] for i in ind]

print("LR test for current year prediction based on per-36 stat is",LR2.score(X_test, y_test))
print("The importance of coefficients are,", ', '.join(imp_list))

LR3 = LogisticRegression()

X3 = df_player_trad[Trad_stat]
scaler.fit(X3)
X3 = scaler.transform(X3)
y3 = df_player_trad["Award_next_year"]
y3 = y3.astype('int')

X_train, X_test, y_train, y_test = train_test_split(X3, y3, test_size=0.10, random_state=42)


LR3.fit(X_train,y_train)

coef = LR3.coef_
coef = coef[0]
ind = sorted(range(len(coef)), key = lambda k: abs(coef[k]), reverse=True)


imp_list = [Trad_stat[i] for i in ind]


print("LR test for next year prediction based on per-game stat is",LR3.score(X_test, y_test))
print("The importance of coefficients are,", ', '.join(imp_list))

LR4 = LogisticRegression()
X4 = df_player_trad[Trad_stat_36]
scaler.fit(X4)
X4 = scaler.transform(X4)
y4 = df_player_trad["Award_next_year"]
y4 = y4.astype('int')

X_train, X_test, y_train, y_test = train_test_split(X4, y4, test_size=0.10, random_state=42)

LR4.fit(X_train,y_train)

coef = LR4.coef_
coef = coef[0]
ind = sorted(range(len(coef)), key = lambda k: abs(coef[k]), reverse=True)


imp_list = [Trad_stat_36[i] for i in ind]


print("LR test for next year prediction based on per-36 stat is",LR4.score(X_test, y_test))
print("The importance of coefficients are,", ', '.join(imp_list))