class PayloadException(Exception):
    def __init__(self, content):
        self.content = "Invalid %s" % content
        # Call the base class constructor with the parameters it needs
        super().__init__(self.content)