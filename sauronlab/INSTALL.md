# Sauronlab installation

You will need Python 3.9+.
For a suggested setup, see
[_new data science steps_](https://dmyersturnbull.github.io/data-science-setup).

Sauronlab is built and installed using [poetry](https://python-poetry.org).
You can use either pip or conda (both use Poetry behind the scenes):

- With conda using the [sauronlab environment](https://github.com/dmyersturnbull/sauronlab/blob/main/sauronlab-env.yml):
  `conda env create --file=https://raw.githubusercontent.com/dmyersturnbull/sauronlab/main/sauronlab-env.yml`
- `pip install git+https://github.com/dmyersturnbull/sauronlab.git/main[extras]`

The first option will create an environment called _sauronlab_.
Note that it is different from the _sauronpub_ environment file in the sauron-publication repo;
the latter is intended only for exact replication of the analyses used for the manuscript.

Run `sauronlab init` to finalize the installation.
It will walk you through and ask some questions,
generating config files under `~/.sauronlab`.
The "shire" path can be set to the location of full raw data (including video data).
If set, videos must be organized under `year/month/run.tag/`. For example, `2021/05/20200528.175151.S10/`.
For historical reasons, the videos are then under `camera/x265-crf15/x265-crf15.mkv`.
You can edit the those files for [additional configuration](#-additional-configuration).

## Jupyter setup

You may want to run `python -m ipykernel install --user --name=sauronlab`
to add the environment to Jupyter.

If you are using Windows, navigate to your Anaconda environment under
`<ANACONDA-INSTALL-DIR>/envs/sauronlab/Scripts` and run `python pywin32_postinstall.py -install`.

On Linux, you may need to install the [Rust toolchain](https://rustup.rs/) and the
[sndfile](https://en.wikipedia.org/wiki/Libsndfile) library.
It is possible for these to be needed on macOS and Windows, too.

## 📝 Technical note
Sauronlab is available on both [conda-forge](https://anaconda.org/conda-forge/sauronlab)
and [PyPi](http://pypi.org/project/sauronlab).
We generally recommend installing via pip/Poetry.
The reasons for this are described
[in this post](https://dmyersturnbull.github.io/python-infrastructure).
Briefly, conda will not detect dependency conflicts for packages that are only available on PyPi.

## 🔨 Building

To build and test locally (with MariaDB installed):

```bash
git clone https://github.com/dmyersturnbull/sauronlab.git
cd sauronlab
pip install tox
tox
```

The `tox.ini` assumes that the root MariaDB password is `root`.

## 🐛 Known issues

Sauronlab was forked from a previous package to make it usable outside of our lab. Specifically, by:

1. eliminating references to specific database rows,
2. adding a dependency-injected layer over the database,
3. enabling straightforward and reliable installation,
4. overhauling the test infrastructure using dynamic data generation, and
5. adding continuous integration and deployment with GitHub Actions.

It is officially in a pre-alpha [development state](https://semver.org/#spec-item-4).
During this refactoring, some code is experimental and poorly tested.
In general, lower-level code such as models (e.g. `WellFrame`) are reliable,
while replacement tests are being added to higher-level code.
Experimental and full untested code is marked with `status(CodeStatus.Immature)`
from [decorate-me](https://github.com/dmyersturnbull/decorate-me);
using them will trigger a warning (`ImmatureWarning`).
Such code is highly subject to change or removal.

## 🔧 Additional configuration

You can also quietly overwrite any
[resource file](https://github.com/dmyersturnbull/sauronlab/tree/main/sauronlab/resources)
internal to sauronlab by copying it to `~/.sauronlab/...`.
For example, you can copy
`https://github.com/dmyersturnbull/sauronlab/blob/main/sauronlab/resources/viz/stim_colors.json` to
`~/.sauronlab/viz/stim_colors.json` to change the default colors used to plot stimuli.
