"""Ejecutar el módulo"""
import os
import pandas as pd
import datetime
import asyncio
import dataclass_wizard as dw

from typing import cast

from msopti.params import json_params as params
from msopti.algorithm import annealing, formula, interfaces
from msopti.params.interfaces.route_provider import IRouteProvider
from msopti.params.interfaces.stop_provider import IStopProvider
from msopti.params.interfaces.vehicle_provider import IVehicleProvider

# Globals
ROUTE = 30
P = params.load_params_from_file(os.environ["PARAMS_PATH"])
DF = pd.read_csv(os.environ["DATASET_TEST_PATH"])

def available(i: IVehicleProvider) -> bool:
    return i.is_available and i.route_id == ROUTE

async def run():
    units = [i for i in P.vehicles if available(i)]
    route = next(i for i in P.routes if i.id == ROUTE)
    stops = [i for i in P.stops if i.id in route.stops]

    cap_score = P.scores.capacity_cost
    time_score = P.scores.minute_price
    low_demand_score = P.scores.low_demand_cost
    zero_demand_score = P.scores.zero_demand_cost
    interval = P.schedule.interval

    today = datetime.datetime(2024,3,23)
    forecast = cast(pd.DataFrame,DF[DF["stop_id"].isin(route.stops)])
    forecast["timespan"] = pd.DatetimeIndex(DF["timespan"])
    forecast.set_index(keys="timespan",inplace=True)
    initial_time = today + P.schedule.start.min
    final_time = today + P.schedule.start.max

    g = forecast.groupby(cast(pd.DatetimeIndex,forecast.index).floor("d")) # type: ignore pylint: disable=C0301
    cdate = pd.Timestamp(today)
    forecast = cast(pd.DataFrame,g.get_group(cdate))
    # forecast = forecast.between_time(initial_time.time(),final_time.time())

    time_max = (final_time - initial_time) / len(units)

    solutions: list[interfaces.Solution] = []
    while len(units) != 0:
        f = formula.gererate_formula(forecast,stops,P.scores)
        an2 = annealing.AnnealSolver(
            f,
            time_score,
            cap_score,
            low_demand_score,
            zero_demand_score,
            initial_time,
            time_max,
            interval,
            units,
            stops
        )
        print("== DISPATCH ==")
        solution = an2.solve()
        solutions.append(solution)
        unit = next(u for u in units if u.unumber == solution.unit.unumber)
        unit.is_available = False
        units = [i for i in P.vehicles if available(i)]

        initial_time += datetime.timedelta(minutes=solution.delay) \
            + P.schedule.interval

        # TODO: Mover esta implementación a solve_multi y considerar los
        # cambios y reordenamiento de las rutas
        for i,sto in enumerate(solution.planification):
            last_time = datetime.datetime(
                year=initial_time.year,
                month=initial_time.month,
                day=initial_time.day,
                hour=sto.time.hour,
                minute=sto.time.minute
            )
            stops[i].visit(last_time)

        for stop in stops:
            print(stop)

    return solutions


async def main():
    solutions = await run()
    df = pd.concat([i.to_dataframe() for i in solutions])

    print("===  Planification  ==")
    print("== Configuraciones ===")
    print(f"    Se intentará despachar como mínimo cada {P.schedule.interval}")
    print("\n")
    print("== Unidades despachadas (en orden) ===")

    for i in solutions:
        print(f"Stop: {dw.asdict(next(j for j in P.stops if j.get_id() == i.start_point), exclude=('time', 'event_delay', 'last_visit'))}") # type: ignore pylint: disable=C0301
        print(f"    {dw.asdict(i.unit, exclude=('available','start_point','route'))}") # type: ignore pylint: disable=C0301
        print(f"         {[j.time.isoformat() for j in i.planification]}")
        print(f"         Esperado {i.delay} minutos antes de despachar")
        print("\n\n")

    print("View results on testing.csv")
    df.to_csv("testing.csv")

asyncio.run(main())
