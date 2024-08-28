"""
Example to illustrate use of gas carrier and gas grid connection along with
CHP implementation for heat and power generation.
"""

import logging
import os

from oemof.solph.processing import results

from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies
from mtress.physics import HYDROGEN
from mtress.technologies import HYDROGEN_CHP

LOGGER = logging.getLogger(__file__)
from mtress._helpers import get_flows

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
house_2 = Location(name="house_2")

energy_system.add_location(house_1)
energy_system.add_location(house_2)


house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=350))

house_1.add(
    technologies.GasGridConnection(
        name="H2_Grid",
        gas_type=HYDROGEN,
        grid_pressure=40,
        working_rate=5,
        revenue=-5,
    )
)

house_1.add(
    carriers.GasCarrier(
        gases={
            HYDROGEN: [30, 40, 50],
        }
    )
)

house_1.add(
    demands.Electricity(
        name="electricity_demand",
        time_series=1e3,
    )
)

house_1.add(
    carriers.HeatCarrier(
        temperature_levels=[20, 80],
        reference_temperature=0,
    )
)

house_1.add(
    demands.FixedTemperatureHeating(
        name="heat_demand",
        time_series=20e3,
        min_flow_temperature=80,
        return_temperature=20,
    )
)


house_1.add(
    technologies.CHP(
        name="H2_CHP",
        nominal_power=4e3,
        template=HYDROGEN_CHP,
        input_pressure=30,
    )
)


house_2.add(
    carriers.GasCarrier(
        gases={
            HYDROGEN: [30, 40, 50],
        }
    )
)

house_2.add(
    technologies.GasGridConnection(
        name="H2_Grid",
        gas_type=HYDROGEN,
        grid_pressure=40,
        working_rate=None,
        revenue=2,
    )
)

house_2.add(
    demands.GasDemand(name="H2_demand", gas_type=HYDROGEN, time_series=1, pressure=30)
)

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2022-06-01 08:00:00",
        "end": "2022-06-01 09:00:00",
        "freq": "15T",
        "tz": "Europe/Berlin",
    },
)

house_1.connect(connection=technologies.GasGridConnection, destination=house_2)

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=True)
plot.render(outfile="gas_grid_detail.png")

plot = solph_representation.graph(detail=False)
plot.render(outfile="gas_grid_simple.png")

solved_model = solph_representation.solve(solve_kwargs={"tee": True})

myresults = results(solved_model)
flows = get_flows(myresults)

plot = solph_representation.graph(detail=True, flow_results=flows)
plot.render(outfile="gas_grid_flow.png")

solved_model.write("gas_plant.lp", io_options={"symbolic_solver_labels": True})
