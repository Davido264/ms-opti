"""
Interfaz para proveer la información de las rutas.
"""

import abc

class IRouteProvider(abc.ABC):
    """Información de una ruta.

    Una ruta contiene múltiples paradas en un determinado orden, es
    importante que la representación de dichas rutas en esta clase
    mantengan ese mismo orden, no es lo mismo una lista de rutas con
    `[ 0, 1 ]` que una lista de rutas con `[ 1, 0 ]`.
    """

    @property
    @abc.abstractmethod
    def id(self) -> str|int:
        """
        El ID de la ruta en string o int.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def stops(self) -> tuple[str|int]:
        """
        Una tupla (inmutable) de IDs de paradas (strings o ints), indicando las
            paradas que sigue la ruta.
        """
        raise NotImplementedError
