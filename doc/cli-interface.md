## <a name="interface"></a> The BIDSme CLI interface

All interactions with BIDSme occurs from command-line interface, by a master script [`bidsme.py`](https://gitlab.uliege.be/CyclotronResearchCentre/Public/bidstools/bidsme/bidsme/-/blob/tutorial/bidsme/bidsme.py).

This script accepts a small set of parameters and commands 

- `prepare`, to prepare dataset
- `process`, to process dataset
- `bidsify`, to bidsify dataset
- `map`, to create bidsmap

Outside the standard `-h`, `-v` options, to access help and retrieve the version of the toolkit, `bidsme` accepts 
the option `-c', '--configuration` that retrieves the path to the configuration file. 
This file is searched following the precedence order: current directory, user-standard directory and 
bids code directory (when available).

The `--conf-save` switch saves the current configuration (affected by command-line
options) in the given location. It is useful to run this option once to update the configuration.

> N.B. both `-c` and `--conf-save` must be given **before** the command 'prepare', 'process' or 'bidsify'.

The individual commands accept common and individual arguments. 
In what follows, only common arguments are described, whereby individual ones are 
described in corresponding sections.

- Logging options, corresponding to the *logging* section of configuration file:
    *  `-q`, `--quiet` suppress the standard output, useful for running in the script
    * `--level` sets the message verbosity of the log output, from very verbose *DEBUG*
    to showing only critical message *CRITICAL*
    * `--formatter` sets the log line format message 
- Plug-in options, corresponding to the *plugins* section of configuration file. They affect only the
relevant commands: 
    * `--plugin` sets the path to the plugin file
    * `-o Name=Value` sets the options passed to plugin
- Subject and session selection, corresponding to the *selection* section of the configuration file
    * `--participants` corresponds to the space separated list of participants to process. Listed participants
    are retrieved after the bidsification, with `sub-` prefix
    * `--skip-in-tsv` is a switch that allows to skip participants, if already present in the specified destination
    * `--skip-existing` is a switch that allows to skip participants, if a corresponding folder already exists
    in the specified destination
    * `--skip-existing-sessions` is a swtich that allows to skip participants, if a corresponding session already exists in the specificied destination 
- General options, non existing in configuration file:
    * `--dry-run`, allows to run commands in simulation mode, without writing any outputs outside of the
    logs

The full list of commands parameters can be seen using the `-h` option:
`bidsme.py [command] -h`.
If a configuration file is set, then the default values shown when calling ......... correspond to the configuration file
parameters.
