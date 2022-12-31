def convert_to_int(value):
    return int(value) if value else value

def get_json_data(req_url, headers={'accept': 'application/json'}, params={}):
    r = requests.get(req_url, headers=headers, params=params)
    if r.status_code == 200:
        return r.json()

