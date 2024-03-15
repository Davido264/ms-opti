"""Definición de interfaces y tipos genéricos que serán 
utilizados por los algoritmos"""

import abc
from dataclasses import dataclass
import datetime
import pandas as pd

from typing import TypeAlias, Callable
from msopti.params import Stop, Vehicle

Scorefn: TypeAlias = Callable[[datetime.datetime,str|int,datetime.timedelta,int],float] # pylint: disable=C0301
"""Función de calificación.

Args:
    time_score: float, penalización del tiempo.
    cap_score: float, penalización de la capacidad.
    low_demand_score: float, penalización de viaje con poca demanda.
    zero_demand_score: float, penalización de viaje con demanda = 0.
    start_time: datetime.datetime, punto de inicio para realizar el cálculo.
    time: datetime.timedelta, tiempo de espera.
    cap: int, capacidad de un vehículo.

Returns:
    Un valor float, el cual es la puntuación de los parámetros.
"""

@dataclass
class SolverParams():
    """Conjunto de parámetros necesarios para los algoritmos.

    Depende de la implementación del algoritmo decidir si usa
    esta clase como atributo. El objetivo de esta clase es
    agrupar las variables necesarias para la ejecución de un
    algoritmo.

    Attributes:
        formula: una `Scorefn` que define la fórmula que califica las
            soluciones.
        time_score: Penalización configurada para el tiempo.
        cap_score: Penalización configurada para la diferencia entre la
            capacidad y la cantidad de personas pronosticadas.
        low_demand_score: Penalización de viaje con poca demanda.
        zero_demand_score: Penalización de viaje con demanda = 0.
        time: Tiempo inicial antes de un despacho.
        time_max: Tiempo máximo que se puede aceptar antes de despachar una
            unidad.
        interval: Tiempo mínimo que se espera de despacho en despacho.
        units: Lista de unidades que están asignados a una ruta en específico.
        stops: Lista de paradas asignadas a una ruta.
    """

    formula: Scorefn
    time_score: float
    cap_score: float
    low_demand_score: float
    zero_demand_score: float
    start_time: datetime.datetime
    time_max: datetime.timedelta
    interval: datetime.timedelta
    units: list[Vehicle]
    stops: list[Stop]


@dataclass
class StopTime:
    """Representación de un punto en la planificación de rutas.

    Se usa esta clase con el objetivo de estandarizar la interfaz
    de salida del método `ISolver.solve()`.

    Attributes:
        stop: La parada en un punto de la planficiación.
        time: El tiempo en el que se esta en la parada.
    """

    stop: Stop
    time: datetime.time


@dataclass
class Solution:
    """Representación de la solución del problema.

    La resolución del problema incluye un dataframe con las paradas y tiempos
    programados según su planificación configurada. Así como la unidad
    más óptima a realizar el recorrido.

    Attributes:
        unit: El vehículo seleccionado para realizar el recorrido.
        planification: Un lista de `StopTime` representando la planificación de
            la unidad.
        start_point: El id de la parada (str|int) en donde se comenzará a
            despachar.
        delay: El tiempo que se esperó antes de realizar el despacho. Es la
            solución del algoritmo.
    """

    unit: Vehicle
    planification: list[StopTime]
    start_point: str|int
    delay: int

    def to_dataframe(self) -> pd.DataFrame:
        """Retorna la representación de la planficiación en `pandas.DataFrame`.

        La representación de la planficiación estará dado en una fila, la
        cantidad de columnas será la cantidad de paradas en la ruta, el número
        de la unidad será el índice del dataframe, y el valor de cada celda del
        dataframe será el tiempo en donde se prevee que se visitará una parada.

        El objetivo de esta representación es que se puedan generar varias de
        las mismas y posteriormente, ser concatenadas para obtener una
        _tabla de despachos_.

        Returns:
            Un `pandas.DataFrame` de una sóla filas, y $n$ columnas.
        """
        df =  pd.DataFrame(
            [[ i.time for i in self.planification ]],
            index=pd.Index([self.unit.unit_number]),
        )

        df.columns = [ i.stop.name for i in self.planification ]

        return df


class ISolver(metaclass=abc.ABCMeta):
    """Interfaz de los solucionadores.
    Define el método `solve()` y `solve_multi()`
    """

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, "solve") and
                callable(subclass.solve) and
                hasattr(subclass, "solve_multi") and
                callable(subclass.solve_multi))

    @abc.abstractmethod
    def solve(self) -> Solution:
        """Resuelve el problema planteado usando las configuraciones y el
        algoritmo indicados.

        Returns:
            La resolución del problema.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def solve_multi(self):
        """Resuelve el problema planteado usando las configuraciones y el
        algoritmo indicados.

        Este método busca solucionar el problema con una lista de candidatos
        en lugar de sólo un candidato.

        Returns:
            La resolución del problema.
        """
        raise NotImplementedError


