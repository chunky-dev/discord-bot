class ImposterMessage:
    def __init__(self):
        self.attachments = []
        self.content = ""
        self.embeds = []


class ImposterAttachment:
    def __init__(self, filename: str):
        self.filename = filename
