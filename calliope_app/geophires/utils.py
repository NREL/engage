import pandas as pd
from geophires_x_client import GeophiresXClient
from geophires_x_client.geophires_input_parameters import GeophiresInputParameters
import numpy as np
from scipy.optimize import curve_fit
from scipy.optimize import minimize


def fit_lower_bound(x, y, percentile):
    # Sort the data by x and get the lower percentile of y for each x
    indices = x.argsort()
    x_sorted = x[indices]
    y_sorted = y[indices]

    # Define the objective function for the linear model: y = ax + b
    def objective(x, a, b):
        return a * x + b

    # Define an error function that will be minimized
    def error_function(params):
        a, b = params
        fitted_line = objective(x_sorted, a, b)
        # Error is a combination of distance to the lower percentile points and the y-intercept
        return np.sum((fitted_line - y_sorted) ** 2) + b**2

    # Initial guess for parameters a and b
    initial_guess = [0, 0]

    # Perform the minimization
    result = minimize(error_function, initial_guess)

    # Extract the optimized parameters
    a_opt, b_opt = result.x

    # Calculate the residuals and find the lower bound threshold
    residuals = y_sorted - objective(x_sorted, a_opt, b_opt)
    threshold = np.percentile(residuals, percentile)

    # Adjust the y-intercept to the lower bound threshold
    b_lower_bound = b_opt + threshold

    # Generate x values for the line of best fit
    x_line = np.asarray([np.min(x), np.max(x)])

    # Calculate the y values for the lower bound line
    lower_line = objective(x_line, a_opt, b_lower_bound)

    # Create a label for the plot
    label = f'y={a_opt:.4f}x+{b_lower_bound:.4f}'

    return a_opt, b_lower_bound, x_line, lower_line, label


def fit_linear_model(x, y, res, m_offset, b_offset):
    # Define the objective function for the linear model: y = ax + b
    def objective(x, a, b):
        return a * x + b

    # Use curve fitting to find the optimal values of a and b that minimize
    # the difference between the predicted y values and the actual y values
    popt, _ = curve_fit(objective, x, y)
    a, b = popt  # a is the slope, b is the y-intercept

    a = a * (m_offset + 1)

    # Generate x values for the line of best fit: use the minimum and maximum x values
    x_line = np.asarray([np.min(x), np.max(x)])

    # Calculate the residuals (difference between actual y values and predicted y values)
    # This is used to adjust the y-intercept for the lower bound line

    b_values = y - np.multiply(a, x)

    # Calculate the 5th percentile of the residuals to determine the lower bound
    lower_b = np.percentile(b_values, res) + b_offset

    # Calculate the y values for the lower bound line using the adjusted y-intercept
    lower_line = objective(x_line, a, lower_b)

    # Create a label for the plot with the equation of the lower bound line
    label = f'y={a:.4f}x+{lower_b:.4f}'

    return a, lower_b, x_line, lower_line, label


