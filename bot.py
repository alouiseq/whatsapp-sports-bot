from flask import Flask, request
import requests
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime, timedelta
import pdb

from nba import Game_NBA, Record_NBA
from nfl import Game_NFL, Record_NFL
from helpers import get_json_data

app = Flask(__name__)

FAILED_MSG = 'I cannot find what you are searching for.'
NO_DATA_MSG = 'Whoops, no {} games are playing right now!'

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
            final_record_msg = record_nba.aggregateRecords()
            msg.body(final_record_msg)
        else:
            games = Games_NBA({"live": "all"})
            if len(games):
                for game in games:
                    game_nba = Game_NBA(game)
                    returned_msg = game_nba.run()
                    msg.body(returned_msg)
            else:
                msg.body(NO_DATA_MSG.format('NBA'))

        searched = True

    if 'nfl' in incoming_msg:
        nfl_games = Game_NFL()
        returned_msg = nfl_games.run()
        msg.body(returned_msg)
        searched = True

    if not searched:
        msg.body(FAILED_MSG)

    return str(resp)

if __name__ == '__main__':
    app.run(port=4000)
