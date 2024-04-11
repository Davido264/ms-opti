"""Módulo de utilidad que genera la función calificadora.
"""
# TODO: Documentar todo esto en un documento aparte y comentar resumen de esto
# con el link a títulos en dicho documento

from functools import reduce
import typing
import math
import datetime
import pandas as pd
import datetime

from msopti.algorithm.interfaces import Scorefn
from msopti.params import Scores, Stop

# TODO: buscar una mejor implementación para realizar catching
# Lo que busco es guardar la última operación realizada, dado a
# que se va a iterar por ella en múltiples ocaciones
CACHE: dict | None = None

def _query_df(
        forecast: pd.DataFrame,
        scoped_stops: list[Stop],
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
    st = start
    df = pd.DataFrame()
    already_done = 0
    for stop in scoped_stops:
        # Times (t = 5, t0 = 6:05):
        #   6:14 - 6:19 (parada 1: tp = 9 minutos)
        #   6:25 - 6:30 (parada 2: tp = 7 minutos)
        #   6:34 - 6:39 (parada 3: tp = 4 minutos)
        #   ...  - ...

        sf = forecast[forecast["stop_id"] == stop.id]
        st += (stop.time + stop.event_delay)
        end = st + t

        # Para cada tiempo establecido (inicio y fin) se va a obtener los
        # valores más cercanos a los registrados (asumiendo que todos los 
        # registros contienen tiempos cuyos minutos son múltiplos de 5), y se
        # hace una consulta a los registros entre los tiempos obtenidos. Para
        # luego iterar por este registro resultante, y obtener el valor más
        # cercano antes y después del tiempo dado. Una vez teniendo eso, se
        # obtiene la diferencia entre los 2 valores obtenidos, tanto en la
        # cantidad de pasajeros como en los minutos, y se los divide entre si,
        # lo cual resulta en un factor aproximado de personas por minuto entre
        # esos 2 intervalos de tiempo. Toda esta opración se omite si el tiempo
        # dado tiene directamente un registro en la base de datos.
        acumulated_passengers = 0
        p = []

        for i in [st,end]:
            floor = datetime.time(
                    hour=i.hour,
                    minute=math.floor(i.minute / 10) * 10,
                    second=i.second
            )

            ceil = datetime.time(
                    hour=i.hour,
                    minute=math.ceil(i.minute / 10) * 10,
                    second=i.second
            )

            s = sf.between_time(floor,ceil)

            # se tiene un registro del valor anterior, en caso de encontrar la
            # primera diferencia de tiempo positiva, se opera el valor anterior
            # y el actual. Esto es válido debido a que se asume que los
            # registros están en orden
            prev_val = 0
            prev_time = None
            val_diff = 0
            time_diff = 0

            for ts,reg in s.iterrows():
                diff = ts - floor # type: ignore
                val = reg["passengers"]
                curr_time = ts
                val_diff = val - prev_val
                time_diff = curr_time - prev_time # type: ignore
                if diff > 0:
                    break
                prev_val = val
                prev_time = curr_time

            p.append(time_diff / val_diff if val_diff != 0 else 0)
        df[] += max(p)


        if len(stop.visits) == 0:
            s = sf.between_time(start.time(),end.time())
        else:
            s = sf.between_time(st.time(),end.time())

        df = pd.concat([df,s])
        df = typing.cast(pd.DataFrame,df)


    CACHE = {}
    CACHE["stops"] = scoped_stops
    CACHE["start"] = start
    CACHE["t"] = t
    CACHE["pt"] = df["passengers"].sum() - already_done
    CACHE["qt"] = (df[df["passengers"] == df["passengers"].max()].iloc[-1].name - start ).seconds // 60 # pylint: disable=C0301

    return (CACHE["pt"],CACHE["qt"])



def _reorder_stop(stops: list[Stop], s: str|int) -> list[Stop]:
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
        stops: list[Stop],
        scores: Scores,
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
    b = scores.cap_cost
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
        print(f"Params: t={t}, stop={sp} ,a={a}, b={b}, c={c}, d={d}, t={t} p(t)={pt}, q(t)={qt}, x={x}. Result: {result}") # pylint: disable=C0301
        return result

    return typing.cast(Scorefn,formula)
