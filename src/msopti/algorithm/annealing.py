"""Resuelve el problema planteado utilizando Recocido Simulado."""
import simanneal
import datetime

from msopti.algorithm.interfaces import ISolver, Scorefn, Solution, SolverParams, StopTime
from msopti.params import Vehicle, Stop

class _AnnealImpl(simanneal.Annealer):
    """Implementación de `simanneal.Annealer` para el problema planteado:
    Ver más en [https://github.com/perrygeo/simanneal?tab=readme-ov-file#quickstart]
    """
    _params: SolverParams

    def move(self):
        """Obtener el siguiente estado."""
        unumber = self._params.units[self._index].unit_number
        self.state = (unumber,(self._time.seconds // 60), self._istop)

        if self._index == len(self._params.units) - 1:
            self._index = 0

            should_update_time = True
            if self._params.optimize_stops and self._istop == len(self._params.stops) - 1:
                self._istop = 0
            elif self._params.optimize_stops:
                self._istop += 1
                should_update_time = False

            if should_update_time and self._time >= self._params.time_max:
                self._time = datetime.timedelta(minutes=0)
            elif should_update_time:
                self._time += self._params.interval

        else:
            self._index += 1


    def energy(self):
        """Calcular la puntuación del estado actual."""
        units = self._params.units
        unit: Vehicle = next(x for x in units if x.unit_number == self.state[0])
        start_time = self._params.start_time
        stop = self._params.stops[self._istop].id
        t = datetime.timedelta(minutes=self.state[1])

        return self._params.formula(start_time,stop,t,unit.max)


    def __init__(self,state: tuple[str|int,int,int],params: SolverParams) -> None:
        # El número máximo de iteraciones se obtiene multiplicando 'm * n * o'.
        # Estas fórmulas son correspespondientes a las
        # combinaciones de los distintos parámetros del algoritmo. En caso de
        # que 'optimize_stops = False', 'o = 1'
        steps = \
            (params.time_max // params.interval) * \
            len(params.units) * \
            (len(params.stops) if params.optimize_stops else 1)

        self._index = 0
        self._istop = 0
        self._time = datetime.timedelta(minutes=0)
        self._params = params
        super(_AnnealImpl,self).__init__(state)
        self.copy_strategy = "slice"
        schedule = self.auto(minutes=0.2,steps=steps)
        self.set_schedule(schedule)


class AnnealSolver(ISolver):
    """Solucionador que utiliza Recocido simulado para obtener la solución
    óptima.

    Utiliza una implmentación de la interfaz provista por
    [https://github.com/perrygeo/simanneal] para la resolución del problema
    con recocido simulado.

    El Recocido simulado es un algoritmo que genera opciones de solución y las
    evalúa siguiendo una fórmula de clasificación. Opta por el mejor estado
    (en este caso, la combinación de parámetros con el menor resultado).

    La forma en la que se opera es la siguiente:

    1. Se tiene una tupla, en la cual se representa el número de unidad, la
    cantidad de minutos antes de salir y una lista de las unidades para 
    consultar información más detallada de una unidad.

    2. Se obtiene un nuevo tiempo actual, sumando el último tiempo obtenido
    y la cantidad de minutos que espera cada unidad. Si es la primera iteración,
    la cantidad de minutos será siempre 0.

    3. Se califica ese tiempo y parada en todas las unidades disponibles.

    4. Cuando se termine con las unidades, se sumará el tiempo otro intervalo.
    Así hasta llegar al tiempo máximo.

    5. El número de iteraciones será calculado en base al número de veces que
    se puede subir el intervalo (m) y la cantidad de unidades que se tiene (n),
    siguiendo la fórmula $m \\times n \\times o$

    Si se define `optimize_stops = True`, se realizan las siguientes
    modificaciones:

    1. Adicional al número de la unidad, y la cantidad de minutos antes de salir
    de una parada, se lleva seguimiento al número de parada desde donde
    iniciaría el recorrido.

    2. Se obtiene la parada actual, recorriendo el índice de la parada en 1.
    Cuando se recorran todas, este índice vuelve a ser 0.

    3. Al finalizar la iteración por las unidades, antes de sumar otro intervalo
    de tiempo, se recorrerá una parada hasta terminar con las mismas.

    5. El número de iteraciones será calculado en base al número de veces que
    se puede subir el intervalo (m), la cantidad de unidades que se tiene (n), y
    la cantidad de paradas que tiene una ruta, siguiendo la fórmula
    $m \\times n \\times o$
    """
    _annealer: _AnnealImpl
    _params: SolverParams

    def solve(self) -> Solution:
        result: tuple[str|int,int,int]
        result, _ = self._annealer.anneal()
        unit = next(i for i in self._params.units if i.unit_number == result[0])
        stopi = result[2]
        stop_id = self._params.stops[stopi].id
        delay = result[1]

        start = datetime.timedelta(
            hours=self._params.start_time.hour,
            minutes=self._params.start_time.minute
        )

        official_start_time = start + datetime.timedelta(minutes=delay)

        p1 = []
        p2 = []

        acum = official_start_time
        for i in self._params.stops[stopi:]:
            stop_time = acum + i.time + i.event_delay
            acum = stop_time
            p1.append(
                StopTime(
                    i,
                    datetime.time(
                        hour=stop_time.seconds // 3600,
                        minute=(stop_time.seconds % 3600) // 60,
                    )
                )
            )

        for i in self._params.stops[:stopi]:
            stop_time = acum + i.time + i.event_delay
            acum = stop_time
            p2.append(
                StopTime(
                    i,
                    datetime.time(
                        hour=stop_time.seconds // 3600,
                        minute=(stop_time.seconds % 3600) // 60,
                    )
                )
            )

        planification = p1 if len(p2) == 0 else (p2 + p1)

        return Solution(unit,planification,stop_id,delay)


    def solve_multi(self):
        result: tuple[int,int]
        e: float
        result, e = self._annealer.anneal()

        unit = next(i for i in self._params.units if i.unit_number == result[0])
        print(f"Unidad: {unit}")
        print(f"Minutos antes de salir: {result[1]}")
        print(f"Puntuación: {e}")


    def __init__(
        self,
        formula: Scorefn,
        time_score: float,
        cap_score: float,
        low_demand_score: float,
        zero_demand_score: float,
        start_time: datetime.datetime,
        time_max: datetime.timedelta,
        interval: datetime.timedelta,
        units: list[Vehicle],
        stops: list[Stop],
        optimize_stops: bool = False
        ) -> None:
        p = SolverParams(
            formula,
            time_score,
            cap_score,
            low_demand_score,
            zero_demand_score,
            start_time,
            time_max,
            interval,
            units,
            stops,
            optimize_stops
        )

        # En https://github.com/perrygeo/simanneal?tab=readme-ov-file#implementation-details
        # se menciona que el algoritmo require hacer un seguimiento al estado,
        # por ende, mantener copias del mismo.
        # A modo de optimización prematura
        # (a pesar de que se que es la raíz de todo mal) decido mantener
        # la representación del estado lo más ligera y rápida de copiar posible,
        # razón por la cual no utilizo SolverParams como el estado
        initial_state = next((unit.unit_number,0,0) for unit in units)
        self._annealer = _AnnealImpl(initial_state,p)
        self._params = p
