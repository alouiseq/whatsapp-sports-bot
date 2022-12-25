from flask import Flask, request
import requests
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime, timedelta
import pdb

app = Flask(__name__)

FAILED_MSG = 'I cannot find what you are searching for.'
NO_DATA_MSG = 'Whoops, I seem to be missing that {} data!'
REQ_NOT_MET_MSG = 'No {} games meet the requirements.'

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

class Game_NBA:
    def __init__(self, game):
        self.team1 = game['teams']['visitors']['nickname']
        self.team1q1 = int(game['scores']['visitors']['linescore'][0])
        self.team1q2 = int(game['scores']['visitors']['linescore'][1])
        self.team2 = game['teams']['home']['nickname']
        self.team2q1 = int(game['scores']['home']['linescore'][0])
        self.team2q2 = int(game['scores']['home']['linescore'][1])
        self.quarter = game['periods']['current']
        self.halftime = game['status']['halftime']
        self.teams_meta = f'({self.team1} at {self.team2})'

        team1_id = game['teams']['visitors']["id"]
        team2_id = game['teams']['home']["id"]
        self.played_yesterday = self.check_game_yesterday(team1_id, team2_id)
        result_msg = None

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
            self.result_msg = f'This is a really solid position! {this.teams_meta}'
            return True
        elif score_count >= 3:
            self.result_msg = f'Not great, but this is a good position! {this.teams_meta}'
            return True
        elif score_count >= 1 and quarter == 2:
            self.result_msg = f'It\'s 2nd Quarter, but this has potential. {this.teams_meta}'
            return True

        return False 

class Game_NFL:
    def __init__(self, game):
        self.team1 = game['teams']['away']['name']
        self.team1_total = game['scores']['away']['total']
        self.team2 = game['teams']['home']['name']
        self.team2_total = game['scores']['home']['total']
        self.quarter = game['game']['status']['short']

        team1_id = game['teams']['away']["id"]
        team2_id = game['teams']['home']["id"]

        teams_meta = f'({self.team1}:{self.team1_total} at {self.team2}:{self.team2_total})'
        trigger_total_msg = f'This is a really solid position, take the 2h total under! {self.teams_meta}'
        trigger_team_total_msg = f'This is a solid position for the team, take the 2h TEAM total under! {self.teams_meta}'
        close_total_msg = f'It\'s 2nd Quarter, but 2h total has potential. {self.teams_meta}'
        close_team_total_msg = f'It\'s 2nd Quarter, but 2h TEAM total has potential. {self.teams_meta}'
        result_msg = None

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

        def checkTotalMet(actual, expected):
            if actual >= expected:
                return True
            return False


        if self.quarter == 'HT':
            if (checkTotalMet(self.team1_total, high_score) and checkTotalMet(self.team2_total, low_score)) or (checkTotalMet(self.team2_total, high_score) and checkTotalMet(self.team1_total, low_score)):
               self.result_msg = trigger_total_msg
            elif checkTotalMet(self.team1_total, max_score) or checkTotalMet(self.team2_total, max_score):
               self.result_msg = trigger_team_total_msg
        elif self.quarter == 'Q2':
            if (checkTotalMet(self.team1_total, low_score) and checkTotalMet(self.team2_total, min_score)) or (checkTotalMet(self.team2_total, low_score) and checkTotalMet(self.team1_total, min_score)):
               self.result_msg = close_total_msg 
            elif checkTotalMet(self.team1_total, high_score) or checkTotalMet(self.team2_total, high_score):
               self.result_msg = close_team_total_msg 

        if result_msg:
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
        today = str(datetime.utcnow().date())
        querystring = {"live": "all"}

        data = get_json_data(NBA_URL, NBA_HEADERS, querystring)

        if data['results']:
            for game in data['response']:
                game = Game_NBA(game)
                trigger = game.strategy_result()
                if trigger:
                    trigger_msgs.append(f'{game.result_msg} ({game.team1} at {game.team2})')

            if len(trigger_msgs):
                msg.body(', '.join(trigger_msgs))
            else:
                msg.body(REQ_NOT_MET_MSG.format('NBA'))
        else:
            msg.body(NO_DATA_MSG.format('NBA'))
        searched = True

    if 'nfl' in incoming_msg:
        today = str(datetime.utcnow().date())
        querystring = {"live": "all", "league": "1", "season": "2022"}

        data = get_json_data(NFL_URL, NFL_HEADERS, querystring)

        if data['results']:
            for game in data['response']:
                game = Game_NFL(game)
                trigger = game.strategy_result()
                if trigger:
                    trigger_msgs.append(f'{game.result_msg} ({game.team1} at {game.team2})')

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
