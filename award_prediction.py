#Python3

import sqlite3
import pandas as pd
import numpy as np


conn = sqlite3.connect('spider.sqlite')

player_trad_stmt = ''' SELECT * from Traditional T 
                JOIN Players P 
                on T.Player_id = P.id 
                where T.Year between {year_start} and {year_end}'''


player_award_stmt = ''' SELECT * from Awards A
                            JOIN Players P
                            on A.Player_id = P.id
                            where A.Year between {year_start} and {year_end} '''


player_trad_plus_award_stmt = '''SELECT * from Traditional T
                                    left join (Awards A
                                        join Players P
                                        on A.Player_id = P.id)
                                    on (T.Player_id = P.id and A.Year = T.year)
                                    where T.Year between {year_start} and {year_end} '''


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

df_player_trad = pd.read_sql_query(player_trad_plus_award_new_stmt.format(year_start = year_start, year_end = year_end), conn)


#Start processing rows

#Drop id column and position

df_player_trad.drop(columns =['id','Pos', "Year:1","Player_id:1", "Year:2", "Player_id:2"],inplace = True)

#Rename columns
new_columns = df_player_trad.columns.values
new_columns[-1] = "Award_next_year"
df_player_trad.columns = new_columns

#Replace awards by 1 then drop duplicates.
df_player_trad.fillna(0,inplace = True)
df_player_trad.loc[df_player_trad["Award"]!= 0, "Award"] = 1
df_player_trad.loc[df_player_trad["Award_next_year"]!= 0, "Award_next_year"] = 1

df_player_trad.drop_duplicates(inplace=True)



#============================================

#First, we combine rows where players are traded to different teams mid-season.

Additive_list = ['G','GS','MP','FG','FGA','ThreeP','ThreePA','TwoP','TwoPA','FT','FTA','ORB','DRB','TRB','AST','STL','BLK','TOV','PF','PTS']

for year in range(year_start, year_end+1):
    #df_player_trad['index1'] = df_player_trad.index

    df_current_year = df_player_trad[df_player_trad['Year'] == year]


    df_teams_count = df_current_year[['Player_id','Year']].groupby('Player_id').count()
    trading_list = list(df_teams_count[df_teams_count['Year'] >1 ].index)
    for pl_id in trading_list:
        df_pl_stat = df_current_year[df_current_year['Player_id']== pl_id]
        ind_list = list(df_pl_stat.index)
        df_player_trad.loc[ind_list[0],Additive_list] = df_pl_stat[Additive_list].sum()

        df_player_trad.loc[ind_list[0],'FGP'] = float(df_player_trad.loc[ind_list[0],'FG'])/ df_player_trad.loc[ind_list[0],'FGA']
        df_player_trad.loc[ind_list[0],'ThreePP'] = float(df_player_trad.loc[ind_list[0],'ThreeP'])/ df_player_trad.loc[ind_list[0],'ThreePA']
        df_player_trad.loc[ind_list[0],'TwoPP'] = float(df_player_trad.loc[ind_list[0],'TwoP'])/ df_player_trad.loc[ind_list[0],'TwoPA']
        df_player_trad.loc[ind_list[0],'FTP'] = float(df_player_trad.loc[ind_list[0],'FT'])/ df_player_trad.loc[ind_list[0],'FTA']
        df_player_trad.loc[ind_list[0],'eFGP'] = float(df_player_trad.loc[ind_list[0],'FG']+ 0.5*df_player_trad.loc[ind_list[0],'ThreeP'])/ df_current_year.loc[ind_list[0],'FGA']

        df_player_trad.drop(index = ind_list[1:], inplace = True)
        
        #Why didn't the table drop those rows? Because we didn't set inplace to be true.







#==============================================

#We will normalize the data to per/game stat. After that we will set G, FGP, TPP, PTS/G, RB/G, AST/G, STL/G, BLK/G as independent variables.

df_player_trad['MPG'] = df_player_trad['MP']/df_player_trad['G']
df_player_trad['PTS/G'] = df_player_trad['PTS']/df_player_trad['G']
df_player_trad['RB/G'] = df_player_trad['TRB']/df_player_trad['G']
df_player_trad['AST/G'] = df_player_trad['AST']/df_player_trad['G']
df_player_trad['STL/G'] = df_player_trad['STL']/df_player_trad['G']
df_player_trad['BLK/G'] = df_player_trad['BLK']/df_player_trad['G']
df_player_trad['TOV/G'] = df_player_trad['TOV']/df_player_trad['G']
df_player_trad['PF/G'] = df_player_trad['PF']/df_player_trad['G']

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



#=============================================
#What do we drop? Where do we normalize? For logistic regression, is it not necessary to normalize?


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