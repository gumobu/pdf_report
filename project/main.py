# -*- coding: <utf-8> -*-
import fpdf
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import pandas as pd
import pandas.io.sql as psql
import numpy as np
from project.producers import aircraft_producers as air_prod
import datetime
import multiprocessing as mp
from project.multiprocessing_functions import mp_avg_flight_time, mp_delay_time
from project.colors_and_styles import Colors as Clr
from fpdf import FPDF
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os
import pdf_functions as pf


# Константы скрипта
CELL_HEIGHT_PDF = 24  # Высота ячейки таблицы в pdf-отчете
TEXT_HEIGHT_PDF = 32  # Высота ячейки с текстом в pdf-отчете


def planes_data(planes_dataframe: pd.DataFrame) -> None:
    """
    Анализ данных, связанных с бортами авиакомпании
    :param planes_dataframe: Pandas DataFrame с информацией о бортах
    :raises: TypeError
    :return: Ничего не возвращается (Неявный None)
    """
    if type(planes_dataframe) != pd.DataFrame:
        raise TypeError('Метод предназначен для обработки pandas.Dataframe')

    print(filler('='))
    title = 'ИСПОЛЬЗУЕМЫЙ ФЛОТ АВИАСУДОВ'
    print(Clr.bold(title))
    file = FPDF(unit='pt', format='A4')  # Все измерения и координаты в документе - в пикселях
    file.set_fill_color(*Clr.CELL_COLORS['red'])  # Настройка цвета заливки ячеек таблицы (красный)
    file.add_page()
    file.set_auto_page_break(False)
    file.add_font('times', '', 'project/static/tnr.ttf', uni=True)  # Normal Times New Roman font
    file.add_font('times b', '', 'project/static/tnrb.ttf', uni=True)  # Bold Times New Roman font

    PDFHelper.pdf_header(file, title, allign='C')
    planes_dataframe = planes_dataframe.drop(['range'], axis=1).assign(Economy=0, Comfort=0, Business=0)
    seats = pd.read_sql("SELECT * FROM seats", connection).drop(['seat_no'], axis=1)  # Перечень мест для каждого борта
    seats_data = seats.groupby('aircraft_code')['fare_conditions'].value_counts()
    for code in planes_dataframe['aircraft_code']:
        data = seats_data[code].reset_index(name='count')
        fares = data['fare_conditions'].to_list()
        for fare in fares:
            planes_dataframe.loc[planes_dataframe['aircraft_code'] == code, fare] = \
                data.loc[data['fare_conditions'] == fare, 'count'].item()
    # Список кортежей вида (название судна (str), мест в экономе (int), мест в комфорте (int), мест в бизнесе (int))
    res = [(x['en'], eco, com, bus) for x, eco, com, bus in
           zip(planes_dataframe['model'],
               planes_dataframe['Economy'],
               planes_dataframe['Comfort'],
               planes_dataframe['Business'])
           ]
    # Список уникальных авиасудов. Подразумевается, что у всех судов одной модели одинаковые салоны
    boards = sorted(set(res), key=lambda x: x[0])
    # Получение списка производителей
    prods = [
        x[0].split()[0] for x in boards
    ]
    # Словарь вида производитель: [количество судов производителя (int)]
    aircraft_by_producers = {x: [prods.count(x)] for x in air_prod if prods.count(x) > 0}
    for producer in aircraft_by_producers.keys():
        for board in boards:
            if board[0].startswith(producer):
                aircraft_by_producers[producer].append(board)
    col_names = ('№', 'Судно', 'Эконом', 'Комфорт', 'Бизнес', 'Всего')  # Названия столбцов таблиц
    total_value_width = 60  # Разница в ширине между столбцом с названием судна и остальными
    for name in col_names:  # Вычисление ширины таблицы
        total_value_width += file.get_string_width(name) + 20
    left_margin = round((file.w - total_value_width) / 2)  # Вычисление левого отступа документа для таблицы
    cols_width = []  # Список для хранения ширин столбцов
    seats_total = [0, 0, 0]  # Список для хранения общего количества мест в судах авиакомпании
    # Словарь для хранения информации о общей вместимости бортов производителей
    seats_by_producer = {x: 0 for x in aircraft_by_producers.keys()}
    for (producer, amount) in aircraft_by_producers.items():
        seats_in_plane = (0, 0, 0)  # Общее количество мест в каждом из классов для производителя
        print(f'  {producer}: {amount[0]} ед.')  # Печать в консоль производителя и количества самолетов его сборки

        file.c_margin = 0  # Настройка отступа в ячейке для выравнивания текста
        file.set_left_margin(left_margin)  # Установка левого отступа для создания ровных таблиц

        # Суммарная высота таблицы для производителя с текстовым заголовком
        total_producer_height = TEXT_HEIGHT_PDF + CELL_HEIGHT_PDF * (amount[0] + 1)
        table_rows = amount[0] + 1  # Количество строк таблицы, не считая заголовков столбцов
        # Заполнение таблицы
        if PDFHelper.fit(file, total_producer_height, auto_add=False):
            # Если таблица и заголовок полностью помещаются на текущей странице
            # Добавление в документ заголовка с указанием производителя
            PDFHelper.pdf_header(file, producer)
            # Добавление ячеек с названиями столбцов
            PDFHelper.add_cols_names(file, col_names, cols_width, clr=Clr)
            # Проход по всем бортам производителя
            for i in range(1, len(amount) + 1):
                if i != len(amount):  # Заполнение всех строк таблицы, кроме подытога

                    print(f'\t{Clr.bold(str(i))} {amount[i][0]}\n\t  Места:')

                    (eco, com, bus) = amount[i][1:]  # Места в экономе, комфорте и бизнес-классе
                    seats_in_plane = (seats_in_plane[0] + eco, seats_in_plane[1] + com, seats_in_plane[2] + bus)
                    file.set_font('times', size=18)  # Установка обычного шрифта TNR для заполнения строк таблицы
                    # Ячейка с порядковым индексом самолета по производителю
                    file.cell(w=cols_width[0], h=CELL_HEIGHT_PDF, txt=str(i), border=1, align='C')
                    file.c_margin = 10  # Настройка внутреннего отступа в ячейке для выравнивания текста
                    data = amount[i]
                    # Заполнение строк таблицы
                    for j in range(len(data) + 1):
                        file.set_fill_color(*Clr.CELL_COLORS['red'])  # Настройка заливки нулевых ячеек красным
                        if j == 0:  # Логика для первой после индекса ячейки
                            file.cell(w=cols_width[j + 1], h=CELL_HEIGHT_PDF, txt=' '.join(data[j].split(' ')[1:]),
                                      border=1, align='L', fill=data[j] == 0)
                        else:
                            if j == len(data):  # Отдельная логика для последней ячейки строки
                                file.set_fill_color(*Clr.CELL_COLORS['gray'])
                                text = str(sum(data[1:]))
                                is_fill = True
                            else:
                                text = str(data[j])
                                is_fill = data[j] == 0
                            file.cell(w=cols_width[j + 1], h=CELL_HEIGHT_PDF, txt=text,
                                      border=1, align='R', fill=is_fill,
                                      ln=1 if j == len(data) else 0)
                    # Печать данных о количестве мест в самолете в консоль
                    print_seats(eco, com, bus)

                else:  # Заполнение строки таблицы с подытогом
                    file.set_fill_color(*Clr.CELL_COLORS['gray'])
                    for j in range(1, len(col_names)):
                        if j != len(col_names) - 1:  # Логика для всех ячеек, кроме последней в строке
                            if j == 1:  # Логика для первой ячейки (два столбца объединены)
                                file.cell(w=sum(cols_width[j - 1:j + 1]), h=CELL_HEIGHT_PDF, txt='Всего',
                                          border=1, align='L', fill=True)
                            else:
                                file.cell(w=cols_width[j], h=CELL_HEIGHT_PDF, txt=str(seats_in_plane[j - 2]),
                                          border=1, align='R', fill=True)
                        else:  # Перенос каретки после последней ячейки в таблице
                            total = str(sum(seats_in_plane))
                            file.cell(w=cols_width[j], h=CELL_HEIGHT_PDF, txt=total, border=1, align='R', ln=1,
                                      fill=True)
                    file.set_fill_color(*Clr.CELL_COLORS['red'])
        else:
            # Если таблица не помещается на странице полностью
            # Минимальная таблица - заголовок, названия столбцов и одна строка с данными
            pdf_index = 0  # Индекс отображаемой строки таблицы
            minimal_table_height = TEXT_HEIGHT_PDF + CELL_HEIGHT_PDF * 2
            PDFHelper.fit(file, minimal_table_height, auto_add=True)
            PDFHelper.pdf_header(file, producer)  # Добавление в документ заголовка с указанием производителя
            PDFHelper.add_cols_names(file, col_names, cols_width, clr=Clr)  # Добаление строки с названиями столбцов
            while pdf_index != table_rows - 1:  # Пока не все строки таблицы добавлены в документ
                if PDFHelper.fit(file, CELL_HEIGHT_PDF, auto_add=False):
                    # Если есть место на еще одну строку таблицы
                    # Если не строка с подытогом
                    pdf_index += 1
                    data = amount[pdf_index]

                    print(f'\t{Clr.bold(str(pdf_index))} {data[0]}\n\t  Места:')

                    (eco, com, bus) = data[1:]  # Места в экономе, комфорте и бизнес-классе
                    seats_in_plane = (seats_in_plane[0] + eco, seats_in_plane[1] + com, seats_in_plane[2] + bus)
                    for i in range(-1, len(data) + 1):
                        # Проход по всем ячейкам строки
                        file.set_fill_color(*Clr.CELL_COLORS['red'])  # Настройка заливки нулевых ячеек красным
                        file.set_font('times', size=18)
                        if i == -1:  # Логика для ячейки индекса
                            file.c_margin = 0
                            file.cell(w=cols_width[i + 1], h=CELL_HEIGHT_PDF, txt=str(pdf_index),
                                      border=1, align='C')
                            file.c_margin = 10
                        elif i == 0:  # Логика для первой после индекса ячейки
                            file.cell(w=cols_width[i + 1], h=CELL_HEIGHT_PDF, txt=' '.join(data[i].split(' ')[1:]),
                                      border=1, align='L', fill=data[i] == 0)
                        else:
                            if i == len(data):  # Отдельная логика для последней ячейки строки
                                file.set_fill_color(*Clr.CELL_COLORS['gray'])
                                text = str(sum(data[1:]))
                                is_fill = True
                            else:
                                text = str(data[i])
                                is_fill = data[i] == 0
                            file.cell(w=cols_width[i + 1], h=CELL_HEIGHT_PDF, txt=text,
                                      border=1, align='R', fill=is_fill,
                                      ln=1 if i == len(data) else 0)
                    # Печать данных о количестве мест в самолете в консоль
                    print_seats(eco, com, bus)

                else:  # Если не хватает места на таблицу на созданной странице
                    PDFHelper.fit(file, CELL_HEIGHT_PDF, auto_add=True)
                    # Добавление названий столбцов первой строкой таблицы
                    PDFHelper.add_cols_names(file, col_names, cols_width, clr=Clr)
            PDFHelper.fit(file, CELL_HEIGHT_PDF, auto_add=True)
            file.set_fill_color(*Clr.CELL_COLORS['gray'])
            for j in range(1, len(col_names)):
                if j != len(col_names) - 1:  # Логика для всех ячеек, кроме последней в строке
                    if j == 1:  # Логика для первой ячейки (два столбца объединены)
                        file.cell(w=sum(cols_width[j - 1:j + 1]), h=CELL_HEIGHT_PDF, txt='Всего',
                                  border=1, align='L', fill=True)
                    else:
                        file.cell(w=cols_width[j], h=CELL_HEIGHT_PDF, txt=str(seats_in_plane[j - 2]),
                                  border=1, align='R', fill=True)
                else:  # Перенос каретки после последней ячейки в таблице
                    total = str(sum(seats_in_plane))
                    file.cell(w=cols_width[j], h=CELL_HEIGHT_PDF, txt=total, border=1, align='R', ln=1,
                              fill=True)
            file.set_fill_color(*Clr.CELL_COLORS['red'])

        # Подсчет общего количества мест
        for k in range(len(seats_total)):
            seats_total[k] += seats_in_plane[k]
        # Сохранение количества мест для производителя
        seats_by_producer[producer] = sum(seats_in_plane)
    file.cell(-left_margin)  # Сброс отступа. Необходим для корректного расположения заголовка
    file.set_font('times b', size=18)  # Установка жирного шрифта для заголовка и названий столбцов таблицы
    file.set_fill_color(*Clr.CELL_COLORS['gray'])
    file.set_left_margin(left_margin)
    PDFHelper.fit(file, TEXT_HEIGHT_PDF + CELL_HEIGHT_PDF * 2, auto_add=True)
    PDFHelper.pdf_header(file, 'Итог')  # Добавление в документ заголовка итоговой таблицы
    # Заполнение итоговой таблицы
    file.c_margin = 0
    for i in range(2):
        for j in range(1, len(col_names)):
            # Заполнение заголовков столбцов итоговой таблицы
            if i == 0:
                if j == 1:
                    file.cell(w=sum(cols_width[0:2]), h=CELL_HEIGHT_PDF, txt='', border=0, fill=False)
                else:
                    file.cell(w=cols_width[j], h=CELL_HEIGHT_PDF, txt=col_names[j], border=1, align='C',
                              ln=j == len(col_names) - 1, fill=j == len(col_names) - 1)
            else:  # Заполнение основной части таблицы
                file.set_font('times', size=18)
                file.c_margin = 10
                if j == 1:
                    file.cell(w=sum(cols_width[0:2]), h=CELL_HEIGHT_PDF, txt='Всего мест', border=1, fill=True)
                elif j < len(col_names) - 1:
                    file.cell(w=cols_width[j], h=CELL_HEIGHT_PDF,
                              txt='{:,}'.format(seats_total[j - 2]).replace(',', ' '), border=1, align='R', fill=True)
                else:
                    file.cell(w=cols_width[j], h=CELL_HEIGHT_PDF, txt='{:,}'.format(sum(seats_total)).replace(',', ' '),
                              border=1, ln=1, align='R', fill=True)
    file.c_margin = 0

    # Сортировка словаря по уменьшению количества самолетов в использовании
    aircraft_by_producers = dict(sorted(aircraft_by_producers.items(), key=lambda val: val[1][0], reverse=True))
    producers_bar_plot(aircraft_by_producers, file)  # Добавление столбчатой диаграммы к отчету

    values = {x: y for (x, y) in seats_by_producer.items()}
    pie_plot(list(values.values()), list(values.keys()), 'seats_by_prod', file, additional_data=seats_by_producer)

    # Сохранение pdf файла с отчетом
    file.output(f'project/output/planes_data_'
                f'{datetime.datetime.now().strftime("%d_%b_%Y_%H_%M_%S")}.pdf')
    file.close()
    print(filler('='))  # Отделение данных в консоли


