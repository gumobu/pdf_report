from unittest import TestCase
from project.colors_and_styles import Colors


class TestColors(TestCase):
    def setUp(self) -> None:
        self.clr = Colors()

    def test_header(self):
        self.assertEqual(self.clr.header('a'), '\033[95ma\033[0m')

    def test_bold(self):
        self.assertEqual(self.clr.bold('some text'), '\033[1msome text\033[0m')

    def test_underline(self):
        self.assertEqual(self.clr.underline('another line'), '\033[4manother line\033[0m')

    def test_blue(self):
        self.assertEqual(self.clr.blue('try this'), '\033[94mtry this\033[0m')

    def test_cyan(self):
        self.assertEqual(self.clr.cyan('fifth try!'), '\033[96mfifth try!\033[0m')

    def test_green(self):
        self.assertEqual(self.clr.green('and again...'), '\033[92mand again...\033[0m')

    def test_orange(self):
        self.assertEqual(self.clr.orange('why NoT?!'), '\033[93mwhy NoT?!\033[0m')

    def test_red(self):
        self.assertEqual(self.clr.red('finally&#$'), '\033[91mfinally&#$\033[0m')


if __name__ == '__main__':
    TestColors()
