# Software installation

You probably want either (A) curated datasets, (B) database and analysis software, (C) raw video data, or
(D) full infrastructure for collecting your own data.

- **(A)** Some [datasets](https://osf.io/43zve/) and [systematic analysis results](https://osf.io/46p9y/)
  can be downloaded as simple flat files.
- **(B)** For complex analyses, use the [database (Valar)](https://github.com/dmyersturnbull/valar-schema)
  and [analysis software (sauronlab)](https://github.com/dmyersturnbull/sauronlab).
- **(C)** Download [raw video data](https://osf.io/wa59p/) separately.
- **(D)** Along with the hardware platform, you will need a skeleton database, the driver software (SauronX),
  and backend infrastructure.

The database stores a very large amount of data, including sensor data, data quality tags, and cheminformatics data.
Although this enables much more sophisticated analyses, it is overkill in some cases.

## Database

If you were not provided with credentials for a remote connection, you can download the database and load it as a
frozen, local copy:

1. Install [MariaDB](https://mariadb.org/) via a download or a package manager (e.g. apt, brew, or chocolatey).
2. Create a database (`create database valar`). Add a write-access user
   (grants: `SELECT`, `INSERT`, `UPDATE`, `DELETE`) and a read-only user (grant: `SELECT`).
3. Load the [full database](https://osf.io/95vpc/) by download the .sql.gz file and loading it.
   (Either pipe from `zcat` or deflate it and run `mysql --user=root --database=valar -e 'source valar-20210301.sql'`.)

## Sauronlab

Refer to the [sauronlab](https://github.com/dmyersturnbull/sauronlab) readme for installation instructions.

## SauronX

SauronX is the driver software for Saurons.
See the [SauronX installation instructions](https://github.com/dmyersturnbull/sauronx/blob/main/INSTALL.md)
for more information.

## Backend infrastructure

The backend infrastructure consists two primary components:

- The code that handles data insertion, feature calculation, etc.
- The website ([valinor](https://github.com/dmyersturnbull/valar-website))

Installation instructions for the insertion code can be found under
[valar-dagger](https://github.com/dmyersturnbull/valar-dagger).
