from helpers import get_json_data, API_KEY

NFL_URL = "https://api-american-football.p.rapidapi.com/games"
NFL_HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "api-american-football.p.rapidapi.com"
}

class Record_NFL:
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
            data = get_json_data(NBA_URL, NFL_HEADERS, querystring)

            if data and data['results']:
                game_counter += data['results']
                games.extend(data['response'])

        return games[0:self.last_num_games]

    def run_game_engine(self, game):
        # TODO: refactor this copied code to be NFL specific
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

    def aggregate_records(self):
        games = self.fetch_games()

        for game in games:
            self.run_game_engine(game)

        return f'{self.winners} - {self.losers} (wins-losses)'


class Games_NFL:
    def __init__(self, query):
        self.games = []
        self.query = {'league': '1', **query}

    def fetch_games(self):
        data = get_json_data(NFL_URL, NFL_HEADERS, self.query)

        if data['results']:
            self.games.extend(data['response'])
        return self.games


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

    def run(self):
        return self.get_trigger_messages()

    def get_trigger_messages(self):
        trigger_msgs = []

        trigger = self.run_game_engine()
        if trigger:
            trigger_msgs.append(game.result_msg)

        if len(trigger_msgs):
            return ', '.join(trigger_msgs)
        else:
            return REQ_NOT_MET_MSG.format('NFL')

    def check_total_met(self, actual, expected):
        if actual >= expected:
            return True
        return False

    def run_game_engine(self):
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
            if (self.check_total_met(self.team1_total, high_score) and self.check_total_met(self.team2_total, low_score)) or (self.check_total_met(self.team2_total, high_score) and self.check_total_met(self.team1_total, low_score)):
               self.result_msg = self.trigger_total_msg
            elif self.check_total_met(self.team1_total, max_score) or self.check_total_met(self.team2_total, max_score):
               self.result_msg = self.trigger_team_total_msg
        elif self.quarter == 'Q2':
            if (self.check_total_met(self.team1_total, low_score) and self.check_total_met(self.team2_total, min_score)) or (self.check_total_met(self.team2_total, low_score) and self.check_total_met(self.team1_total, min_score)):
               self.result_msg = self.close_total_msg 
            elif self.check_total_met(self.team1_total, high_score) or self.check_total_met(self.team2_total, high_score):
               self.result_msg = self.close_team_total_msg 

        if self.result_msg:
            return True

        return False 

