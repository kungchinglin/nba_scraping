# NBA Award Prediction

## Summary

This project scraps all NBA players' statistics between 1976-2020, cleans the data, and builds a predictive model making prediction on whether the player will win an NBA award the following year. In addition, a function with clustering using the embedded distance finds players with a similar playstyle to the player in interest (Who can be the next LeBron James?)

## Packages Used

In this project, **BeautifulSoup** is used for web scraping, **sqlite3** is used for data storage, **pandas** is used for data cleaning, and **scikit-learn** is used for building predictive models.

## Description of Dataset

The dataset comes from https://www.basketball-reference.com. There are many different categories of statistics on this website, including traditional, advanced, and shooting. The traditional statistics includes points, rebounds, assists, steals, blocks, etc. The advanced statistics includes functions of traditional stats as estimators of the players' performance or values. The shooting statistics divides the basketball court into many parts and record the players' shooting frequency and efficiency on each part.

In addition to that, one can also scrap the data on player awards. By storing the data into different SQL tables with primary keys and foreign keys, one can easily recreate suitable tables for analysis.

In terms of the predictors, most of them are quantitative variables, and there are a lot of dependence between predictors. For example, total points correlates strongly with total minutes played, as with all raw counting statistics. To some extent, the three pointers made, three pointers attempted, and three pointer percentage correlate strongly as well.

## Methodology

### Data Cleaning

The dataset appends an asterisk after the player's name if he has been voted into the hall of fame. It presents a problem when one tries to look up players, so custom functions were written in [spyder_cleaning.py](spyder_cleaning.py) to deal with this.

For a given year, players may be traded mid-season, and that results in two or more entries per year. Since some statistics are counted as total over the season (traditional statistics) and others are calculated as an average (advanced statistics), they need to be treated differently.



