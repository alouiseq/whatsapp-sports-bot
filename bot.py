from flask import Flask, request
import requests
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime, timedelta
import pdb

from nba import Games_NBA, Game_NBA, Record_NBA
from nfl import Games_NFL, Game_NFL, Record_NFL
from helpers import get_json_data

app = Flask(__name__)

FAILED_MSG = 'I cannot find what you are searching for.'
NO_DATA_MSG = 'Whoops, no {} games are playing right now!'

LIVE_GAMES = 'all'
SEASON = 2022

def get_game_count(incoming_msg):
    imsgs = incoming_msg.split()

    for imsg in imsgs:
        try:
            if int(imsg):
                return int(imsg)
        except ValueError:
            pass
    return None


@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body' '').lower()
    resp = MessagingResponse()
    msg = resp.message()
    searched = False
    trigger_msgs = []

    if 'nba' in incoming_msg:
        numof_games = get_game_count(incoming_msg)

        if numof_games:
            record_nba = Record_NBA(numof_games)
            final_record_msg = record_nba.aggregate_records()
            msg.body(final_record_msg)
        else:
            games_nba = Games_NBA({"live": LIVE_GAMES})
            games = games_nba.fetch_games()
            if len(games):
                for game in games:
                    game_nba = Game_NBA(game)
                    returned_msg = game_nba.run()
                    msg.body(returned_msg)
            else:
                msg.body(NO_DATA_MSG.format('NBA'))

        searched = True

    if 'nfl' in incoming_msg:
        numof_games = get_game_count(incoming_msg)

        if numof_games:
            record_nba = Record_NBA(numof_games)
            final_record_msg = record_nba.aggregate_records()
            msg.body(final_record_msg)
        else:
            games_nfl = Games_NFL({"live": LIVE_GAMES, "season": SEASON})
            games = games_nfl.fetch_games()
            if len(games):
                for game in games:
                    game_nfl = Game_NFL(game)
                    returned_msg = game_nfl.run()
                    msg.body(returned_msg)
            else:
                msg.body(NO_DATA_MSG.format('NFL'))

        searched = True

    if not searched:
        msg.body(FAILED_MSG)

    return str(resp)

if __name__ == '__main__':
    app.run(port=4000)
