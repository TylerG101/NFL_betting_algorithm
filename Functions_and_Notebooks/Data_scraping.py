import requests
from bs4 import BeautifulSoup
import pandas as pd

import pandas as pd

###Scrape statistics from pro-football-reference.com stats for the desired week are taken as an average over the previous 5 games.
###Unless there have been fewer than 5 games played in the season, then it will be an average of all previous games this season
def create_prediction_input_stat(team, opponent, week):
    team_names = {'Cardinals':'crd', 'Falcons':'atl', 'Ravens':'rav', 'Bills':'buf', 'Panthers':'car', 'Bears':'chi', 'Bengals':'cin', 'Browns':'cle', 'Cowboys':'dal', 'Broncos':'den', 'Lions':'det', 'Packers':'gnb', 'Texans':'htx', 'Colts':'clt', 'Jaguars':'jax', 'Chiefs':'kan', 'Raiders':'rai',
             'Chargers':'sdg', 'Rams':'ram', 'Dolphins':'mia', 'Vikings':'min', 'Patriots':'nwe', 'Saints':'nor', 'Giants':'nyg', 'Jets':'nyj', 'Eagles':'phi', 'Steelers':'pit', 'Seahawks':'sea', '49ers':'sfo', 'Buccaneers':'tam', 'Titans':'oti', 'Washington':'was'}
    
    stats = {'Pass Yds':'Yds',  'Rush Yds':'Yds.2', 'Points per game':'Pts', 'Sacks':'Sk', 
             'Cmp':'Cmp%', 'Plays':'Ply', '3DConv':'3DConv', 'Yards per Play':'Y/P'}
    
    avg_stats = pd.DataFrame()
    

    url = 'https://www.pro-football-reference.com/teams/' + team + '/2024/gamelog/'
    team_df = pd.read_html(url, header=1, attrs={'id':'table_pfr_team-year_game-logs_team-year-regular-season-game-log'})[0]
    opp_df = pd.read_html(url, header=1, attrs={'id':'table_pfr_team-year_game-logs_team-year-regular-season-opponent-game-log'})[0]

    location = team_df['Unnamed: 5'][week-1]
    team_df = team_df.head(week-1)
    opp_df = opp_df.head(week-1)

    ###Append the features that do not need averaging to our empty df
    for feat in [week, location, team, opponent]:
        col = [f'{feat}']  
        df = pd.DataFrame(col)
        avg_stats = pd.concat([avg_stats, df], axis=1)
    avg_stats.columns = ['Week', 'Location', 'Team', 'Opponent']



    for stat in stats:
        if stat == '3DConv':
            t_3rd = 0
            o_3rd = 0
            if week > 5:
                #Average 3rd down conversion rate from the previous 5 games
                for i in range(2,7):
                    t_3rd += team_df['3DConv'][week-i] / team_df['3DAtt'][week-i]
                    o_3rd += opp_df['3DConv'][week-i] / opp_df['3DAtt'][week-i]
                avg_t_3rd = [t_3rd/5]
                avg_o_3rd = [o_3rd/5]
            else:
                ###Average 3rd down conversion rate from all previous games in the season if there are less than 5
                for i in range(2,week+1):
                    t_3rd += team_df['3DConv'][week-i] / team_df['3DAtt'][week-i]
                    o_3rd += opp_df['3DConv'][week-i] / opp_df['3DAtt'][week-i]
                avg_t_3rd = [t_3rd/(week-1)]
                avg_o_3rd = [o_3rd/(week-1)]
                
            thd_df = pd.DataFrame(avg_t_3rd)
            thd_a_df = pd.DataFrame(avg_o_3rd)
            thd_df.columns = ['3DConv']
            thd_a_df.columns = ['3DConv Allowed']
            avg_stats = pd.concat([avg_stats, thd_df, thd_a_df], axis=1)


        else:
            t_pg = 0
            o_pg = 0
            if week > 5:
                ###Average of stat from the previous 5 games
                for i in range(2,7):
                    t_pg += team_df[stats[stat]][week-i]
                    o_pg += opp_df[stats[stat]][week-i]
                avg_t_pg = [t_pg/5]
                avg_o_pg = [o_pg/5]
            else:
                ###Average of stat from all previous games in the season if there are less than 5
                for i in range(2,week+1):
                    t_pg += team_df[stats[stat]][week-i]
                    o_pg += opp_df[stats[stat]][week-i]
                avg_t_pg = [t_pg/(week-1)]
                avg_o_pg = [o_pg/(week-1)]
            
            cur_team_df = pd.DataFrame(avg_t_pg)
            cur_team_df.columns = [stat]
            cur_opp_df = pd.DataFrame(avg_o_pg)
            cur_opp_df.columns = ["Opp " + stat]

            avg_stats = pd.concat([avg_stats, cur_team_df, cur_opp_df], axis=1)
            

    return avg_stats