# TODO Добавить генерацию красивых pdf-документов с отчетностью
def flights_data(flights_dataframe: pd.DataFrame) -> None:
    """
    Анализ данных, связанных с рейсами бортов авиакомпании
    :param flights_dataframe: Pandas Dataframe с информацией о полетах
    :raises: TypeError
    :return: Ничего не возвращается (Неявный None)
    """
    if type(flights_dataframe) != pd.DataFrame:
        raise TypeError('Метод предназначен для обработки pandas.Dataframe')
    print(Clr.bold('ПОЛЕТЫ'))
    print(f'Среднее время полета на основе {Clr.bold(str(len(flights_dataframe)))} записей:')

    # Получение полных перечней времени взлета и посадки бортов и отсечение нулевого смещения по часовому поясу
    departure_actual = [str(x)[:-6] for x in flights_dataframe[['actual_departure']]['actual_departure']]
    arrival_actual = [str(x)[:-6] for x in flights_dataframe[['actual_arrival']]['actual_arrival']]
    departure_planned = [str(x)[:-6] for x in flights_dataframe[['scheduled_departure']]['scheduled_departure']]

    with mp.Pool(4) as pool:
        flight_time = pool.starmap(mp_avg_flight_time, zip(arrival_actual, departure_actual))
        avg_flight_time = datetime.timedelta(seconds=np.average(flight_time))

        delay_time = pool.starmap(mp_delay_time, zip(departure_planned, departure_actual))
        in_time = 0  # Счетчик своевременных вылетов
        delayed = []  # Список для хранения времени задержки рейсов с задержанным вылетом
        too_soon = []  # Список для хранения времени преждевременного вылета рейсов с преждевременным вылетом
        for time in delay_time:
            if time == 0:
                in_time += 1
            elif time > 0:
                delayed.append(time)
            else:
                too_soon.append(time)

    print(f'{Clr.bold(str(avg_flight_time).split(".")[0])}')
    print(filler('-'))

    avg_delay_time = str(datetime.timedelta(seconds=np.average(delayed))).split('.')[0]
    flights_dataframe['delay'] = delay_time
    res = f'Из {Clr.bold(str(len(departure_actual)))} совершенных рейсов\n' \
          f'\tВовремя вылетели: {in_time}'
    if in_time > 0:
        in_time_percent = "{:.3%}".format(in_time / len(departure_actual))
        res += f' ({in_time_percent})'
    res += f'\n\tОпоздали с вылетом: {len(delayed)}'
    if len(delayed) > 0:
        delayed_percent = "{:.3%}".format(len(delayed) / len(departure_actual))
        res += f' ({delayed_percent}).\n' \
               f'\t  При этом среднее время задержки равно: {avg_delay_time}'
    res += f'\n\tВылетели с опережением графика: {len(too_soon)}'
    if len(too_soon) > 0:
        too_soon_percent = "{:.3%}".format(len(too_soon) / len(departure_actual))
        res += f' ({too_soon_percent}.'

    print(res)
    print(filler('-'))

    df_with_seconds = flights_dataframe.drop(
        ['scheduled_departure', 'scheduled_arrival', 'actual_departure', 'actual_arrival',
         'flight_id', 'aircraft_code', 'status'], axis=1)

    if in_time > 0:
        # Датафрейм со своевременными рейсами
        df_in_time = df_with_seconds.loc[df_with_seconds['delay'] == 0].drop(['delay'], axis=1)
        df = df_in_time.flight_no.value_counts().to_frame()
        maxes = df.index[df['flight_no'] == df['flight_no'].max()].tolist()
        df_in_time = df_in_time.drop_duplicates(keep='first')
        if len(maxes) > 2:
            data = df_in_time.loc[df_in_time['flight_no'].isin(maxes)]
            departures = data['departure_airport'].tolist()
            arrivals = data['arrival_airport'].tolist()
            to_print = [board + ' из ' + dep + ' в ' + arr for board, dep, arr in zip(maxes, departures, arrivals)]
            print('Наиболее часто вылетающие вовремя рейсы:')
            for element in to_print:
                print(f'\t {element}')
        else:
            data = df_in_time.loc[df_in_time['flight_no'] == maxes[0]]
            dep = data['departure_airport'].item()
            arr = data['arrival_airport'].item()
            print(f'Наиболее часто вылетающий вовремя рейс:\n\t{maxes[0]} из {dep} в {arr}')

    if len(delayed) > 0:
        # Датафрейм с рейсами, вылетевшими с опозданием
        df_delayed = df_with_seconds.loc[df_with_seconds['delay'] > 0].drop(['delay'], axis=1)
        df = df_delayed.flight_no.value_counts().to_frame()
        maxes = df.index[df['flight_no'] == df['flight_no'].max()].tolist()
        df_delayed = df_delayed.drop_duplicates(keep='first')
        if len(maxes) > 2:
            data = df_delayed.loc[df_delayed['flight_no'].isin(maxes)]
            boards = data['flight_no'].tolist()
            departures = data['departure_airport'].tolist()
            arrivals = data['arrival_airport'].tolist()
            to_print = [board + ' из ' + dep + ' в ' + arr for board, dep, arr in zip(boards, departures, arrivals)]
            print('Наиболее часто вылетающие с задержкой рейсы:')
            for element in to_print:
                print(f'\t {element}')
        else:
            data = df_delayed.loc[df_delayed['flight_no'] == maxes[0]]
            dep = data['departure_airport'].item()
            arr = data['arrival_airport'].item()
            print(f'\tНаиболее часто вылетающий с задержкой рейс:\n\t{maxes[0]} из {dep} в {arr}')

    if len(too_soon) > 0:
        # Датафрейм с рейсами, вылетевшими раньше плана
        df_soon = df_with_seconds.loc[df_with_seconds['delay'] < 0].drop(['delay'], axis=1)
        df = df_soon.flight_no.value_counts().to_frame()
        maxes = df.index[df['flight_no'] == df['flight_no'].max()].tolist()
        df_soon = df_soon.drop_duplicates(keep='first')
        if len(maxes) > 2:
            data = df_soon.loc[df_soon['flight_no'].isin(maxes)]
            boards = data['flight_no'].tolist()
            departures = data['departure_airport'].tolist()
            arrivals = data['arrival_airport'].tolist()
            to_print = [board + ' из ' + dep + ' в ' + arr for board, dep, arr in zip(boards, departures, arrivals)]
            print('Наиболее часто вылетающие с задержкой рейсы:')
            for element in to_print:
                print(f'\t {element}')
        else:
            data = df_soon.loc[df_soon['flight_no'] == maxes[0]]
            dep = data['departure_airport'].item()
            arr = data['arrival_airport'].item()
            print(f'\tНаиболее часто вылетающий с задержкой рейс:\n\t{maxes[0]} из {dep} в {arr}')

    print(filler('='))


