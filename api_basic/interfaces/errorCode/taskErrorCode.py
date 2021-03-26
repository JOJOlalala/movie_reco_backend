from enum import Enum

# all user error code start with 01**


class TaskErrorCode(Enum):
    unknown_task = '0201'
    empty_task = '0202'
    unprocessed_video = '0203'
    wrong_update_form = '0204'
    task_already_exist = '0205'
    permission_deny = '0206'
    lack_of_params = '0207'
    unexist_index = '0208'
