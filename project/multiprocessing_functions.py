import datetime


def mp_avg_flight_time(arr: str, dep: str) -> float:
    """
    Вспомогательный метод для анализа среднего времени полета
    :param arr: Время вылета борта
    :param dep: Время прилета борта
    :raises: TypeError, ValueError
    :return: Время полета в секундах
    """
    diff = datetime.datetime.strptime(arr, '%Y-%m-%d %H:%M:%S') \
        - datetime.datetime.strptime(dep, '%Y-%m-%d %H:%M:%S')
    diff = diff.total_seconds()
    if diff < 0:
        raise ValueError('В данном методе не предусмотрено вычитания поздней даты из более ранней')
    return diff


def mp_delay_time(dep_plan: str, dep_act: str) -> float:
    """
    Вспомогательный метод для расчета разницы в запланированном и реальном времени вылета борта
    :param dep_plan: Запланированное время вылета борта
    :param dep_act: Реальное время вылета борта
    :raises: TypeError
    :return: Разность между запланированным и реальным временем вылета в секундах
    """
    dep_plan, dep_act = datetime.datetime.strptime(dep_plan, '%Y-%m-%d %H:%M:%S'), \
        datetime.datetime.strptime(dep_act, '%Y-%m-%d %H:%M:%S')
    if dep_act >= dep_plan:
        diff = (dep_act - dep_plan).total_seconds()
    else:
        diff = - (dep_plan - dep_act).total_seconds()
    return diff
