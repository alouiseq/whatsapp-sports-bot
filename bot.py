from flask import Flask, request
import requests
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime, timedelta
import pdb

app = Flask(__name__)

FAILED_MSG = 'I cannot find what you are searching for.'
NO_DATA_MSG = 'Whoops, no {} games are playing right now!'
REQ_NOT_MET_MSG = 'No {} games meet the requirements!'

API_KEY = "d16b6e4142mshfff4f1f121ab449p1088cajsnfabf9adc12f5"

NBA_URL = "https://api-nba-v1.p.rapidapi.com/games"
NBA_HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "api-nba-v1.p.rapidapi.com"
}

NFL_URL = "https://api-american-football.p.rapidapi.com/games"
NFL_HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "api-american-football.p.rapidapi.com"
}

MIN_SCORE_NBA = 30
THIRD_QT_TOTAL = 55

def convertToInt(value):
    return int(value) if value else value

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
        self.team1q1 = convertToInt(game['scores']['visitors']['linescore'][0])
        self.team1q2 = convertToInt(game['scores']['visitors']['linescore'][1])
        self.team2 = game['teams']['home']['nickname']
        self.team2q1 = convertToInt(game['scores']['home']['linescore'][0])
        self.team2q2 = convertToInt(game['scores']['home']['linescore'][1])
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


    def strategy_result(self):
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

class Game_NFL:
    def __init__(self, game):
        self.team1 = game['teams']['away']['name']
        self.team1_total = game['scores']['away']['total']
        self.team2 = game['teams']['home']['name']
        self.team2_total = game['scores']['home']['total']
        self.quarter = game['game']['status']['short']

        teams_meta = f'({self.team1}:{self.team1_total} at {self.team2}:{self.team2_total})'
        self.trigger_total_msg = f'This is a solid position, take the 2h total under! {teams_meta}'
        self.trigger_team_total_msg = f'This is a solid position for the team, take the 2h TEAM total under! {teams_meta}'
        self.close_total_msg = f'It\'s 2nd Quarter, but 2h total has potential. {teams_meta}'
        self.close_team_total_msg = f'It\'s 2nd Quarter, but 2h TEAM total has potential. {teams_meta}'
        self.result_msg = None

    def checkTotalMet(self, actual, expected):
        if actual >= expected:
            return True
        return False

    def strategy_result(self):
        meets_req = False 
        close_to_req = False
        no_trigger_statuses = ['Q1', 'Q3', 'Q4', 'OT', 'FT', 'AOT', 'CANC', 'PST']
        max_score = 20
        high_score = 17
        low_score = 10
        min_score = 7

        if self.quarter in no_trigger_statuses:
            return None

        if self.quarter == 'HT':
            if (self.checkTotalMet(self.team1_total, high_score) and self.checkTotalMet(self.team2_total, low_score)) or (self.checkTotalMet(self.team2_total, high_score) and self.checkTotalMet(self.team1_total, low_score)):
               self.result_msg = self.trigger_total_msg
            elif self.checkTotalMet(self.team1_total, max_score) or self.checkTotalMet(self.team2_total, max_score):
               self.result_msg = self.trigger_team_total_msg
        elif self.quarter == 'Q2':
            if (self.checkTotalMet(self.team1_total, low_score) and self.checkTotalMet(self.team2_total, min_score)) or (self.checkTotalMet(self.team2_total, low_score) and self.checkTotalMet(self.team1_total, min_score)):
               self.result_msg = self.close_total_msg 
            elif self.checkTotalMet(self.team1_total, high_score) or self.checkTotalMet(self.team2_total, high_score):
               self.result_msg = self.close_team_total_msg 

        if self.result_msg:
            return True

        return False 

def get_json_data(req_url, headers={'accept': 'application/json'}, params={}):
    r = requests.get(req_url, headers=headers, params=params)
    if r.status_code == 200:
        return r.json()

@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body' '').lower()
    resp = MessagingResponse()
    msg = resp.message()
    searched = False
    trigger_msgs = []

    if 'nba' in incoming_msg:
        imsgs = incoming_msg.split()
        numof_games = None

        for imsg in imsgs:
            try:
                if int(imsg):
                    numof_games = int(imsg)
                    break
            except ValueError:
                pass

        if numof_games:
            record_nba = Record_NBA(numof_games)
            final_record = record_nba.aggregateRecords()
            msg.body(final_record)
        else:
            querystring = {"live": "all"}

            data = get_json_data(NBA_URL, NBA_HEADERS, querystring)

            if data['results']:
                for game in data['response']:
                    game = Game_NBA(game)
                    trigger = game.strategy_result()
                    if trigger:
                        trigger_msgs.append(game.result_msg)

                if len(trigger_msgs):
                    msg.body(', '.join(trigger_msgs))
                else:
                    msg.body(REQ_NOT_MET_MSG.format('NBA'))
            else:
                msg.body(NO_DATA_MSG.format('NBA'))
        searched = True

    if 'nfl' in incoming_msg:
        querystring = {"live": "all", "league": "1", "season": "2022"}

        data = get_json_data(NFL_URL, NFL_HEADERS, querystring)

        if data['results']:
            for game in data['response']:
                game = Game_NFL(game)
                trigger = game.strategy_result()
                if trigger:
                    trigger_msgs.append(game.result_msg)

            if len(trigger_msgs):
                msg.body(', '.join(trigger_msgs))
            else:
                msg.body(REQ_NOT_MET_MSG.format('NFL'))
        else:
            msg.body(NO_DATA_MSG.format('NFL'))
        searched = True

    if not searched:
        msg.body(FAILED_MSG)

    return str(resp)

if __name__ == '__main__':
    app.run(port=4000)
