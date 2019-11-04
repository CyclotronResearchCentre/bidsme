import re

def cleanup_value(label):
    """
    Converts a given label to a cleaned-up label
    that can be used as a BIDS label. 
    Remove leading and trailing spaces;
    convert other spaces, special BIDS characters and anything 
    that is not an alphanumeric to a ''. This will for example 
    map "Joe's reward_task" to "Joesrewardtask"

    :param label:   The given label
    :return:        The cleaned-up / BIDS-valid labe
    """

    if label is None:
        return label
    special_characters = (' ', '_', '-','.')
    for special in special_characters:
        label = str(label).strip().replace(special, '')

    return re.sub(r'(?u)[^-\w.]', '', label)

def match_value(val, regexp, force_str=False):
    if force_str:
        val = str(val).strip()
        regexp = regexp.strip()
        return (re.fullmatch(regexp, val) is not None)

    if isinstance(regexp, str):
        val = str(val).strip()
        regexp = regexp.strip()
        return (re.fullmatch(regexp, val) is not None)
    return val == regexp
