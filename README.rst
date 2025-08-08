************************
affinitic.smartweb.luigi
************************

This package is use to migrate content from a plone site to a smartweb site.

The migration has 3 step :

1. Export content from old site with collective.exportimport

2. Process the exported data with this package

3. Import the data in the new smartweb site, the package affinitic.smartweb must be instal

==============
How to install
==============

1. Create a environement :
  ``pyenv virtualenv 3.8 affinitic.smartweb.luigi``

2. Activate the environement :
  ``pyenv activate affinitic.smartweb.luigi``

3. Link bin folder:
  ``ln -s ~/.pyenv/versions/affinitic.smartweb.luigi/bin ./bin``

4. Install dependencies:
  ``bin/pip install -r requirements.txt``

=============
How to use it
=============
----
Data
----
Put your json in `data/project_name/in`. 

-----------
Config file
-----------
Add a ``project_name.cfg`` at the root. Inside it add this :
::
  [HandleDocument]
  url_absolute=https://www.project_name.be

Add the original url (the one that appear in exported json file) to be fix during the process

--------
Makefile
--------
Then add a command in Makefile to start.
ex:
::
  run-project-name :
	LUIGI_CONFIG_PATH=./project_name.cfg bin/luigi --module src.main Start --path "./data/project_name" --local-scheduler 

------
Launch
------
``make run-project-name``

If it must be relauch, delete the `out` and/or `temp` folder
