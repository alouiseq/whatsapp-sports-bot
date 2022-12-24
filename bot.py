from flask import Flask, request
import requests
from twilio.twiml.messaging_response import MessagingResponse
import datetime

app = Flask(__name__)

no_data_msg = 'Whoops, I seem to be missing that data!'


# nba game metadata
class Game_NBA = {
    def __init__(self, game):
        self.team1 = game['teams']['visitors']['nickname']
        self.team1q1 = game['scores']['visitors']['linescore'][0]
        self.team1q2 = game['scores']['visitors']['linescore'][1]
        self.team2 = game['teams']['home']['nickname']
        self.team2q1 = game['scores']['home']['linescore'][0]
        self.team2q2 = game['scores']['home']['linescore'][1]
        self.quarter = periods['current']
        self.played_yesterday = played_yesterday
        self.halftime =game['status']['halftime']

    # nba strategy engine logic
    def strategy_result_msg(self):
        score_count = 0

        if quarter > 2 or quarter == 1:
            return None
        if self.halftime:
            if team1q2 >= 30:
                score_count += 1
            if team2q2 >= 30:
                score_count += 1
        team1q1 >= 30:
            score_count += 1
        team2q1 >= 30:
            score_count += 1

        if score_count >= 3 and self.played_yesterday:
            return "This is a really solid position!"
        elif score_count >= 3:
            return "Not great, but this is a good position!"
        elif score_count >= 1 and quarter == 2:
            return "It's 2nd Quarter, but this has potential"

        return None
}

def getJsonData(req_url, headers={'accept': 'application/json'}):
    r = requests.get(req_url, headers=headers)
    if r.status_code == 200:
        return r.json()

@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body' '').lower()
    resp = MessagingResponse()
    msg = resp.message()
    searched = False

    if 'nba' in incoming_msg:
        url = "https://api-nba-v1.p.rapidapi.com/games"
        headers = {
            "X-RapidAPI-Key": "d16b6e4142mshfff4f1f121ab449p1088cajsnfabf9adc12f5",
            "X-RapidAPI-Host": "api-nba-v1.p.rapidapi.com"
        }
        querystring = {"live": "all", "date": str(datetime.date.today())}

        data = getJsonData(url, headers, querystring)

        if data:
            for game in data.response:
            game = Game_NBA(game)
            result_msg = game.strategy_result_msg()
            if result_msg:
                msg.body(f'{result_msg} ({game.team1} vs {game.team2})')

        searched = True
    if not searched:
        msg.body(no_data_msg)

    return str(resp)

if __name__ == '__main__':
    app.run(port=4000)
