#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import aerospike
import os
import pandas as pd
import pprint
import sys


_client = None
_config = {
    'hosts': [
        ('10.140.0.10' if os.uname()[0] == 'Linux' else '104.199.207.153',
         3000)
    ]
}
_key = ('test', 'budgets', 'budget')
_meta = {
    'ttl': 86400  # seconds
}


def connect():
    try:
        global _client
        _client = aerospike.client(_config).connect()
    except Exception as e:
        print('error: {}'.format(e), file=sys.stderr)
        sys.exit(1)


def init_budgets():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    budgets = pd.read_json('{}/json/budgets.json'.format(script_dir),
                           orient='index')
    bins = budgets.loc[:, 'budget'].to_dict()

    # to float
    for adv in bins:
        bins[adv] = float(bins[adv])

    try:
        _client.put(_key, bins, meta=_meta)
    except Exception as e:
        print('error: {}'.format(e), file=sys.stderr)
        _client.close()
        sys.exit(2)


def get_budgets():
    _, _, bins = _client.get(_key)
    return bins


def set_budgets(budgets):
    _client.put(_key, budgets, _meta)


def consume(adv, budget):
    _client.increment(_key, adv, -budget)


def disconnect():
    _client.close()


if __name__ == '__main__':
    connect()
    init_budgets()
    print(get_budgets())
    consume('adv_01', 100.0)
    print(get_budgets())
    consume('adv_02', 55555.0)
    print(get_budgets())
    disconnect()
