#  Copyright 2020 Soda
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
from typing import List

from sodasql.configuration.helper import parse_int
from sodasql.scan.metric import Metric
from sodasql.scan.parse_logs import ParseLogs
from sodasql.scan.scan_column_configuration import ScanColumnConfiguration

KEY_TABLE_NAME = 'table_name'
KEY_METRICS = 'metrics'
KEY_COLUMNS = 'columns'
KEY_MINS_MAXS_LIMIT = 'mins_maxs_limit'
KEY_FREQUENT_VALUES_LIMIT = 'frequent_values_limit'
KEY_SAMPLE_PERCENTAGE = 'sample_percentage'
KEY_SAMPLE_METHOD = 'sample_method'


def ensure_metric(metrics: List[str],
                  metric: str,
                  dependent_metric: str,
                  parse_logs: ParseLogs,
                  column_name: str = None):
    if metric not in metrics:
        metrics.append(metric)
        column_message = f' on column {column_name}' if column_name else ''
        parse_logs.info(f'Added metric {metric} as dependency of {dependent_metric}{column_message}')


def is_metric_category_enabled(metrics: List[str], category: str, category_metrics: List[str]):
    if category in metrics:
        return True
    for category_metric in category_metrics:
        if category_metric in metrics:
            return True
    return False


def resolve_category(metrics: List[str],
                     category: str,
                     category_metrics: List[str],
                     parse_logs: ParseLogs,
                     column_name: str = None):
    if is_metric_category_enabled(metrics, category, category_metrics):
        if category in metrics:
            metrics.remove(category)
        for category_metric in category_metrics:
            ensure_metric(metrics, category_metric, category, parse_logs, column_name)


def resolve_metrics(metrics: List[str],
                    parse_logs: ParseLogs,
                    column_name: str = None):
    resolve_category(metrics, Metric.CATEGORY_MISSING, Metric.CATEGORY_MISSING_METRICS, parse_logs, column_name)
    resolve_category(metrics, Metric.CATEGORY_VALIDITY, Metric.CATEGORY_VALIDITY_METRICS, parse_logs, column_name)
    resolve_category(metrics, Metric.CATEGORY_DISTINCT, Metric.CATEGORY_DISTINCT_METRICS, parse_logs, column_name)

    if Metric.HISTOGRAM in metrics:
        ensure_metric(metrics, Metric.MIN, Metric.HISTOGRAM, parse_logs, column_name)
        ensure_metric(metrics, Metric.MAX, Metric.HISTOGRAM, parse_logs, column_name)

    return metrics


class ScanConfiguration:

    VALID_KEYS = [KEY_TABLE_NAME, KEY_METRICS, KEY_COLUMNS,
                  KEY_MINS_MAXS_LIMIT, KEY_FREQUENT_VALUES_LIMIT,
                  KEY_SAMPLE_PERCENTAGE, KEY_SAMPLE_METHOD]

    def __init__(self, scan_dict: dict):
        self.parse_logs: ParseLogs = ParseLogs()

        self.table_name = scan_dict.get(KEY_TABLE_NAME)
        if not self.table_name:
            self.parse_logs.error('table_name is required')

        self.metrics = resolve_metrics(scan_dict.get(KEY_METRICS, []), self.parse_logs)
        if not isinstance(self.metrics, list):
            self.parse_logs.error('metrics is not a list')
            self.metrics = []
        else:
            self.parse_logs.warning_invalid_elements(
                self.metrics,
                Metric.METRIC_TYPES,
                'Invalid metrics value')

        self.columns = {}
        columns_dict = scan_dict.get(KEY_COLUMNS, {})
        for column_name in columns_dict:
            column_dict = columns_dict[column_name]
            column_name_lower = column_name.lower()
            self.columns[column_name_lower] = ScanColumnConfiguration(column_name, column_dict, self.parse_logs)

        self.sample_percentage = scan_dict.get(KEY_SAMPLE_PERCENTAGE)
        self.sample_method = scan_dict.get(KEY_SAMPLE_METHOD, 'SYSTEM').upper()
        self.mins_maxs_limit = \
            parse_int(scan_dict, KEY_MINS_MAXS_LIMIT, self.parse_logs, 'scan configuration', 20)
        self.frequent_values_limit = \
            parse_int(scan_dict, KEY_FREQUENT_VALUES_LIMIT, self.parse_logs, 'scan configuration', 20)

        self.parse_logs.warning_invalid_elements(
            scan_dict.keys(),
            ScanConfiguration.VALID_KEYS,
            'Invalid scan configuration')

    def is_any_metric_enabled(self, column_name: str, metrics: List[str]):
        for metric in self.__get_metrics(column_name):
            if metric in metrics:
                return True
        return False

    def is_metric_enabled(self, column_name: str, metric: str):
        return metric in self.__get_metrics(column_name)

    def __get_metrics(self, column_name: str):
        metrics = self.metrics.copy()
        column_configuration = self.columns.get(column_name.lower())
        if column_configuration is not None and column_configuration.metrics is not None:
            metrics.extend(column_configuration.metrics)
        return metrics

    def get_missing(self, column_name: str):
        column_configuration = self.columns.get(column_name.lower())
        return column_configuration.missing if column_configuration else None

    def get_validity(self, column_name: str):
        column_configuration = self.columns.get(column_name.lower())
        return column_configuration.validity if column_configuration else None

    def get_validity_format(self, column):
        column_configuration = self.columns.get(column.name.lower())
        if column_configuration \
                and column_configuration.validity \
                and column_configuration.validity.format:
            return column_configuration.validity.format

    def get_mins_maxs_limit(self, column_name):
        return self.mins_maxs_limit

    def get_frequent_values_limit(self, column_name):
        return self.mins_maxs_limit

    def get_column_configuration(self, column_name: str):
        return self.columns.get(column_name.lower())