def tickets_data(tickets_dataframe: pd.DataFrame) -> None:
    """
    Анализ данных, связанных с билетами
    :param tickets_dataframe: Pandas Dataframe с информацией о билетах
    :raises: TypeError
    :return: Ничего не возвращается (Неявный None)
    """
    if type(tickets_dataframe) != pd.DataFrame:
        raise TypeError('Метод предназначен для обработки pandas.Dataframe')

    print(f'{Clr.bold("БИЛЕТЫ")}')

    economy_tickets = tickets_dataframe.loc[tickets_dataframe['type'] == 'Economy']
    economy_tickets_amount = len(economy_tickets)
    avg_price = economy_tickets['price'].sum() / economy_tickets_amount

    print(f'Средняя цена билета:\n'
          f'\tВ эконом-класс: {"{:.2f}".format(avg_price)}')

    comfort_tickets = tickets_dataframe.loc[tickets_dataframe['type'] == 'Comfort']
    comfort_tickets_amount = len(comfort_tickets)
    avg_price = comfort_tickets['price'].sum() / comfort_tickets_amount

    print(f'\tВ комфорт-класс: {"{:.2f}".format(avg_price)}')

    business_tickets = tickets_dataframe.loc[tickets_dataframe['type'] == 'Business']
    business_tickets_amount = len(business_tickets)
    avg_price = business_tickets['price'].sum() / business_tickets_amount

    print(f'\tВ бизнес-класс: {"{:.2f}".format(avg_price)}')
    print(filler('-'))

    total = economy_tickets_amount + business_tickets_amount + comfort_tickets_amount
    economy_percent = economy_tickets_amount / total
    comfort_percent = comfort_tickets_amount / total
    business_percent = business_tickets_amount / total

    print(f'Из всех билетов куплено:\n'
          f'\tВ эконом-класс: {economy_tickets_amount} ({"{:.3%}".format(economy_percent)})\n'
          f'\tВ комфорт-класс: {comfort_tickets_amount} ({"{:.3%}".format(comfort_percent)})\n'
          f'\tВ бизнес-класс: {business_tickets_amount} ({"{:.3%}".format(business_percent)})')

    print(filler('='))


