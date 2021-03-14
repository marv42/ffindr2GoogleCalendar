from xml.sax.handler import ContentHandler

from Constants import DOM_ITEM, DOM_TITLE


class FfindrChannelContentHandler(ContentHandler):

    def __init__(self):
        super().__init__()
        self.inChannelContent = True
        self.inTitleContent = False

    def startElement(self, name, attrs):
        if name == DOM_ITEM:
            # exclude item content
            self.inChannelContent = False
        elif self.inChannelContent:
            if name == DOM_TITLE:
                self.inTitleContent = True
                self.title = ""

    def characters(self, ch):
        if self.inTitleContent:
            self.title = self.title + ch

    def ignorableWhitespace(self, ch):
        if self.inTitleContent:
            self.title = self.title + ch

    def endElement(self, name):
        if name == DOM_TITLE:
            self.inTitleContent = False

    def get_title(self):
        return self.title
