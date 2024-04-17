"""
Intefaz para proveer la información de las paradas
"""
import abc
import datetime

class IStopProvider(abc.ABC):
    """
    Información de una parada.

    Una parada puede ser un punto en varias rutas, para el algoritmo tanto como
    para el modelo, si una parada se encuentra en 2 o más rutas, se consierará
    como si hay 2 o más paradas con el mismo nombre, pero distintos tiempos e
    id.

    Esta interfaz se disñó para ser el proveedor de la información sobre las
    paradas que se tiene, Abstrayendo su implementación y permitiendo definir
    varias fuentes de información.
    """

    @property
    @abc.abstractmethod
    def id(self) -> str|int:
        """
        El ID de una parada en string o int.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """
        El nombre de una parada
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def time(self) -> datetime.timedelta:
        """
        El tiempo que demora **normalmente** el recorrido desde la parada 
            anterior a la parada actual.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def event_delay(self) -> datetime.timedelta:
        """
        El tiempo adicional que tardará el transporte en llegar a la parada,
            (por defecto 0, modificado dinámicamente).
        """
        raise NotImplementedError

    @event_delay.setter
    @abc.abstractmethod
    def event_delay(self, d: datetime.timedelta):
        """
        Establece un nuevo valor para `get_event_delay`

        El `event_delay` se establece dinámicamente dependiendo de eventos
        externos a la planificación normal que se tenga.

        Arguments:
            d: Nuevo valor para `get_event_delay`
        """
        raise NotImplementedError


    @property
    @abc.abstractmethod
    def visits(self) -> tuple[datetime.datetime]:
        """
        Una tupla (inmutable) de registros de visitas
        """
        raise NotImplementedError

    @abc.abstractmethod
    def visit(self,dt: datetime.datetime):
        """
        Agrega el tiempo dado al registro de visitas de una parada

        Arguments:
            dt: Nuevo tiempo para agregar al registro de paradas
        """
        raise NotImplementedError