def filler(symbol: str):
    """
    Функция для графического отделения данных в консольном отображении.
    Знак '=' отделяется строчными отступами сверху и снизу
    :param symbol: Символ для повторения в консоли
    :raises: TypeError
    :return: Строка - заполнитель
    """
    # Разделитель между основными разделами
    if type(symbol) != str:
        raise TypeError('Метод принимает объект str в качестве аргумента')
    if symbol == '=':
        return f'\n{Clr.bold(symbol * 50)}\n'
    # Разделитель подразделов
    else:
        return symbol * 50


def print_seats(eco_seats: int, com_seats: int, bus_seats: int) -> None:
    """
    Функция для печати количества мест разных классов в самолете
    :param eco_seats: число мест в эконом-классе
    :param com_seats: число мест в комфорт-классе
    :param bus_seats: число мест в бизнес-классе
    :return: None
    :raises: TypeError
    """
    # Проверка типов аргументов
    seats = (eco_seats, com_seats, bus_seats)
    seats_names = ('eco_seats', 'com_seats', 'bus_seats')
    for i in range(len(seats)):
        if type(seats[i]) != int:
            raise TypeError(f'Метод print_seats()\n'
                            f'{seats_names[i]} - ожидалось int, получено {type(seats[i])}.')
    if eco_seats > 0:
        print(f'\t\tЭконом-класс: {eco_seats}')
    if com_seats > 0:
        print(f'\t\tКомфорт-класс: {com_seats}')
    if bus_seats > 0:
        print(f'\t\tБизнес-класс: {bus_seats}')


