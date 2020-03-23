#!/usr/bin/env python3
#
# Copyright (c) 2019 Roberto Riggio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.

"""Inspect the specified module for services."""

import pkgutil


def walk_module(package):
    """Inspect the specified module for services."""

    results = {}

    pkgs = pkgutil.walk_packages(package.__path__)

    for importer, module_name, is_pkg in pkgs:

        if not is_pkg:
            continue

        # only import from subfolders of the package
        if not any(importer.path.startswith(p) for p in package.__path__):
            continue

        __import__(package.__name__ + "." + module_name)

        if not hasattr(package, module_name):
            continue

        module = getattr(package, module_name)

        if not hasattr(module, "MANIFEST"):
            continue

        manifest = getattr(module, "MANIFEST")

        if 'name' not in manifest:
            name = package.__name__ + "." + module_name + "." + module_name
            manifest['name'] = name

        if 'modules' not in manifest:
            manifest['modules'] = []

        if 'label' not in manifest:
            manifest['label'] = module_name

        if 'desc' not in manifest:
            manifest['desc'] = "No description available"

        results[manifest['name']] = manifest

    return results
