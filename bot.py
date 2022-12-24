from flask import Flask, request
import requests
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime, timedelta
import pdb

app = Flask(__name__)

NO_DATA_MSG = 'Whoops, I seem to be missing that data!'
FAILED_MSG = 'No games meet the requirements.'

NBA_URL = "https://api-nba-v1.p.rapidapi.com/games"
NBA_HEADERS = {
    "X-RapidAPI-Key": "d16b6e4142mshfff4f1f121ab449p1088cajsnfabf9adc12f5",
    "X-RapidAPI-Host": "api-nba-v1.p.rapidapi.com"
}

# nba game metadata
class Game_NBA:
    def __init__(self, game):
        self.team1 = game['teams']['visitors']['nickname']
        self.team1q1 = game['scores']['visitors']['linescore'][0]
        self.team1q2 = game['scores']['visitors']['linescore'][1]
        self.team2 = game['teams']['home']['nickname']
        self.team2q1 = game['scores']['home']['linescore'][0]
        self.team2q2 = game['scores']['home']['linescore'][1]
        self.quarter = periods['current']
        self.halftime =game['status']['halftime']

        team1_id = game['teams']['visitors']["id"]
        team2_id = game['teams']['home']["id"]
        self.played_yesterday = self.check_game_yesterday(team1_id, team2_id)

    def check_game_yesterday(self, team1_id, team2_id):
        yesterday = str(datetime.utcnow().date() - timedelta(1))
        querystring1 = {"season": "2022", "team": str(team1_id), "date": yesterday}
        querystring2 = {"season": "2022", "team": str(team2_id), "date": yesterday}
        data1 = getJsonData(NBA_URL, NBA_HEADERS, querystring1)
        data2 = getJsonData(NBA_URL, NBA_HEADERS, querystring2)

        if data1 and data2:
            return True if data1.results or data2.results else False
        else:
            return False


    def strategy_result_msg(self):
        score_count = 0

        if quarter > 2 or quarter == 1:
            return None
        if self.halftime:
            if team1q2 >= 30:
                score_count += 1
            if team2q2 >= 30:
                score_count += 1

        if team1q1 >= 30:
            score_count += 1
        if team2q1 >= 30:
            score_count += 1

        if score_count >= 3 and self.played_yesterday:
            return "This is a really solid position!"
        elif score_count >= 3:
            return "Not great, but this is a good position!"
        elif score_count >= 1 and quarter == 2:
            return "It's 2nd Quarter, but this has potential"

        return None

def getJsonData(req_url, headers={'accept': 'application/json'}, params={}):
    r = requests.get(req_url, headers=headers, params=params)
    if r.status_code == 200:
        return r.json()

@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body' '').lower()
    resp = MessagingResponse()
    msg = resp.message()
    searched = False

    if 'nba' in incoming_msg:
        today = str(datetime.utcnow().date())
        querystring = {"live": "all"}

        data = getJsonData(NBA_URL, NBA_HEADERS, querystring)

        if data['results']:
            for game in data['response']:
                game = Game_NBA(game)
                result_msg = game.strategy_result_msg()
                if result_msg:
                    msg.body(f'{result_msg} ({game.team1} vs {game.team2})')

        msg.body(FAILED_MSG)

        searched = True
    if not searched:
        msg.body(NO_DATA_MSG)

    return str(resp)

if __name__ == '__main__':
    app.run(port=4000)