def producers_bar_plot(producers_data: dict, pdf: fpdf.FPDF) -> None:
    """
    Функция для создания столбчатой диаграммы количества самолетов по производителям
    :param producers_data: словарь вида производитель: [количество самолетов, (название, места в экономе,
    места в комфорте, места в бизнесе), ...]
    :param pdf: объект fpdf.FPDF (документ отчета) для добавления диаграммы
    :return: None
    :raises: TypeError
    """
    # Проверка типов аргументов
    if type(producers_data) != dict:
        raise TypeError(f'Метод producers_bar_plot()\n'
                        f'producer_data - ожидалось dict, получено {type(producers_data)}')
    if type(pdf) != fpdf.FPDF:
        raise TypeError(f'Метод producers_bar_plot()\n'
                        f'pdf - ожидалось fpdf.FPDF, получено {type(producers_data)}')
    fig, ax = plt.subplots()
    plt.xticks(rotation=45)
    x, y = producers_data.keys(), [i[0] for i in producers_data.values()]
    barlist = ax.bar(x, y, width=5 / len(producers_data) - 0.1)
    for i in range(len(barlist)):
        barlist[i].set_color(Clr.CHART_COLORS['RGBA'][i])
    ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
    fig.set_figwidth(5)
    fig.set_figheight(2.5)
    fig.tight_layout()
    directory = 'project/output/producers_plot.jpg'
    fig.savefig(directory, dpi=1200)

    # Добавление графика в отчет
    page_space_left = PDFHelper.space_left(pdf)
    if page_space_left - fig.get_figheight() * 100 - TEXT_HEIGHT_PDF <= 0:
        pdf.add_page()
    PDFHelper.pdf_header(pdf, 'Количество самолетов по производителям')
    pdf.image(directory, w=pdf.w - pdf.l_margin - pdf.r_margin, h=fig.get_figheight() * 100)
    fig.clf()
    # Удаление созданного изображения из папки
    if os.path.isfile(directory):
        os.remove(directory)


