"""
Example to illustrate use of gas carrier and gas grid connection along with
CHP implementation for heat and power generation.
"""

import logging
import os

from oemof.solph.processing import results

from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)
from mtress.physics import HYDROGEN, NATURAL_GAS
from mtress.technologies import HYDROGEN_MIXED_CHP

LOGGER = logging.getLogger(__file__)
from mtress._helpers import get_flows

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")

energy_system.add_location(house_1)


house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=0.35))
house_1.add(
    technologies.GasGridConnection(
        name="NG_Grid",
        gas_type=NATURAL_GAS,
        grid_pressure=10,
        working_rate=5,
        revenue=None,
    )
)

house_1.add(
    technologies.GasGridConnection(
        name="H2_Grid",
        gas_type=HYDROGEN,
        grid_pressure=40,
        working_rate=15,
        revenue=None,
    )
)

house_1.add(
    carriers.GasCarrier(
        gases={
            HYDROGEN: [30, 40],
            NATURAL_GAS: [10, 20, 30],
        }
    )
)

house_1.add(
    demands.Electricity(
        name="electricity_demand",
        time_series="FILE:../input_file.csv:electricity",
    )
)

house_1.add(
    carriers.HeatCarrier(
        temperature_levels=[20, 80],
        reference_temperature=10,
    )
)


# Choose default CHP template (HYDROGEN_MIXED_CHP) and change gas
# shares (vol %)

house_1.add(
    technologies.CHP(
        name="Mixed_CHP",
        nominal_power=1e5,
        gas_type={NATURAL_GAS: 0.75, HYDROGEN: 0.25},
        template=HYDROGEN_MIXED_CHP,
    )
)

# Add heat demands
house_1.add(
    demands.FixedTemperatureHeating(
        name="heat_demand",
        min_flow_temperature=80,
        return_temperature=20,
        time_series="FILE:../input_file.csv:heat",
    )
)

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2022-06-01 08:00:00",
        "end": "2022-06-06 18:00:00",
        "freq": "15T",
        "tz": "Europe/Berlin",
    },
)

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=True)
plot.render(outfile="gas_plant_detail.png")

plot = solph_representation.graph(detail=False)
plot.render(outfile="gas_plant_simple.png")

solved_model = solph_representation.solve(solve_kwargs={"tee": True})

logging.info("Optimise the energy system")
myresults = results(solved_model)
flows = get_flows(myresults)

plot = solph_representation.graph(
    detail=True, flow_results=flows, flow_color=None
)
plot.render(outfile="gas_plant_results.png")

solved_model.write("gas_plant.lp", io_options={"symbolic_solver_labels": True})
