"""Módulo de utilidad que genera la función calificadora.
"""

import typing
import pandas as pd
import datetime

from msopti.algorithm.interfaces import Scorefn
from msopti.params import Scores, Stop

def _limit_stops(stops: list[Stop], s: str|int,e: str|int) -> list[Stop]:
    """Delimita las paradas que se tomarán en cuenta para el algoritmo.

    No todas las paradas serán tomadas en cuenta, ya que se contempla
    el caso en que existan distintos puntos de salida. Por ejemplo, se
    tienen las paradas `[1, 2, 3, 4, 5, 6, 7, 8]` y se tiene 2 unidades,
    la unidad 1 sale desde la paradas 1, mientras que la unidad 2 sale
    desde la parada 5. Si se quiere optimizar la salida de la unidad 1,
    no se debería tomar en cuenta de la parada 5 en adelante, porque esa
    parada ya va a ser visitada por la unidad 2 cuado se optimice su salida.
    Del mismo modo, para la unidad 2, no se debería tomar en cuenta de la 
    parada 1 en adelante por la misma razón.

    Args:
        stops: Una lista de paradas (`Stop`).
        s: El punto de partida de la ruta para una unidad a (string o int).
        e: El punto de partida de la ruta para una unidad b (string o int).

    Returns:
        Una lista ordenada de las paradas que se considerarán para la 
        optimización. Volviendo al ejemplo de la unidad 1 y 2, para la unidad
        1, la función retorna `[1, 2, 3, 4]`, mientra que para la unidad 2,
        retorna `[5, 6, 7, 8]`
    """
    si = [i.id for i in stops].index(s)
    ei = [i.id for i in stops].index(e)

    if ei > si:
        return stops[si:ei]
    elif ei < si:
        arr = stops[si:]
        arr.extend(stops[ei:si])
        return arr
    else:
        return stops[si:]

# TODO: Mejorar esta api
def gererate_formula(
        forecast: pd.DataFrame,
        start_points: list[str|int],
        stops: list[Stop],
        scores: Scores,
        curr_date: datetime.datetime
    ) -> Scorefn:
    """Genera una fórmula para ser utilizada con los algoritmos.

    Se necesita tener previamente el dataset con los pronósticos
    debido a que la función simplemente hace una consulta y una
    sumatoria con el mismo. Realizar la lectura completa del
    dataset es una tarea que afectaría negativamente el rendimiento
    de la función. Razón por la cual también se recomienda
    proveer el dataset filtrado

    Args:
        forecast: pandas.DataFrame, Un dataset con `pandas.DatetimeIndex`,
            una columna `passengers` y una columna `stop_id`
        start_points: Una lista de ids de paradas (string o int) indicando los
            puntos en donde se comenzrán a despachar las unidades
        stops: Una lista ordenada de paradas (`Stop`) indicando
            todas las paradas en una ruta.
        scores: Un `Scores` con las penalizaciones asignadas
        curr_date: La fecha que se tomará como inicio, debe ser de tipo
            `datetime.datetime` con la hora en 00:00:00

    Returns:
        Un `Scorefn` adaptado para utilizarse con los algoritmos de la librería.

    Raise:
        ValueError: cuando el pandas.DataFrame no contiene las llaves
            `passengers` y `stop_id`, o no tiene `pandas.DatetimeIndex`
    """

    if not all(i in forecast.columns for i in ["passengers","stop_id"]):
        raise ValueError("No se encontró las columnas 'passengers' y 'stop_id'")

    if not isinstance(forecast.index, pd.DatetimeIndex):
        raise ValueError("No se tiene un `DatetimeIndex` como índice")

    scoped_stops = _limit_stops(stops,start_points[0],start_points[-1])

    a = scores.minute_price
    b = scores.cap_cost
    c = scores.low_demand_cost
    d = scores.zero_demand_cost
    cdate = pd.Timestamp(curr_date)

    def formula(
            start: datetime.datetime,
            t: datetime.timedelta,
            x: int
        ) -> float:

        # setup para p(t) y g(t)
        # si es el primer despacho, se lo tiene que manejar distinto
        # considerando que otros buses visitarán las paradas y no se
        # esperaría tanto tiempo. Por ejemplo, en este ejemplo se
        # revisa desde las 5:30 hasta x debido a que no hay otro bus,
        # pero si hubieramos despachado antes, no sería desde las 5:30
        # hasta x en ciertas paradas debido, a que posiblemente hasta
        # ese tiempo ya hayan sido visitadas
        st = start
        df = pd.DataFrame()
        for stop in scoped_stops:
            # Times (t = 5, t0 = 6:05):
            #   6:14 - 6:19 (parada 1: tp = 9)
            #   6:25 - 6:30 (parada 2: tp = 7)
            #   6:34 - 6:39 (parada 3: tp = 4)
            #   ...  - ...
            st = stop.last_visit or st
            st += (stop.time + stop.event_delay)
            end = st + t
            sf = forecast[forecast["stop_id"] == stop.id]

            if stop.last_visit is None:
                s = sf.between_time(start.time(),end.time())
            else:
                s = sf.between_time(st.time(),end.time())

            df = pd.concat([df,s])

        # p(t)
        pt = df["passengers"].sum()

        # q(t)
        g = df.groupby(typing.cast(pd.DatetimeIndex,df.index).floor("d")) # type: ignore pylint: disable=C0301
        df = typing.cast(pd.DataFrame,g.get_group(cdate))
        qt = df[df["passengers"] == df["passengers"].max()].iloc[-1].name - start # pylint: disable=C0301

        # d(t)
        dt = ((c * (1 / pt)) if pt != 0 else d)


        # fórmula temporal: f(t, x) = 1 * t + 10 * abs(x - p(t)) + d(t) = 180
        # result = (a * ( t.seconds // 60 )) + (b * abs( x - pt )) + dt
        # fórmula :D
        # f(t,x) = a * q(t) + b * abs(x - p(t)) + d(t)
        # p(t) == sumatoria de pasajeros en una parada (i) e tiempo (j) específico
        # q(t) == el tiempo que espera la parada con más pasajeros
        result = (a * ( qt.seconds // 60 )) + (b * abs( x - pt )) + dt

        # print(f"Params: a={a}, b={b}, c={c}, d={d}, t={t} p(t)={pt}, x={x}")
        # print(f"Params: t={t} ,a={a}, b={b}, c={c}, d={d}, t={t} p(t)={pt}, q(t)={qt.seconds // 60}, x={x}") # pylint: disable=C0301
        # print(f"Result: {result}")
        return result

    return typing.cast(Scorefn,formula)
