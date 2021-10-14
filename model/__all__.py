from importlib import import_module
from inspect import isclass
from pathlib import Path
from pkgutil import iter_modules

# Iterate modules

package_dir = str(Path(__file__).resolve().parent)

for (_, module_name, _) in iter_modules([package_dir]):

    # import the module and iterate through its attributes
    module = import_module(f"model.{module_name}")
    for attribute_name in dir(module):
        attribute = getattr(module, attribute_name)

        if isclass(attribute):
            globals()[attribute_name] = attribute
