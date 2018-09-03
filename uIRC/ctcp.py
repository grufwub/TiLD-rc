import re

LOW_LEVEL_QUOTE = "\x10"
LEVEL_QUOTE = "\\"
DELIMITER = "\x01"

low_level_mapping = {
    "0": "\x00",
    "n": "\n",
    "r": "\r",
    LEVEL_QUOTE: LEVEL_QUOTE
}

low_level_regexp = re.compile( LOW_LEVEL_QUOTE + "(.)" )

def _low_level_replace(match_obj):
    ch = match_obj.group(1)
    # If low_level_mapping doesn't have the character as key,
    # we should just return the character
    return low_level_mapping.get(ch, ch)

def dequote(message):
    """
    Dequote a message according to CTCP specifications
    """

    # Perform the substitution
    message = low_level_regexp.sub(_low_level_replace, message)
    if DELIMITER not in message: return list(message)
    
    # Split it into parts
    chunks = message.split(DELIMITER)
    return list(_gen_messages(chunks))

def _gen_messages(chunks):
    i = 0

    while i < len(chunks) - 1:
        # Add message if it's non-empty
        if len(chunks[i]) > 0:
            yield chunks[i]
        
        if i < len(chunks) - 2:
            # Aye! CTCP tagged data ahead!
            yield tuple(chunks[i + 1].split(" ", 1))
        
        i = i + 2
    
    if len(chunks) % 2 == 0:
        # Hey, a lonely CTCP delimiter at the end! This means
        # that the last chunk, including delimiter, is a normal
        # message. (according to CTCP spec)
        yield DELIMITER + chunks[-1]