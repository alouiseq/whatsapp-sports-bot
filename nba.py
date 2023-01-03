from datetime import datetime, timedelta
from helpers import convert_to_int, get_json_data, API_KEY

MIN_SCORE = 30
SECOND_QT_TOTAL = 58
THIRD_QT_TOTAL = 58
QUARTER_GOAL = 2
NBA_URL = "https://api-nba-v1.p.rapidapi.com/games"
NBA_HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "api-nba-v1.p.rapidapi.com"
}
REQ_NOT_MET_MSG = 'No {} games meet the requirements!'


class Record_NBA:
    def __init__(self, last_num_games):
        self.last_num_games = last_num_games
        self.final_record = ''
        self.winners = 0
        self.losers = 0

    def fetch_games(self):
        game_counter = 0
        day_delta = 0
        games = []

        while game_counter < self.last_num_games:
            date = str(datetime.utcnow().date() - timedelta(day_delta))
            day_delta += 1
            querystring = {"date": date}
            data = get_json_data(NBA_URL, NBA_HEADERS, querystring)

            if data and data['results']:
                game_counter += data['results']
                games.extend(data['response'])

        return games[0:self.last_num_games]

    def run_game_engine(self, game):
        team1_scores = game['scores']['visitors']['linescore']
        team2_scores = game['scores']['home']['linescore']

        qt_goals_met = 0
        qt_needed = 3

        try:
            if int(team1_scores[0]) >= MIN_SCORE:
                qt_goals_met += 1
            if int(team1_scores[1]) >= MIN_SCORE:
                qt_goals_met += 1
            if int(team2_scores[0]) >= MIN_SCORE:
               qt_goals_met += 1
            if int(team2_scores[1]) >= MIN_SCORE:
               qt_goals_met += 1

            if qt_goals_met < qt_needed:
                pass
            elif int(team1_scores[2]) + int(team2_scores[2]) >= THIRD_QT_TOTAL:
                self.winners += 1
            else:
                self.losers += 1
        except ValueError:
            pass

    def aggregate_records(self):
        games = self.fetch_games()

        for game in games:
            self.run_game_engine(game)

        return f'{self.winners} - {self.losers} (wins-losses)'


class Games_NBA:
    def __init__(self, query):
        self.games = []
        self.query = query

    def fetch_games(self):
        data = get_json_data(NBA_URL, NBA_HEADERS, self.query)

        if data and data['results']:
            self.games.extend(data['response'])
        return self.games


class Game_NBA:
    def __init__(self, game):
        self.team1 = game['teams']['visitors']['nickname']
        self.team1q1 = convert_to_int(game['scores']['visitors']['linescore'][0])
        self.team1q2 = convert_to_int(game['scores']['visitors']['linescore'][1])
        self.team2 = game['teams']['home']['nickname']
        self.team2q1 = convert_to_int(game['scores']['home']['linescore'][0])
        self.team2q2 = convert_to_int(game['scores']['home']['linescore'][1])
        self.quarter = game['periods']['current']
        self.halftime = game['status']['halftime']

        teams_meta = f'({self.team1} at {self.team2})'
        self.trigger_total_msg = f'This is a solid position, take the 2h total under! {teams_meta}'
        self.consider_total_msg = f'Not great, but this is a good position, consider the 2h total under! {teams_meta}'
        self.close_total_msg = f'It\'s 2nd Quarter, but 2h total has potential. {teams_meta}'
        self.result_msg = None

        self.team1_id = game['teams']['visitors']["id"]
        self.team2_id = game['teams']['home']["id"]

    def run(self):
        self.played_yesterday = self.check_game_yesterday()
        return self.get_trigger_message()

    def check_game_yesterday(self):
        yesterday = str(datetime.utcnow().date() - timedelta(1))
        querystring1 = {"season": "2022", "team": str(self.team1_id), "date": yesterday}
        querystring2 = {"season": "2022", "team": str(self.team2_id), "date": yesterday}
        data1 = get_json_data(NBA_URL, NBA_HEADERS, querystring1)
        data2 = get_json_data(NBA_URL, NBA_HEADERS, querystring2)

        if data1 and data2:
            return True if data1['results'] or data2['results'] else False
        else:
            return False

    def get_trigger_message(self):
        trigger = self.run_game_engine()
        if trigger:
            return self.game.result_msg
        return None

    def run_game_engine(self):
        qt_goals_met = 0

        if self.quarter > 2 or self.quarter == 1:
            return None
        if self.halftime:
            if self.team1q2 >= MIN_SCORE:
                qt_goals_met += 1
            if self.team2q2 >= MIN_SCORE:
                qt_goals_met += 1

        if self.team1q1 >= MIN_SCORE:
            qt_goals_met += 1
        if self.team2q1 >= MIN_SCORE:
            qt_goals_met += 1

        if self.played_yesterday:
            return False

        if qt_goals_met >= QUARTER_GOAL:
            self.result_msg = self.trigger_total_msg
        elif self.team1q2 + team2q2 < SECOND_QT_TOTAL:
            self.result_msg = self.consider_total_msg
        elif qt_goals_met >= 1 and self.quarter == 2 and not self.halftime:
            self.result_msg = self.close_total_msg

        if self.result_msg:
            return True

        return False 