class geophires_parametrization_analysis:
    def __init__(self, prod_temp_min, prod_temp_max):
        self.client = GeophiresXClient()
        self.df_results = []
        self.parameter_list = []
        self.prod_min = prod_temp_min
        self.prod_max = prod_temp_max  # Corrected this line to properly set prod_max
        self.results_cache = {}  # Cache for storing results

    def get_value(self, results, keys):
        for key in keys:
            results = results.get(key, {})
            if not isinstance(results, dict):
                return None
        return results.get('value', None)

    def calculate_ratios(self, data_row):
        # Make sure the required data is present
        required_keys = [
            'Average Reservoir Heat Extraction (MWth)',
            'Average Heat Production (MWth)',
            'Average Electricity Production (MWe)',
        ]

        if not all(key in data_row for key in required_keys):
            print('Required data is missing to calculate ratios.')
            return None

        # Calculate ratios
        heat_extraction = data_row['Average Reservoir Heat Extraction (MWth)']
        heat_production = data_row['Average Heat Production (MWth)']
        electricity_production = data_row['Average Electricity Production (MWe)']

        ratios = {
            'Ratio Avg Reservoir Heat Extraction to Ratio Avg Reservoir Heat Extraction': heat_extraction
            / heat_extraction
            if heat_extraction
            else 0.0,
            'Ratio Avg Heat Production to Avg Reservoir Heat Extraction': heat_production / heat_extraction
            if heat_extraction
            else 0.0,
            'Ratio Avg Electricity Production to Avg Reservoir Heat Extraction': electricity_production
            / heat_extraction
            if heat_extraction
            else 0.0,
        }

        return ratios

    def process_multiple(self, input_params):
        # Initialize data_row at the beginning of the method
        data_row = {}

        param_key = str(input_params)
        if param_key in self.results_cache:
            return self.results_cache[param_key]

        result = self.client.get_geophires_result(GeophiresInputParameters(input_params))
        all_results = result.result

        # Define paths for the values we're interested in
        paths = {
            'Depth (km)': ['ENGINEERING PARAMETERS', 'Well depth (or total length, if not vertical)'],
            'Number of Prod Wells': ['ENGINEERING PARAMETERS', 'Number of Production Wells'],
            'Number of Inj Wells': ['ENGINEERING PARAMETERS', 'Number of Injection Wells'],
            'Flow Rate per Prod Well (kg/sec)': ['ENGINEERING PARAMETERS', 'Flowrate per production well'],
            'Maximum Reservoir Temperature (deg.C)': ['RESOURCE CHARACTERISTICS', 'Maximum reservoir temperature'],
            'Surface Plant Cost ($M)': ['CAPITAL COSTS (M$)', 'Total surface equipment costs'],
            'Exploration Cost ($M)': ['CAPITAL COSTS (M$)', 'Exploration costs'],
            'Drilling and completion cost ($MUSD)': ['CAPITAL COSTS (M$)', 'Drilling and completion costs'],
            'Wellfield maintenance costs ($MUSD/yr)': [
                'OPERATING AND MAINTENANCE COSTS (M$/yr)',
                'Wellfield maintenance costs',
            ],
            'Make-Up Water O&M Cost ($MUSD/year)': ['OPERATING AND MAINTENANCE COSTS (M$/yr)', 'Water costs'],
            'Average Reservoir Heat Extraction (MWth)': [
                'RESERVOIR SIMULATION RESULTS',
                'Average Reservoir Heat Extraction',
            ],
            'Average Heat Production (MWth)': ['SURFACE EQUIPMENT SIMULATION RESULTS', 'Average Net Heat Production'],
            'Average Cool Production (MW)': ['SURFACE EQUIPMENT SIMULATION RESULTS', 'Average Cooling Production'],
            'Average Electricity Production (MWe)': [
                'SURFACE EQUIPMENT SIMULATION RESULTS',
                'Average Net Electricity Generation',
            ],
            'Lifetime': ['ECONOMIC PARAMETERS', 'Project lifetime'],
            'Total capital costs ($MUSD/yr)': ['CAPITAL COSTS (M$)', 'Total capital costs'],
            'Surface maintenance costs ($MUSD/yr)': [
                'OPERATING AND MAINTENANCE COSTS (M$/yr)',
                'Power plant maintenance costs',
            ],
            'Average Production Temperature (degC)': ['RESERVOIR SIMULATION RESULTS', 'Average Production Temperature'],
            'Maximum Total Electricity Generation (MWe)': [
                'SURFACE EQUIPMENT SIMULATION RESULTS',
                'Maximum Total Electricity Generation',
            ],
            'Maximum Cooling Production (MW)': ['SURFACE EQUIPMENT SIMULATION RESULTS', 'Maximum Cooling Production'],
            'Maximum Net Heat Production (MWth)': [
                'SURFACE EQUIPMENT SIMULATION RESULTS',
                'Maximum Net Heat Production',
            ],
        }

        # Extract values using the defined paths and update data_row
        for label, path in paths.items():
            value = self.get_value(all_results, path)

            if value is not None:
                data_row[label] = value

        data_row = {k: v for k, v in data_row.items() if v is not None}
        self.results_cache[param_key] = data_row

        ratios = self.calculate_ratios(data_row)
        if ratios:
            data_row.update(ratios)

        return data_row

    def run_iterations(self):
        for params in self.parameter_list:
            data_row = self.process_multiple(params)
            # Check if Average Production Temperature is within the specified range
            avg_prod_temp = data_row.get('Average Production Temperature (degC)', None)
            if avg_prod_temp is not None and self.prod_min <= avg_prod_temp <= self.prod_max:
                self.df_results.append(data_row)
            elif avg_prod_temp is not None and avg_prod_temp > self.prod_max:
                break  # Stop processing once the maximum temperature is reached

    def prepare_parameters(self, new_params_list):
        self.parameter_list = new_params_list

    def get_final_dataframe(self):
        return pd.DataFrame(self.df_results)
    
def generate_parameters(base_params, depth_range, flow_rate_range, wells_prod_range, wells_inj_range, prod_diam, inj_diam, cost_correlation):
    parameter_list = []
    depth_start, depth_stop, depth_step = depth_range
    flow_rate_start, flow_rate_stop, flow_rate_step = flow_rate_range
    wells_prod_start, wells_prod_stop = wells_prod_range  # Assuming step is 1
    wells_inj_start, wells_inj_stop = wells_inj_range    # Assuming step is 1

    for depth in np.arange(depth_start, depth_stop, depth_step):
        for flow_rate in range(flow_rate_start, flow_rate_stop, flow_rate_step):
            for wells_prod in range(wells_prod_start, wells_prod_stop + 1):
                for wells_inj in range(wells_inj_start, wells_inj_stop + 1):
                    if wells_prod == wells_inj or wells_prod == 2 * wells_inj:
                        params = base_params.copy()
                        params.update({
                            'Production Flow Rate per Well': flow_rate,
                            'Reservoir Depth': depth,
                            'Number of Production Wells': wells_prod,
                            'Number of Injection Wells': wells_inj,
                            'Production Well Diameter': prod_diam,
                            'Injection Well Diameter': inj_diam,
                            'Well Drilling Cost Correlation': cost_correlation,
                        })
                        parameter_list.append(params)
    return parameter_list
