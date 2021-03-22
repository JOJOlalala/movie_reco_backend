from enum import Enum

# all user error code start with 01**


class UserErrorCode(Enum):
    unknown_user = '0101'
    auth_failed = '0102'
    wrong_password = '0103'
    wrong_update_form = '0104'
    user_already_exist = '0105'
