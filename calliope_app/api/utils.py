"""
This module contains support functions and libraries used in views and tasks.
"""

import json
import logging
import os
import shutil
from datetime import datetime
from itertools import permutations

import yaml
import pandas as pd
import numpy as np
from django.db.models import Func, Value
from django.utils.timezone import make_aware


CALLIOPE = 18
logging.addLevelName(CALLIOPE, "CALLIOPE")
logger = logging.getLogger("calliope")


def get_model_logger(log_file):
    """
    Get logger for logging model run info or errors

    :param log_file:
    :return: logger
    """
    logging.basicConfig(level=logging.INFO,
                        format="[%(asctime)s] %(levelname)s: %(message)s")
    if logger.handlers:
        logger.removeHandler(logger.handlers[0])

    file_handler = logging.FileHandler(log_file)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s<br>",
        datefmt="%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.setLevel(CALLIOPE)

    return logger


def dateformats():
    """
    Yield common combinations of valid datetime formats.
    """

    years = ("%Y", "%y",)
    months = ("%m", "%b", "%B",)
    days = ("%d",)
    times = (
        "%H:%M", "%H:%M:%S", "%I:%M%p", "%I:%M:%S%p",
        "%I:%M %p", "%I:%M:%S %p", "%I%p")

    for year in years:
        for month in months:
            for day in days:
                date_orders = ((year, month, day), (month, day, year),
                               (day, month, year), (month, day), (day, month))
                for args in date_orders:
                    for sep in (" ", "/", "-"):
                        date = sep.join(args)
                        for time in times:
                            for combo in permutations([date, time]):
                                yield " ".join(combo).strip()


def get_date_format(string):
    """
    Detect datetime.strptime format or None from a string.
    from http://code.activestate.com/recipes/578245-flexible-datetime-parsing/
    """

    for fmt in dateformats():
        try:
            datetime.strptime(string, fmt)
            return fmt
        except ValueError:
            pass

    return None


def zip_folder(path, keep_folder=True):
    """
    Zip contents of folder

    Parameters
    ----------
    path : str
        folder path to be zipped
    """
    zip_file = path + ".zip"
    if not os.path.exists(zip_file):
        root_dir = os.path.dirname(path)
        base_dir = "./" + os.path.basename(path)
        shutil.make_archive(path, "zip", root_dir, base_dir=base_dir)

    if not keep_folder:
        shutil.rmtree(path)

    return zip_file


def dictfetchall(cursor):
    """
    Return all rows from a cursor as a dict
    """

    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def list_to_yaml(table_list, filename):
    """
    Convert a list of strings to YAML file format
    """

    X = [x[0].split('||') for x in table_list]
    timeseries = [x[1] for x in table_list]
    d = {}
    for index in range(len(X)):
        path = X[index]
        current_level = d
        for i, part in enumerate(path):
            if i < (len(path) - 1):
                if i == (len(path) - 2):
                    if timeseries[index] is True:
                        parameter = path[i]
                        technology = path[i - 2]
                        if (i - 4 > 0):
                            location = path[i - 4]
                            current_level[part] = \
                                "file={}--{}--{}.csv:value".format(
                                    location, technology, parameter)
                        else:
                            current_level[part] = \
                                "file={}--{}.csv:value".format(
                                    technology, parameter)
                    elif path[i + 1] == "":
                        current_level[part] = None
                    elif path[i + 1] == 'True':
                        current_level[part] = True
                    elif path[i + 1] == 'False':
                        current_level[part] = False
                    else:
                        try:
                            string = path[i + 1].replace(", ", ",")
                            for char in ['\'', '“', '”', '‘', '’']:
                                string = string.replace(char, '\"')
                            current_level[part] = json.loads(string)
                        except Exception:
                            try:
                                current_level[part] = float(path[i + 1])
                            except ValueError:
                                current_level[part] = path[i + 1]
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
    with open(filename, 'w') as outfile:
        yaml.dump(d, outfile, default_flow_style=False)
        return True


def get_cols_from_csv(filename):
    """
    Read the columns from a csv
    """

    df = pd.read_csv(filename)
    return df.columns


def load_timeseries_from_csv(filename, t_index, v_index, has_header=False):
    """
    Build a timeseries as a pandas dataframe from a csv file
    """

    t_index = int(t_index)
    v_index = int(v_index)
    date_format = None  # just use pd.to_datetime if None
    df = pd.DataFrame()

    # Cache date format for large files (sample 20th row):
    if filename.size > 2e6:  # 2 MB
        read_df = pd.read_csv(filename.path, header=None, skiprows=20,
                              usecols=[t_index, v_index],
                              skipinitialspace=True, nrows=1)
        test_date = read_df.iloc[0, t_index]
        date_format = get_date_format(test_date)

    # Load Full Data
    skiprows = 0
    if has_header:
        skiprows = 1
    read_df = pd.read_csv(filename.path, header=None, skiprows=skiprows,
                          usecols=[t_index, v_index],
                          skipinitialspace=True, chunksize=100000)

    # Convert to Timestamps
    for chunk_df in read_df:
        if date_format is None:
            # Slow: We didn't find the strptime format:
            chunk_dates = pd.to_datetime(chunk_df.loc[:, t_index])
        else:
            # Fast: Try using strptime
            try:
                chunk_dates = chunk_df[[t_index]].astype(str).ix[:, 0].apply(
                    lambda x: make_aware(datetime.strptime(x, date_format)))
            except ValueError:
                chunk_dates = pd.to_datetime(chunk_df.loc[:, t_index])

            chunk_df.iloc[:, t_index] = chunk_dates

        # Filter out NaN values
        chunk_df = chunk_df[pd.notnull(chunk_df)]
        chunk_df = chunk_df[pd.notnull(chunk_df)]

        df = df.append(chunk_df)

    # Clean
    df = df.set_index(t_index)
    df.index.name = 'datetime'
    df.columns = ['value']

    # Resample
    df = hourly_timeseries(df)

    return df


def hourly_timeseries(df):
    """
    Set the timestamp and resample to hourly in a pandas dataframe
    """

    if type(df.index) is not pd.core.indexes.datetimes.DatetimeIndex:
        df.index = pd.to_datetime(df.index, utc=True)

    df = df.resample(rule='h').mean()
    df[np.isnan(df.value)] = 0
    return df


def pad_timeseries(df, start, end):
    """
    Add padding to a pandas dataframe timeseries

    start = '2019-01-01 00:00'
    end = '2019-01-02 00:00'
    """
    idx = pd.date_range(start=start, end=end, freq='h')
    ts = pd.DataFrame(index=idx)
    df = ts.join(df).fillna(0).reset_index()
    return df


class DateTrunc(Func):
    """
    To support using DATE_TRUNC('text', "field") in SQL

    Example::

        order_totals = (orders
            .annotate(
                period=DateTrunc('month', 'date_placed'),
            )
            .values("period")  # Needs to be in between for a correct GROUP_BY
            .order_by('period')
            .annotate(
                order_count=Count('id'),
                shipping_excl_tax=Sum('shipping_excl_tax'),
                shipping_incl_tax=Sum('shipping_incl_tax'),
            ))

    SQL DateTrunc function (for grouping by day, hour, month, etc.):
    https://gist.github.com/vdboor/f3ebe5e20c0882d39053
    """
    function = 'DATE_TRUNC'

    def __init__(self, trunc_type, field_expression, **extra):
        super(DateTrunc, self).__init__(
            Value(trunc_type), field_expression, **extra)
