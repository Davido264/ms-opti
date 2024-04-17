"""
Interfaz para proveer información sobre las puntuaciones configuradas.
"""

import abc

class IScoreProvider(abc.ABC):
    """
    Puntuaciones o valores de penalización para cada variable.

    Varios algoritmos requieren de una definición de factores de
    penalización, dependiendo de los valores que estos se escojan
    será el desempeño del algoritmo. Los valores dados por esta
    clase, se multiplicarán a los valores calculados por la
    fórmula, por lo que a mayor sea el valor de acada atributo,
    mayor penalización tendrá el aumento de dicha característica.

    No existe una regla para definir estas puntuaciones, lo que si
    se debe considerar es el valor relativo que estas tendrán con
    respecto a si mismas.

    Cabe recalcar que los algoritmos van a optar por la fórmula con
    el menor resultado posible.
    """

    @property
    @abc.abstractmethod
    def minute_price(self) -> float:
        """
        Penalización asignada al minuto de espera.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def capacity_cost(self) -> float:
        """
        Penalización por diferencia entre la capacidad máxima con la cantidad 
            de personas pronosticadas.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def low_demand_cost(self) -> float:
        """
        Penalización a despachos realizados cuando existe poca demanda.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def zero_demand_cost(self) -> float:
        """
        Penalización dada a despachos realizados cuando no existe demanda.
        """
        raise NotImplementedError
