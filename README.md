# NBA Award Prediction

## Summary

This project scraps all NBA players' statistics between 1976-2020, cleans the data, and builds a predictive model making prediction on whether the player will win an NBA award the following year. In addition, a function with clustering using the embedded distance finds players with a similar playstyle to the player in interest (Who can be the next LeBron James?)

## Packages Used

In this project, **BeautifulSoup** is used for web scraping, **sqlite3** is used for data storage, **pandas** is used for data cleaning, and **scikit-learn** is used for building predictive models.

## User Guides

### Data Scraping

To scrap data from the internet, [nba_spyder.py](nba_spyder.py) is used, which then stores the data into different tables: Awards, Teams, Players, Traditional, Advanced, and Shooting. There are several different functions for scraping different kinds of data. To use them, simply un-comment the codes that call the functions.

The data is stored in spider.sqlite.

### Data Cleaning

[spyder_cleaning.py](spyder_cleaning.py) deals with the issue where player names are appended with asterisks if they have been introduced into the hall of fame. By running the function, those asterisks will be cleaned up.

### Award Prediction

[award_prediction.py](award_prediction.py) predicts whether players will receive awards in the following year based on their current performance. By selecting the range of years, the models will be built to estimate for those years.

### Player Clustering

[player_cluster.py](player_cluster.py) calculates and returns players with similar playstyles of the inputted player. The range is set to be 1980-2019, but it can be changed by the user.

## Description of Dataset

The dataset comes from https://www.basketball-reference.com. There are many different categories of statistics on this website, including traditional, advanced, and shooting. The traditional statistics includes points, rebounds, assists, steals, blocks, etc. The advanced statistics includes functions of traditional stats as estimators of the players' performance or values. The shooting statistics divides the basketball court into many parts and record the players' shooting frequency and efficiency on each part.

In addition to that, one can also scrap the data on player awards. By storing the data into different SQL tables with primary keys and foreign keys, one can easily recreate suitable tables for analysis.

In terms of the predictors, most of them are quantitative variables, and there are a lot of dependence between predictors. For example, total points correlates strongly with total minutes played, as with all raw counting statistics. To some extent, the three pointers made, three pointers attempted, and three pointer percentage correlate strongly as well.

## Methodology

### Data Cleaning

The dataset appends an asterisk after the player's name if he has been voted into the hall of fame. It presents a problem when one tries to look up players, so custom functions were written in [spyder_cleaning.py](spyder_cleaning.py) to deal with this.

For a given year, players may be traded mid-season, and that results in two or more entries per year. Since some statistics are counted as total over the season (traditional statistics) and others are calculated as an average (advanced statistics), they need to be treated differently.

To eliminate the apparent dependence between raw counting stats and games played, normalization needs to be performed before prediction.

Also, for players who have not attempted any three-pointers, their percentages are set to be zero.

### Award Prediction

The model used here is logistic regression. Different types of normalization were tested (per-game stats vs per-36 stats) on traditional statistics.

### Player Clustering

Given the name of a player and a year in which he played, the statistics were pulled from the dataset, and the distance between the row with all other rows is calculated. Then, the ten rows of the smallest distance are returned, showing the players that are close in the embedded space to the inputted player.

To look for rookies with great potential, we normalize the statistics on a per-36 basis (how well a player performs if he plays exactly 36 minutes.)

## Results

The logistic regression returns ~95% performance for both per-game and per-36 stats on traditional statistics. The clustering shows that players with similar playstyles are almost always playing the same position. This is a piece of evidence against the convention that the NBA basketball has become position-less in that positions matter much less now than before.



