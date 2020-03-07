import os
import time

from kivy.app import App
from kivy.core.window import Window


class GifPlayerApp(App):

    def build(self):
        Window.bind(on_dropfile=self.on_dropfile)

    def on_dropfile(self, *args, **kwargs):
        print(args, kwargs)


if __name__ == '__main__':
    app = GifPlayerApp()
    app.run()
