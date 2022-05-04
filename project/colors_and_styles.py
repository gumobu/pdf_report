class Colors:
    _HEADER = '\033[95m'
    _END = '\033[0m'
    _BLUE = '\033[94m'
    _CYAN = '\033[96m'
    _GREEN = '\033[92m'
    _ORANGE = '\033[93m'
    _RED = '\033[91m'
    _BOLD = '\033[1m'
    _UNDERLINE = '\033[4m'
    CELL_COLORS = {
        # Словарь с цветами для заливки ячеек в pdf-документах
        'red': (255, 64, 52),
        'gray': (211, 211, 211),
        'green': (79, 121, 66),
        'blue': (0, 0, 128),
        'yellow': (255, 255, 0),
        'purple': (128, 0, 128),
    }
    CHART_COLORS = {
        # Словарь цветов в hex и RGBA значениях
        'hex': ('#00BFFF', '#ADD8E6', '#6B8E23', '#2E8B57',
                '#00FA9A', '#00FF00', '	#ADFF2F', '#FA8072', '#FFB6C1',
                '#FF8C00', '#FFFF00'),
        'RGBA': ((0, 0.75, 1, 1), (0.68, 0.85, 0.9, 1), (0.42, 0.56, 0.14, 1), (0.18, 0.55, 0.34, 1),
                 (0, 0.98, 0.6, 1), (0, 1, 0, 1), (0.67, 1, 0.18, 1), (0.98, 0.5, 0.45, 1), (1, 0.71, 0.76, 1),
                 (1, 0.55, 0, 1), (1, 1, 0, 1))
    }

    def header(self, text_to_wrap: str) -> str:
        """
        Окрашивает текст в ярко-фиолетовый цвет
        :param text_to_wrap: текст для окрашивания
        :return: строка с ANSI-последовательностью
        """
        return self._HEADER + str(text_to_wrap) + self._END

    def bold(self, text_to_wrap: str) -> str:
        """
        Возвращает текст в полужирном начертании
        :param text_to_wrap: текст для утолщения
        :return: строка с ANSI-последовательностью
        """
        return self._BOLD + str(text_to_wrap) + self._END

    def underline(self, text_to_wrap: str) -> str:
        """
        Возвращает текст в подчеркнутом начертании
        :param text_to_wrap: текст для подчеркивания
        :return: строка с ANSI-последовательностью
        """
        return self._UNDERLINE + str(text_to_wrap) + self._END

    def blue(self, text_to_wrap: str) -> str:
        """
        Возвращает текст в синем цвете
        :param text_to_wrap: текст для окрашивания
        :return: строка с ANSI-последовательностью
        """
        return self._BLUE + str(text_to_wrap) + self._END

    def cyan(self, text_to_wrap: str) -> str:
        """
        Возвращает текст в светло-голубом цвете
        :param text_to_wrap: текст для окрашивания
        :return: строка с ANSI-последовательностью
        """
        return self._CYAN + str(text_to_wrap) + self._END

    def green(self, text_to_wrap: str) -> str:
        """
        Возвращает текст в зеленом цвете
        :param text_to_wrap: текст для окрашивания
        :return: строка с ANSI-последовательностью
        """
        return self._GREEN + str(text_to_wrap) + self._END

    def orange(self, text_to_wrap: str) -> str:
        """
        Возвращает текст в оранжевом цвете
        :param text_to_wrap: текст для окрашивания
        :return: строка с ANSI-последовательностью
        """
        return self._ORANGE + str(text_to_wrap) + self._END

    def red(self, text_to_wrap: str) -> str:
        """
        Возвращает текст в красном цвете
        :param text_to_wrap: текст для окрашивания
        :return: строка с ANSI-последовательностью
        """
        return self._RED + str(text_to_wrap) + self._END
