#Fix the database, taking away the * sign

import sqlite3

conn = sqlite3.connect('spider.sqlite')
cur = conn.cursor()


#We are taking away any names with asterisks at the end.

def take_away_asterisks():
    cur.execute('SELECT Player_name from Players where Player_name like "%*"')
    asterisks_list = cur.fetchall()
    for player_asterisk in asterisks_list:
        player_ast = player_asterisk[0]
        player_name = player_ast[:-1]
        print(player_ast,player_name)
        cur.execute('UPDATE Players SET Player_name = ? where Player_name = ?', (player_name,player_ast))
    
    cur.commit()
    cur.close()

def test():
    player_name = "Kareem Abdul-Jabbar"
    new_player_name = player_name+"*"
    cur.execute('select id from Players where Player_name = ?', (new_player_name,))
    print(cur.fetchone())
    print(cur.fetchone())

test()
