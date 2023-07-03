# Legacy Sauron-related code archive

This page contains documentation for the software as a whole.
More detailed documentation can be found for the respective projects.

**For installation** of various subsystems, please see the
[installation overview](https://github.com/dmyersturnbull/sauron-publication/blob/main/DOCUMENTATION/INSTALL.md).

## Overview of projects

**TIP:** Open the diagram in another window (side-by-side). It contains embedded links, which cannot be rendered here.

<img src="https://raw.githubusercontent.com/chelsell/sauron-legacy/main/projects.svg" width="45%" height="45%" />

## Flow of data

<img src="https://raw.githubusercontent.com/chelsell/sauron-legacy/main/flow.svg" width="45%" height="45%" />

## Component glossary

#### Sauron (instrument)

Behavioral phenotyping instrument

#### SauronX (drivers)

High-level drivers for Sauron (Python and C++)

#### Valar (database)

Database (MariaDB)

#### Valinor (website)

Website (Scala)

#### lorien

Video feature analysis code (Scala)

#### Spinnaker SDK

External library from Point Grey to control Grasshopper 3 camera (C++)

#### Firmata

Firmware used on the Arduino for SauronX (C++)

#### valar-dagger

Scheduler for backend jobs like data insertion and database maintenance (Python)

#### Slack

Valar-dagger can use [Slack](https://slack.com/) for user interaction

#### valar-backend

Collection of backend software, mostly for handling incoming data from valar-dagger (Scala)

#### valar-importer

Subproject of valar-backend to handle data post-processing and insertion (Scala)

#### valar-insertion

Small subproject of valar-backend that provides interfaces for database transactions (Scala)

#### valar-params

Subproject of valar-backend that handles template assays, batteries, and plate layouts (Scala)

#### valar-core

Subproject of valar-backend that provides a stateless database view via [Slick](https://scala-slick.org/) (Scala)

#### Gale (language)

Language for describing behavioral assays (stimuli over time)

#### gale (interpreter)

Interpreter for Gale in Parboiled2 (Scala)

#### pippin-grammars

Grammars and interpreters for parameterization of plate layouts (Scala)

#### valarpy

Stateful ORM for Valar (Python)

#### sauronlab

Analysis package (Python)

#### typed-dfs

Library for Pandas DataFrames with specifications, extensively used by sauronlab (Python)

#### chemserve

Thin wrapper and isolation library for rdkit (Python)

#### pocketutils

Collection of extensively used utilities (Python)
