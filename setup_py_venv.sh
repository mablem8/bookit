#!/bin/bash
#
# setup_py_venv.sh
# A bash script that sets up a Python 3 virtual environment
#
# Usage: ./setup_py_venv.sh
#
# Written by Bradley Denby
# Other contributors: None
#
# See the top-level LICENSE file for the license.

python3 -m venv p3-env
source p3-env/bin/activate
python3 -m pip install wheel==0.36.1
python3 -m pip install Pillow==8.0.0
python3 -m pip install fpdf2==2.1.0
python3 -m pip install beautifulsoup4==4.9.3
python3 -m pip install requests==2.25.0
deactivate
