# -*- coding: utf-8 -*-
"""
Tests for MTRESS FixedTemperatureHeat Demand.
"""
import os

import pytest
from oemof.solph.processing import results

from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies
)
from mtress._helpers import get_flows

n_days = 30


@pytest.mark.skip(reason="Not really a test, yet.")
def test_layered_heat_storage():

    house_1 = Location(name="house_1")
    house_1.add(
        carriers.HeatCarrier(
            temperature_levels=[10, 20, 30],
            reference_temperature=0,
        )
    )

    reservoir_temperature = np.full(n_days * 24, 20)
    reservoir_temperature[10 * 24 : 12 * 24] = 0
    house_1.add(
        technologies.HeatSource(
            name="source",
            reservoir_temperature=20,
            nominal_power=1e6,
            maximum_working_temperature=40,
            minimum_working_temperature=10,
        )
    )

    waste_heat = np.zeros(n_days * 24)
    waste_heat[14 * 24] = 10e3
    house_1.add(
        demands.FixedTemperatureCooling(
            name="CD",
            max_flow_temperature=20,
            return_temperature=30,
            time_series=waste_heat,
        )
    )

    heat_demand = np.zeros(n_days * 24)
    heat_demand[7 * 24] = 5e3
    house_1.add(
        demands.FixedTemperatureHeating(
            name="HD",
            min_flow_temperature=30,
            return_temperature=20,
            time_series=heat_demand,
        )
    )

    house_1.add(
        technologies.LayeredHeatStorage(
            name="HS",
            diameter=1,
            volume=10,
            ambient_temperature=0,
            u_value=0.1,
            power_limit=None,
            max_temperature=30,
            min_temperature=10,
            initial_storage_levels={30: 0.9},
            balanced=False,
        )
    )
    meta_model = MetaModel(locations=[house_1])

    solph_representation = SolphModel(
        meta_model=meta_model,
        timeindex={
            "start": "2021-01-01 00:00:00",
            "end": f"2021-01-{n_days+1} 00:00:00",
            "freq": "60min",
        },
    )

    solph_representation.build_solph_model()

    solved_model = solph_representation.solve(solve_kwargs={"tee": True})

    return solph_representation, solved_model


if __name__ == "__main__":
    import matplotlib
    import matplotlib.pyplot as plt
    import numpy as np

    matplotlib.use("QtAgg")

    os.chdir(os.path.dirname(__file__))

    solph_representation, solved_model = test_layered_heat_storage()

    myresults = results(solved_model)
    flows = get_flows(myresults)

    total_content = np.zeros(n_days * 24 + 1)
    index = None
    for key, result in myresults.items():
        if "storage_content" in result["sequences"]:
            plt.plot(
                result["sequences"]["storage_content"] * 1e-3,
                label=str(key[0].label.solph_node),
            )
            total_content += result["sequences"]["storage_content"]
            index = result["sequences"].index
    plt.plot(index, total_content * 1e-3, label="total")
    plt.ylabel("Energy (kWh)")

    plt.legend()

    plot = solph_representation.graph(detail=True, flow_results=flows)
    plot.render(outfile="layered_heat_demand.png")

    plt.show()
