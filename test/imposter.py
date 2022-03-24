class ImposterMessage:
    def __init__(self):
        self.attachments = []
        self.content = ""


class ImposterAttachment:
    def __init__(self, filename: str):
        self.filename = filename
