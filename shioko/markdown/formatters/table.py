# Note:
# - On linux, kivy requires `xclip` and `xsel`, which are not installable with pip.

from kivy.app import App
from kivy.core.window import Window
from kivy.logger import Logger

from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty

from parsers.table import Formatter


class TableFormatter(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # self.layout = FloatLayout(
        #     # size_hint=(1, 1),
        #     # size=(450, 450),
        #     # pos=(0, 0),
        # )
        self.layout = BoxLayout()

        self.input_tb = TextInput(
            text='some_text',
            # size=(self.width / 2, self.height),
            size=(450, 450),
            # size_hint=(.5, 1),
            # pos=(0, 0),
            # background_color=(0, 0, 0, 1),
            # foreground_color=(1, 1, 1, 1),
        )

        self.output_tb = TextInput(
            # size=(self.width / 2, self.height),
            # size=(200, 600),
            # size_hint=(.5, 1),
            # pos=(self.width / 2, 0),
            # readonly=True,
            # background_color=(0.1, 0.1, 0.1, 1),
            # foreground_color=(1, 1, 1, 1),
        )

        self.layout.add_widget(self.input_tb)
        self.layout.add_widget(self.output_tb)

    def build(self):
        return self.layout


class TableFormatterApp(App):

    # input_tb = ObjectProperty(None)
    # output_tb = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.table_formatter = TableFormatter()

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        # Logger.info(f'key={key}, scancode={scancode}, codepoint={codepoint}, modifier={modifier}')
        # Enter: 13
        if ('shift' in modifier) and (key == 13):
            # self.output_tb.text = self.input_tb.text
            print(self.table_formatter.input_tb)
            print(self.table_formatter.output_tb)

    def build(self):
        # bind our handler
        Window.bind(on_keyboard=self.on_keyboard)
        return self.table_formatter


if __name__ == '__main__':
    app = TableFormatterApp()
    app.run()
