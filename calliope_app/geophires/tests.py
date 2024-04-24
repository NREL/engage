import os
import datetime

from django.conf import settings
from django.test import TestCase

from geophires.geophiresx import Geophires

class GeophiresTestCase(TestCase):
    
    def test_geophires_run(self):
        start_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        plant = 'binary_subcritical'

        # subsurface parameters
        inputs = dict(
            reservoir_heat_capacity = 700,
            reservoir_density = 1400,
            reservoir_thermal_conductivity = 4,
            gradient = 60,

            min_temperature = 200,
            max_temperature = 200,
            temperature_step = 25,

            min_reservoir_depth = 1,
            max_reservoir_depth = 5,
            reservoir_depth_step = 0.1,

            min_production_wells = 1,
            max_production_wells = 7,
            production_wells_step = 1,

            min_injection_wells = 1,
            max_injection_wells = 7,
            injection_wells_step = 1
        )
        
        ## Run

        job_meta_id = '123'
        result_file = os.path.join(settings.DATA_STORAGE, "geophires", f"{job_meta_id}__{plant}__{start_time}.csv")
        
        geophiers = Geophires()
        geophiers.run(input_params=inputs, output_file=result_file)
