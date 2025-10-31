#
# Copyright 2021 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
Copyright (C) 2005-2019 Splunk Inc. All Rights Reserved.

Commonly used design partten for python user, includes:
  - singleton (Decorator function used to build singleton)
"""
import warnings
import traceback
from functools import wraps


def singleton(class_):
    """
    Singleton decoorator function.
    """
    warnings.warn(
        "This function is deprecated. "
        "Please see https://github.com/splunk/addonfactory-ta-library-python/issues/38",
        DeprecationWarning,
        stacklevel=2,
    )
    instances = {}

    @wraps(class_)
    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance


class Singleton(type):
    """
    Singleton meta class
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
            print(cls)
        return cls._instan


def catch_all(logger, reraise=True):
    def catch_all_call(func):
        def __call__(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                logger.error(
                    "Failed to execute function=%s, error=%s",
                    func.__name__,
                    traceback.format_exc(),
                )
                if reraise:
                    raise

        return __call__

    return catch_all_call


class SingletonMeta(type):
    def __init__(cls, name, bases, attrs):
        super(SingletonMeta, cls).__init__(name, bases, attrs)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instance
