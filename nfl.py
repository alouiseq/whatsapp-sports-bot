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

