<!-- control tracker documentation master file, created by
sphinx-quickstart on Wed Oct 26 09:44:19 2022.
You can adapt this file completely to your liking, but it should at least
contain the root `toctree` directive. -->
# Welcome to control tracker’s documentation!

# Installation

1. Create a folder to hold everything.
```shell
mkdir ControlsTracker
cd ControlsTracker
```

2. Clone the git repository.
```shell
git clone https://github.com/landowark/control_tracker.git .
```

3. Create virtual environment and install required python packages.
```shell
conda create --name <env> --file requirements.txt
```

4. Activate virtual environment.
```shell
conda activate <env>.
```

5. Install refseq_masher
```shell
pip install refseq_masher
```
(For the life of me I could not get this to work with conda.)


6. Initialize the sqlite3 database.
```shell
alembic upgrade head
```

7. Edit 'config_dummy.yml' and save as 'config.yml'. You might have to get it from me.

8. Create control types in the database.
```shell
python controls DBinit
```

# Usage.

Note: All commands below will have to be executed in the folder and prepended with "python "

## controls

```shell
python controls [OPTIONS] COMMAND [ARGS]...
```

### Options


### -v(, --verbose()
Set logging level to DEBUG if true.


### -c(, --config( <config>)
Path to config.yml. If blank defaults to first found of ~/.config/controls/config.yml, ~/.controls/config.yml or controls/config.yml

### DBinit

```shell
python controls DBinit [OPTIONS]
```

### parse

```shell
python controls parse [OPTIONS]
```

### Options


### -s(, --storage( <storage>)
Folder for storage of fastq files.


### --mode( <mode>)
**Required**


* **Options**

    contains | matches


### report

```shell
python controls report [OPTIONS]
```

### Options


### -o(, --output_dir( <output_dir>)
Folder for storage of reports.

# Configuration file.

This file stores the configuration that will be used by the program and must be filled in by the user.
Fill in values before the ‘#’ in config_dummy.yml and save as config.yml in the same folder.

```yaml
# custom join statement defined in setup.__init__ 
irida:
  project_number: #: Project id assigned by irida
  project_name: #: Project name assigned by irida
  username: #: Username for irida permissions
  password: #: Password for irida permissions
  storage: #: Location to store irida shortcuts (only used if not overridden in command line options)
folder:
  output: #: Where xlsx and html output files from reports will be stored.
  old_db_path: #: Location of old database export file for retrieving dates. Not necessary if date in sample name.
control_types: #: Key:value pairs where key is name of the control type and value is a list of targets.
  #: e.g. ATCC49226: ["Neisseria"]
ct_type_regexes: #: list of regex patterns to pull out control types.
```
