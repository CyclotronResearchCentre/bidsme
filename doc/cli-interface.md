# The bidsme CLI interface



If the installation of the bidsme was performed using `pip` (see [instructions](../INSTALLATION.md)), then the command line interface `bidsme` and `bidsme-pdb` should be available in the terminal.
The two interfaces are identical except the second one executes within a standard Python3 debugger [pdb](https://docs.python.org/3/library/pdb.html).

If `bidsme` was installed manually, then the same interface can be achieved by calling `main.py:main` function.

## The main interface

```bash
usage: bidsme [-h] [-c conf.yaml] [--conf-save] [-v]  subcommand
```

The main interface `bidsme` require a sub-command, corresponding to one of the bidsification step:

 - `prepare`, to prepare dataset
 - `process`, to process dataset
 - `bidsify`, to bidsify dataset
 - `map`, to create bidsmap

For example,
```bash
bidsme bidsify <options>
```
will execute bidsification step.

Some general optional parameter can be passed **before** the command:
  
 - `-h` prints help for main interface
 - `-v` prints the version of program and version of supported BIDS
 - `-c`, '--configuration` with path to the configuration yaml file allow to retrieve the saved parameters
 - `--conf-save` will save current command-line parameters into configuration file 

## Sub-command interface

All sub-commands will require two positional arguments:

 - `source` -- path to dataset on which subcommand must be executed
 - `destination` -- path where the results of the subcommand will be written

For the `prepare` subcommand, source is the raw dataset and destination will be prepared dataset.
For the `process` subcommand, source and destination is prepared dataset.
For all other subcommands the source is prepared dataset, and destination is bidsified dataset.

All subcommands will have common parameters, described below.

### Logging options
Logging options, corresponding to the *logging* section of configuration file:
 *  `-q`, `--quiet` suppress the standard output, useful for running in the script
 * `--level` sets the message verbosity of the log output, from very verbose *DEBUG*, to showing only critical message *CRITICAL*
 * `--formatter` sets the log line format message 

### Plugin options
Plug-in options, corresponding to the *plugins* section of configuration file. They affect only the
relevant commands: 
 * `--plugin` sets the path to the plugin file
 * `-o Name=Value` sets the options passed to `InitEP` funcion of the plugin

### Subject and session selection options
Subject and session selection, corresponding to the *selection* section of the configuration file
 * `--participants` corresponds to the space separated list of participants to process. Listed participants are retrieved after the bidsification, with `sub-` prefix
 * `--skip-in-tsv` is a switch that allows to skip participants, if already present in the specified destination
 * `--skip-existing` is a switch that allows to skip participants, if a corresponding folder already exists in the specified destination
 * `--skip-existing-sessions` is a switch that allows to skip participants, if a corresponding session already exists in the specificied destination 

### General options
General options, non existing in configuration file:
 * `--dry-run`, allows to run commands in simulation mode, without writing any outputs outside of the logs. The non-writing is not garanteed in the plugins, user must ensure himself that nothing is written in plugin in dry mode.


The full list of commands parameters can be seen using the `-h` option:
`bidsme.py [command] -h`.
