from utils import utility


def already_error_string(members, action):
    if len(members) == 1:
        return f"The member <@{members[0].id}> is already {action}."
    else:
        return f"The members {', '.join([f'<@{m.id}>' for m in members])} are already {action}."


def higher_error_string(members, action):
    if len(members) == 1:
        return (
            f"I do not have the permissions to {action} the member <@{members[0].id}>."
        )
    else:
        return f"I do not have the permissions to {action} the members {', '.join([f'<@{m.id}>' for m in members])}."


def member_string(everyone, roles, members):
    string = ""

    if everyone:
        string += "everyone"
    else:
        if roles:
            if len(roles) == 1:
                string += f"the role <@&{roles[0].id}>"
            else:
                string += f"the roles {', '.join([f'<@&{r.id}>' for r in roles])}"
            if members:
                string += " and "
        if members:
            if len(members) == 1:
                string += f"the member <@{members[0].id}>"
            else:
                string += f"the members {', '.join([f'<@{m.id}>' for m in members])}"

    return string


def before_string(everyone, roles, members, time, action):
    string = f"{action} ".capitalize()
    string += member_string(everyone, roles, members)

    if time:
        string += f" for `{utility.time_string(time)}`..."
    else:
        string += "..."

    return string


def after_string(everyone, roles, members, time, action):
    string = member_string(everyone, roles, members)
    string = string[0].upper() + string[1:]

    if len(roles) > 1 or len(members) > 1 or (len(roles) == 1 and len(members) == 1):
        string += f" were {action}"
    else:
        string += f" was {action}"

    if time:
        string += f" for `{utility.time_string(time)}`."
    else:
        string += "."

    return string
