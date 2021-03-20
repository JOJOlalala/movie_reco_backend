import json


class JsonResponseMsg:
    'return message'
    name = ''
    description = 0

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def get_dict_data(name, description):
        return JsonResponseMsg(name, description).__dict__
