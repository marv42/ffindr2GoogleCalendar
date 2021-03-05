from xml.sax.handler import ContentHandler


class FfindrChannelContentHandler(ContentHandler):

    def __init__(self):
        super().__init__()
        self.inChannelContent = True
        self.inTitleContent = False

    def startElement(self, name, attrs):
        if name == 'item':
            # exclude item content
            self.inChannelContent = False
        elif self.inChannelContent:
            if name == 'title':
                self.inTitleContent = True
                self.title = ""

    def characters(self, ch):
        if self.inTitleContent:
            self.title = self.title + ch

    def ignorableWhitespace(self, ch):
        if self.inTitleContent:
            self.title = self.title + ch

    def endElement(self, name):
        if name == 'title':
            self.inTitleContent = False

    def get_title(self):
        return self.title
