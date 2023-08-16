## Installation of bidsme

Since version `1.4.0` bidsme can be installed using pip.
It is the best option if you don't plan to contribute to `bidsme`
developmnent.

For advanced usage, and development, you can install bidsme
manually (with or without pip).

I will suggest to install `bidsme` within it's own virtual
environment (see below).

### Automatic installation using pip (not editable)

To install `bidsme` using `pip` you just need to write in terminal:
```bash
pip install git+https://gitlab.uliege.be/CyclotronResearchCentre/Public/bidstools/bidsme/bidsme.git
```

It should install `bidsme` and nessesary dependencies in the local
python3 library.

Once installed, you should be able to run `bidsme` from terminal:
```bash
bidsme --help
```

or from `iPthon3`/`notebook`:
```python
import bidsme
bidsme.init()
```

### Manual installation (editable, for experts)

To install bidsme manually, you need first clone bidsme repository:
```bash
cd <installation dir>
git clone https://gitlab.uliege.be/CyclotronResearchCentre/Public/bidstools/bidsme/bidsme.git
```

Once repository is cloned, you can add paths to python paths using `pip -e`:
```bash
pip install -e <installation dir>/bidsme
```
In this case, pip will automatically install needed dependancies,
also it will be aviable to be imported in python3 console or notebook:
```python
import bidsme
bidsme.init()
```

Or just run bidsme directly:
```bash
python3 <installation dir>/bidsme.py --help
```
In this case you need to install the dependencies (see requirements.txt file).

## Using virtual environments and kernels

`bidsme` will require the installation of some additional python packages, some of them
are very common, like `pandas`, and likely already present in your installation of
python, others are less common.

In order to keep python installation clean, usage of virtual environments and/or kernels
are suggested.

If you are using [virtual environment](https://docs.python.org/3/library/venv.html) and/or [(Ana)conda](https://anaconda.org/), then creating a new envoronment is
straightforward, in terminal you just need to:
**[venv](https://docs.python.org/3/tutorial/venv.html)**:
``` 
python3 -m venv bidsme_env
source bidsme_env/bin/activate
```  

**[Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)**:
```
conda create --name bidsme_env
conda activate bidsme_env
```

In order to deactivate (return to your default) environment, you just need
`deactivate` with venv or `conda deactivate` in conda.

Once the environment is activated you need to install the kernel --
a library that will link iPython/jupyter interface with environment.

Still within the terminal, and active environment, do:
```
pip install ipykernel
python -m ipykernel install --user --name bidsme_env --display-name "bidsme_env (Python)"
```

The first line will install the kernel package, and second will create a new kernel
with internal name `bidsme_env` and displayed name `Python (bidsme_env)`.
For more instructions and details, you can refer to the
[Kernel instructions](https://ipython.readthedocs.io/en/latest/install/kernel_install.html)

Once kernel is installed, you can open a new jupyter(-lab) notebook, and check if
the new kernel of name `Python (bidsme_env)` is available.

This way all necessary packages will be installed in dedicated virtual environment
and will not create conflicts with your other python projects.