###Scrape nflweather.com to get the weather and temperature outlook for the desired game
###**Note this data will likely be more accurate to the actual gameday conditions as the function called closer to game date
def create_prediction_input_weather(team, week):
    team_names = {'crd':'Cardinals', 'atl':'Falcons', 'rav':'Ravens', 'buf':'Bills', 'car':'Panthers', 'chi':'Bears', 'cin':'Bengals', 'cle':'Browns', 'dal':'Cowboys', 'den':'Broncos', 'det':'Lions', 'gnb':'Packers', 'htx':'Texans', 'clt':'Colts', 'jax':'Jaguars', 'kan':'Chiefs', 'rai':'Raiders',
             'sdg':'Chargers', 'ram':'Rams', 'mia':'Dolphins', 'min':'Vikings', 'nwe':'Patriots', 'nor':'Saints', 'nyg':'Giants', 'nyj':'Jets', 'phi':'Eagles', 'pit':'Steelers', 'sea':'Seahawks', 'sfo':'49ers', 'tam':'Buccaneers', 'oti':'Titans', 'was':'Washington'}
    
    url = 'https://www.nflweather.com/week/2025/week-' + str(week)
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    base_df = pd.DataFrame()

    # Find all game weather rows
    games = soup.find_all(class_='mx-2')
    #Get correspoinding team names
    teams = soup.find_all('span', class_="fw-bold")

    #Get team names from html for matchups
    team_list = []
    for i in range(len(teams)):
        text = teams[i].get_text()
        if text != '@':
            team_list.append(text)
        
    #Create a list of matchups from team_list that correspond to the weather data
    matchups = []
    n = 0
    while n < len(team_list) - 1:
        vs = team_list[n] + " " + team_list[n+1]
        matchups.append(vs)
        n += 2  
    #Get the temperature and weather data from html
    m = 0
    temp = []
    weather = []
    while m < len(games):
        stripped_temp = games[m]
        stripped_weat = games[m+1]
        temp.append(games[m].get_text())
        weather.append(games[m+1].get_text())
        m += 2

    ###Combine data for matchup, temp, and weather into one df
    Matchup_df = pd.DataFrame(matchups)
    temp_df = pd.DataFrame(temp)
    weather_df = pd.DataFrame(weather)
    combined = pd.concat([Matchup_df, temp_df, weather_df], axis=1, ignore_index=True)
    combined.columns = ["Matchup", "Temperature", "Weather"]
    combined['Week'] = float(week)

    base_df = pd.concat([base_df, combined], axis=0)

    ###Of all games in the chosen week, we pick out the one with our desired team
    for index, game in base_df.iterrows():
        if team_names[team] in game.iloc[0]:
            target_game = pd.Series(game)
        
    target_game = pd.DataFrame(target_game).T 
    target_game.index = [0]

    return target_game





###Combine the data from both dataframes scraped in the above functions
def create_raw_input(team, opponent, week):
    stats_df = create_prediction_input_stat(team, opponent, week)
    weather_df = create_prediction_input_weather(team, week)

    return pd.concat([stats_df, weather_df["Temperature"], weather_df["Weather"]], axis=1)

create_raw_input('nyg', 'sdg', week=4)

