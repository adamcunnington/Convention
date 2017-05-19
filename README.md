# Convention

A naming convention is a generally agreed upon scheme for naming things. For a naming convention to be useful - beyond aesthetic organisation (although there is value in that) - it needs to be:
- Enforceable: If user entry cannot be restricted such that the convention is adhered to, the value of the convention is limited. Ideally, the convention should be enforceable in as many data entry contexts as possible (web based, file system, 3rd party desktop applications etc.)
- Configurable: Conventions are bound to change over time - if not the pattern itself, perhaps the restricted values that form part of the pattern.
- Dynamic: Perhaps different elements that make up parts of the pattern are stored in a separate system and so to remove redundancy, these should be fetched on a trigger / schedule.

These characteristics are especially vital when names are used to pass structured data between systems in the absence of dedicated fields designed to capture specific attributes. An example of this would be an [advertising campaign management system](https://www.techopedia.com/definition/30994/campaign-management-system-cms, "Techopedia: Campaign Management System") creating campaigns in an [ad server](https://en.wikipedia.org/wiki/Ad_serving, "Wiki: Ad serving"). Information may be added to the campaign name that should be parsed out at a later stage to form a segment for analytical purposes, i.e. aggregating ad serving performance metrics by a campaign objective that was added to the names of several campaigns.

Convention is a tool that attempts to meet all the objectives described above. It comprises of a web portal where administrators can manage conventions and a series of  plugins that enforce these conventions for users in different contexts.

Please note that this project is currently in development and pre-release. The below installation and configuration notes are subject to change.


***


## Installation

The following installation steps assume that you have cloned the master branch into *C:\Python Projects\Convention*:
1. [Install Python](https://www.python.org/downloads/, "Download Python"). Tested with 3.6.1 but there's no known reason why this won't work in any python build >= 2.7.
2. Create a virtual environment. If you are using Python 3.3 or later, use [pyvenv](https://docs.python.org/3/library/venv.html, "Python 3 Docs: venv"), otherwise, use [virtualenv](https://pypi.python.org/pypi/virtualenv, "PyPI: virtualenv").
3. Activate your virtual environment.
4. Change directory into *C:\Python Projects\Convention* and Install convention with:
'''
python setup.py install
'''


***


## Configuration

Convention's web portal is based on [Flask](http://flask.pocoo.org/, "Flask"). It is configured in the following way:
1. A standard config is loaded from *config.py* based on the value of the **CONVENTION_CONFIG** environment variable (must be "dev" [default] or "test"). Note that the standard configs read from the environment variables specified in *config.env*.
2. This is then overriden by the python file specified in the **CONVENTION_CONFIG_OVERRIDE_PATH** environment variable. If provided, the path must be relative to the *instance* folder. If the value is blank or an invalid file path, this step is silently ignored.


***

## Launch

Convention's web portal can be launched like any other flask application by using [flask run](http://flask.pocoo.org/docs/0.12/quickstart/, "Flask: Quickstart") but we recommend you run *convention\launch.py* as this ensures all aspects of the web application are loaded in the correct order and it will also create the database for you if it does not already exist.

Assuming you are inside *C:\Python Projects\Convention*, execute:
'''
python convention/launch.py
'''
