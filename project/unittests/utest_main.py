from unittest import TestCase
from project.multiprocessing_functions import mp_avg_flight_time, mp_delay_time
from project.main import filler, planes_data, flights_data, tickets_data
import pandas as pd


class TestMpAvgFlightTime(TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_first_arg_not_a_str(self) -> None:
        self.assertRaises(TypeError, mp_avg_flight_time, (12, 'str'))

    def test_second_arg_not_a_string(self) -> None:
        self.assertRaises(TypeError, mp_avg_flight_time, ('12', 12))

    def test_first_arg_is_in_incorrect_format(self) -> None:
        self.assertRaises(TypeError, mp_avg_flight_time, ('12-1333-313', '2012-03-05 10:12:31'))

    def test_second_arg_is_in_incorrect_format(self) -> None:
        self.assertRaises(TypeError, mp_avg_flight_time, ('2012-03-05 10:12:31', '2012-03-05 10:12:91'))

    def test_everything_is_correct(self) -> None:
        date1 = '2020-06-13 20:06:13'
        date2 = '2019-05-12 19:05:12'
        self.assertEqual(type(mp_avg_flight_time(date1, date2)), float)

    def first_arg_is_bigger_than_second(self) -> None:
        date1 = '2019-05-12 19:05:12'
        date2 = '2020-06-13 20:06:13'
        self.assertRaises(ValueError, mp_avg_flight_time, (date1, date2))


class TestMpDelayTime(TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_first_arg_not_a_str(self) -> None:
        self.assertRaises(TypeError, mp_delay_time, (12, 'str'))

    def test_second_arg_not_a_string(self) -> None:
        self.assertRaises(TypeError, mp_delay_time, ('12', 12))

    def test_first_arg_is_in_incorrect_format(self) -> None:
        self.assertRaises(TypeError, mp_delay_time, ('12-1333-313', '2012-03-05 10:12:31'))

    def test_second_arg_is_in_incorrect_format(self) -> None:
        self.assertRaises(TypeError, mp_delay_time, ('2012-03-05 10:12:31', '2012-03-05 10:12:91'))

    def test_everything_is_correct(self) -> None:
        date1 = '2020-06-13 20:06:13'
        date2 = '2019-05-12 19:05:12'
        self.assertEqual(type(mp_delay_time(date1, date2)), float)


class TestFiller(TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_main_delimiter_is_correct(self) -> None:
        res = f'\n' \
              f'{"=" * 50}' \
              f'\n'
        self.assertEqual(filler('='), res)

    def test_usual_delimiter_is_correct(self) -> None:
        res_dict = {
            '-': '-' * 50,
            '/': '/' * 50,
            '#': '#' * 50
        }
        for key in res_dict.keys():
            self.assertEqual(filler(key), res_dict[key])

    def test_arg_class_is_incorrect(self) -> None:
        self.assertRaises(TypeError, filler, 2)
        self.assertRaises(TypeError, filler, ('2', '4'))


class TestDataAnalysisMethods(TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_correct_behaviour(self):
        test_planes = pd.DataFrame(
            [
                [771, {'en': 'Boeing 777-300', 'ru': 'Боинг 777-300'}, 100],
                [763, {'en': 'Boeing 767-300', 'ru': 'Боинг 767-300'}, 7900],
                [733, {'en': 'Boeing 737-300', 'ru': 'Боинг 737-300'}, 4200]
            ],
            columns=['aircraft_code', 'model', 'range']
        )
        test_tickets = pd.DataFrame(
            [
                ['Business', 99800.0],
                ['Business', 99800.0],
                ['Economy', 3300.0]
            ],
            columns=['type', 'price']
        )
        # TODO: Добавить тестирование метода flights_data
        self.assertEqual(planes_data(test_planes), None)
        self.assertEqual(tickets_data(test_tickets), None)

    def test_incorrect_behaviour(self):
        self.assertRaises(TypeError, planes_data, 2)
        self.assertRaises(TypeError, planes_data, 'dataframe')
        self.assertRaises(TypeError, planes_data, lambda x: x*2)

        self.assertRaises(TypeError, flights_data, 99)
        self.assertRaises(TypeError, flights_data, 'another dataframe')
        self.assertRaises(TypeError, flights_data, lambda y: y + 1)

        self.assertRaises(TypeError, tickets_data, 10001)
        self.assertRaises(TypeError, tickets_data, 'some string')
        self.assertRaises(TypeError, tickets_data, lambda x: str(x))


if __name__ == '__main__':
    TestFiller()
    TestMpDelayTime()
    TestMpAvgFlightTime()
    TestDataAnalysisMethods()

