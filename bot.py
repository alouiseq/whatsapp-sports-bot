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
REQ_NOT_MET_MSG = 'No {} games meet the requirements!'

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