def pie_plot(vals: list, labels:list, name:str, pdf: fpdf.FPDF, additional_data: dict = None) -> None:
    """
    Функция для сохранения и добавления в отчет круговой диаграммы
    :param vals: список значений
    :param labels: список категорий
    :param name: имя файла для сохранения
    :param pdf: объект fpdf.FPDF (документ отчета) для добавления диаграммы
    :param additional_data: дополнительные данные
    :return: None
    :raises: TypeError
    """
    # Проверка типов аргументов
    if type(vals) != list:
        raise TypeError(f'Метод pie_plot()\n'
                        f'vals - ожидалось lsit, получено {type(vals)}')
    if type(labels) != list:
        raise TypeError(f'Метод pie_plot()\n'
                        f'labels - ожидалось list, получено {type(labels)}')
    if type(name) != str:
        raise TypeError(f'Метод pie_plot()\n'
                        f'name - ожидалось str, получено {type(name)}')
    if additional_data and type(additional_data) != dict:
        raise TypeError(f'Метод pie_plot()\n'
                        f'additional_data - ожидалось dict, получено {type(additional_data)}')
    if len(vals) != len(labels):
        raise ValueError(f'Метод pie_plot()\n'
                         f'Размеры vals и labels не совпадают')

    fig, ax = plt.subplots()
    patches, texts = ax.pie(vals, labels=labels, colors=Clr.CHART_COLORS['hex'])
    for element in texts:
        element.set_fontsize(10)
    fig.set_figwidth(5)
    fig.set_figheight(2.5)
    if additional_data:
        additional_data = dict(sorted(additional_data.items(), key=lambda item: item[1], reverse=True))
        total_boards = sum(x[1] for x in additional_data.items())
        percents = ('{:.3%}'.format(x[1] / total_boards) for x in additional_data.items())
        labels = [f'{x[0]}: {x[1]} ({z})' for (x, z) in zip(additional_data.items(), percents)]
    plt.legend(patches, labels, loc='upper left', bbox_to_anchor=(1, 1))
    plt.tight_layout()
    directory = 'project/output/' + str(name) + '_pie_plot.jpg'
    fig.savefig(directory, dpi=1200, bbox_inches='tight')

    # Добавление графика в отчет
    page_space_left = PDFHelper.space_left(pdf)
    if page_space_left - fig.get_figheight() * 100 - TEXT_HEIGHT_PDF <= 0:
        pdf.add_page()
    PDFHelper.pdf_header(pdf, 'Процентное содержание мест по производителям судов')
    pdf.image(directory, w=pdf.w - pdf.l_margin - pdf.r_margin, h=fig.get_figheight() * 100)
    fig.clf()
    # Удаление созданного изображения из папки
    if os.path.isfile(directory):
        os.remove(directory)


if __name__ == '__main__':
    start_time = datetime.datetime.now()  # Начальная временная метка для отслеживания времени выполнения скрипта
    pd.set_option('display.max_columns', 15)
    mp.freeze_support()
    Clr = Clr()
    PDFHelper = pf.PDFHelper()
    try:
        connection = psycopg2.connect(
            host='localhost',
            port='5432',
            database='demo',
            user='superUser',
            password='superUserPassword'
        )
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()

        # Выгрузка данных
        dataframe = psql.read_sql('SELECT * FROM aircrafts_data', connection)
        # Анализ данных по бортам
        planes_data(dataframe)
        # Анализ данных по полетам
        dataframe = psql.read_sql("SELECT * FROM flights WHERE status='Arrived'", connection)
        flights_data(dataframe)
        # Анализ данных по билетам
        dataframe = psql.read_sql("SELECT fare_conditions as type, amount as price FROM ticket_flights", connection)
        tickets_data(dataframe)

    except (Exception, Error) as error:
        print('Ошибка при выполнении скрипта:\n\t', error)

    finally:
        if connection:
            cursor.close()
            connection.close()
            print('Подключение к базе данных закрыто')
        print('Процесс выполнен за', datetime.datetime.now() - start_time)
