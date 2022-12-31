from datetime import datetime, timedelta
from helpers import convert_to_int, get_json_data, API_KEY

MIN_SCORE_NBA = 30
THIRD_QT_TOTAL = 55
NBA_URL = "https://api-nba-v1.p.rapidapi.com/games"
NBA_HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "api-nba-v1.p.rapidapi.com"
}

class Record_NBA:
    def __init__(self, last_num_games):
        self.last_num_games = last_num_games
        self.final_record = ''
        self.winners = 0
        self.losers = 0

    def fetchGames(self):
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

    def game_engine(self, game):
        team1_scores = game['scores']['visitors']['linescore']
        team2_scores = game['scores']['home']['linescore']

        qt_goals_met = 0
        qt_needed = 3

        try:
            if int(team1_scores[0]) >= MIN_SCORE_NBA:
                qt_goals_met += 1
            if int(team1_scores[1]) >= MIN_SCORE_NBA:
                qt_goals_met += 1
            if int(team2_scores[0]) >= MIN_SCORE_NBA:
               qt_goals_met += 1
            if int(team2_scores[1]) >= MIN_SCORE_NBA:
               qt_goals_met += 1

            if qt_goals_met < qt_needed:
                pass
            elif int(team1_scores[2]) + int(team2_scores[2]) <= THIRD_QT_TOTAL:
                self.winners += 1
            else:
                self.losers += 1
        except ValueError:
            pass

    def aggregateRecords(self):
        games = self.fetchGames()

        for game in games:
            self.game_engine(game)

        return f'{self.winners} - {self.losers} (wins-losses)'


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

        team1_id = game['teams']['visitors']["id"]
        team2_id = game['teams']['home']["id"]
        self.played_yesterday = self.check_game_yesterday(team1_id, team2_id)

    def start:
        return self.fetchGames()

    def check_game_yesterday(self, team1_id, team2_id):
        yesterday = str(datetime.utcnow().date() - timedelta(1))
        querystring1 = {"season": "2022", "team": str(team1_id), "date": yesterday}
        querystring2 = {"season": "2022", "team": str(team2_id), "date": yesterday}
        data1 = get_json_data(NBA_URL, NBA_HEADERS, querystring1)
        data2 = get_json_data(NBA_URL, NBA_HEADERS, querystring2)

        if data1 and data2:
            return True if data1['results'] or data2['results'] else False
        else:
            return False

    def fetchGames(self):
        querystring = {"live": "all"}

        data = get_json_data(NBA_URL, NBA_HEADERS, querystring)

        if data['results']:
            for game in data['response']:
                game = Game_NBA(game)
                trigger = game.game_engine()
                if trigger:
                    trigger_msgs.append(game.result_msg)

            if len(trigger_msgs):
                return ', '.join(trigger_msgs)
            else:
                return REQ_NOT_MET_MSG.format('NBA')
        else:
            return NO_DATA_MSG.format('NBA')

    def game_engine(self):
        score_count = 0
        min_score = 30

        if self.quarter > 2 or self.quarter == 1:
            return None
        if self.halftime:
            if self.team1q2 >= min_score:
                score_count += 1
            if self.team2q2 >= min_score:
                score_count += 1

        if self.team1q1 >= min_score:
            score_count += 1
        if self.team2q1 >= min_score:
            score_count += 1

        if score_count >= 3 and self.played_yesterday:
            self.result_msg = self.trigger_total_msg
        elif score_count >= 3:
            self.result_msg = self.consider_total_msg
        elif score_count >= 1 and self.quarter == 2 and not self.halftime:
            self.result_msg = self.close_total_msg

        if self.result_msg:
            return True

        return False 
