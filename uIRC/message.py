__metaclass__ = type

class Tag:
    """
    IRC message tag
    """

    @staticmethod
    def parse(item):
        key, sep, value = item.partition("=")
        value = value.replace("\\:", ";")
        value = value.replace("\\s", " ")
        value = value.replace("\\n", "\n")
        value = value.replace("\\r", "\r")
        value = value.replace("\\\\", "\\")
        value = value or None

        return {
            "key": key,
            "value": value,
        }
    
    @classmethod
    def from_group(cls, group):
        """
        Construct tags from regex group
        """

        if not group: return
        tag_items = group.split(";")
        return list(map(cls.parse, tag_items))

class Arguments(list):
    @staticmethod
    def from_group(group):
        """
        Construct arguments from the regex group
        """

        if not group: return list()
        main, sep, ext = group.partition(" :")
        arguments = main.split()
        if sep: arguments.append(ext)
        return arguments