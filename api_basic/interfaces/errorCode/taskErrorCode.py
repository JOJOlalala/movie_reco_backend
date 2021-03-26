from enum import Enum

# all user error code start with 01**


class TaskErrorCode(Enum):
    unknown_task = '0201'
    empty_task = '0202'
    unprocessed_video = '0203'
    wrong_update_form = '0204'
