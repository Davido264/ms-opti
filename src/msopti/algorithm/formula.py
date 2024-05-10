"""Módulo de utilidad que genera la función calificadora.
"""
# TODO: Documentar todo esto en un documento aparte y comentar resumen de esto
# con el link a títulos en dicho documento

import typing
import math
import datetime
import pandas as pd

from msopti.algorithm.interfaces import Scorefn
from msopti.params.interfaces.stop_provider import IStopProvider
from msopti.params.interfaces.scores_provider import IScoreProvider

# TODO: buscar una mejor implementación para realizar catching
# Lo que busco es guardar la última operación realizada, dado a
# que se va a iterar por ella en múltiples ocaciones
CACHE: dict | None = None

pd.options.mode.copy_on_write = True

def _query_df(
        forecast: pd.DataFrame,
        scoped_stops: list[IStopProvider],
        start: datetime.datetime,
        t: datetime.timedelta
    ) -> tuple[int|float,int|float]:
    global CACHE
    # revisar si los resultados de la operación fueron calculados
    # antes
    if CACHE is not None:
        is_cached = CACHE.get("stops",None) == scoped_stops and \
            CACHE.get("start",None) == start and \
            CACHE.get("t",None) == t

        if is_cached:
            return (CACHE["pt"],CACHE["qt"])

    # setup para p(t) y q(t)
    # si es el primer despacho, se lo tiene que manejar distinto
    # considerando que otros buses visitarán las paradas y no se
    # esperaría tanto tiempo. Por ejemplo, se revisa desde las
    # 5:30 hasta x debido a que no hay otro bus, pero si hubieramos
    # despachado antes, no sería desde las 5:30 hasta x en ciertas
    # paradas debido, a que posiblemente hasta ese tiempo ya hayan
    # sido visitadas. Para ese caso, se registra que una parada fue
    # visitada en y, y se revisa desde y hasta x
    start_time = start + t
    df = pd.DataFrame()

    # se busca el tiempo registrado más cercano y se lo utiliza
    def diff(a,b):
        time_a = datetime.timedelta(hours=a.hour,minutes=a.minute)
        time_b = datetime.timedelta(hours=b.hour,minutes=b.minute)
        return abs(time_a - time_b)

    for stop in scoped_stops:
        # Times (t = 5, t0 = 6:05):
        #   6:14 - 6:19 (parada 1: tp = 9 minutos)
        #   6:25 - 6:30 (parada 2: tp = 7 minutos)
        #   6:34 - 6:39 (parada 3: tp = 4 minutos)
        #   ...  - ...

        stop_forecast = forecast[forecast["stop_id"] == stop.id]
        start_time += (stop.time + stop.event_delay)

        # Para cada tiempo establecido se va a obtener el valor registrado más
        # cercano, esto se lo realizará redondeando a las decenas de minutos y
        # comparando los valores intermedios en el rango establecido con el
        # tiempo que se maneja, en caso de encontrarse un valor ya registrado,
        # se pasará al siguiente mejor resultado. Si no se encuentra un
        # resultado satisfactorio en un rango de descena, se pasará al siguiente
        register = None

        while register is None:
            floor = datetime.time(
                hour=start_time.hour,
                minute=math.floor(start_time.minute / 10) * 10,
                second=start_time.second
            )

            min_ceil = math.ceil(start_time.minute / 10) * 10

            ceil = datetime.time(
                hour=start_time.hour if min_ceil != 60 else start_time.hour + 1,
                minute= min_ceil if min_ceil != 60 else 0,
                second=start_time.second
            )

            s = stop_forecast.between_time(floor,ceil)
            s = typing.cast(pd.DataFrame,s)

            date_index = typing.cast(pd.DatetimeIndex,s.index)
            s["time_diff"] = [ diff(i.time(),start_time) for i in date_index ]
            # s = s.loc[s["time_diff"].idxmin():] # type: ignore
            s.sort_values(by="time_diff", ascending=True,inplace=True)

            # s será el registro más aproxima
            for index,row in s.iterrows():
                if (
                    len(stop.visits) == 0 or
                    len(stop.visits) != 0 and stop.visits[0] != index
                ):
                    register = pd.DataFrame(data=[row],index=[index])
                    break

            start_time += datetime.timedelta(minutes=10)

        df = pd.concat([df,register])
        df = typing.cast(pd.DataFrame,df)


    CACHE = {}
    CACHE["stops"] = scoped_stops
    CACHE["start"] = start
    CACHE["t"] = t
    CACHE["pt"] = df["passengers"].sum()
    CACHE["qt"] = (df[df["passengers"] == df["passengers"].max()].iloc[-1].name - start ).seconds // 60 # pylint: disable=C0301

    return (CACHE["pt"],CACHE["qt"])



def _reorder_stop(stops: list[IStopProvider], s: str|int) -> list[IStopProvider]:
    """Reordena las paradas que se tomarán en cuenta para el algoritmo.

    Las paradas mantendrán su orden de planficiación, cambiará el punto de
    inicio que estas tengan. Esto debido a que se cuenta la posibilidad de
    que sea más efectivo comenzar la ruta desde otra parada. Por ejemplo,
    si la salida más óptima es la primera parada, en una ruta con las paradas
    `[ 0, 1, 2, 3, 4, 5 ]`, la lista obtenida por la función es la misma, por
    otro lado, si la salida más óptima es la tercera parada, el resultado de
    la función es `[3, 4, 5, 0, 1, 2]`.

    Args:
        stops: Una lista de paradas (`Stop`).
        s: El punto de partida de la ruta para una unidad a (string o int).

    Returns:
        Una lista ordenada de las paradas que se considerarán para la 
        optimización.
    """
    si = [i.id for i in stops].index(s)

    if si == 0:
        return stops[:]
    else:
        arr = stops[si:]
        arr.extend(stops[:si])
        return arr

# TODO: Mejorar esta api
def gererate_formula(
        forecast: pd.DataFrame,
        stops: list[IStopProvider],
        scores: IScoreProvider,
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
        stops: Una lista ordenada de paradas (`Stop`) indicando
            todas las paradas en una ruta.
        scores: Un `Scores` con las penalizaciones asignadas

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

    a = scores.minute_price
    b = scores.capacity_cost
    c = scores.low_demand_cost
    d = scores.zero_demand_cost

    def formula(
            start: datetime.datetime,
            sp: str|int,
            t: datetime.timedelta,
            x: int
        ) -> float:

        scoped_stops = _reorder_stop(stops,sp)

        # p(t) y q(t)
        pt,qt = _query_df(forecast,scoped_stops,start,t)

        # d(t)
        dt = (c * (1 / pt)) if pt != 0 else d

        # fórmula temporal: f(t, x) = 1 * t + 10 * abs(x - p(t)) + d(t) = 180
        # result = (a * ( t.seconds // 60 )) + (b * abs( x - pt )) + dt
        # fórmula :D
        # f(t,x) = a * q(t) + b * abs(x - p(t)) + d(t)
        # p(t) == sumatoria de pasajeros en una parada (i) y tiempo (j)
        # q(t) == el tiempo que espera la parada con más pasajeros
        result = (a * qt) + (b * abs( x - pt )) + dt

        # print(f"Params: a={a}, b={b}, c={c}, d={d}, t={t} p(t)={pt}, x={x}")
        # print("runin")
        # print(f"Params: t={t}, stop={sp} ,a={a}, b={b}, c={c}, d={d}, t={t} p(t)={pt}, q(t)={qt}, x={x}. Result: {result}") # pylint: disable=C0301
        return result

    return typing.cast(Scorefn,formula)
