# Valarpy setup


First, install valarpy with just `pip install valarpy`.
Note that if you are using sauronlab, you
only need to install sauronlab.

## Config file

An example connection config file:

```json
{
  "port": 3306,
  "user": "kaletest",
  "password": "kale123",
  "database": "valartest",
  "host": "127.0.0.1"
}
```

## Tunnel into Valinor

Valarpy connects to Valar through an SSH tunnel; the database is not
accessible remotely. There are two modes of connection: Valarpy can
either use an existing SSH tunnel or create its own.

Replacing *53419* with a number of your choosing, The port can’t be
*anything*. It needs to be between 1025 and 65535, and I recommend
49152–65535.

create the tunnel using:

``bash
   ssh -L 53419:localhost:3306 valinor.ucsf.edu
``

Note that after running it your shell is now on Valinor.

You will need to leave this tunnel open while connecting to Valar. As
long the terminal window connection is open, you can access valar
through your notebooks.

You can of course alias in your `~/.commonrc`. Adding these lines
will provide a `valinor-tunnel` alias:

``bash
   export valinor_tunnel_port=53419
   alias valinor-tunnel='ssh -L ${valinor_tunnel_port}:localhost:3306 valinor.ucsf.edu'
``


## Connect to Valar

You will connect to Valar via that tunnel.
An example configuration file is provided in the readme. I recommend
downloading it to `$HOME/.sauronlab/connection.json`. You’ll need
to fill in the username and password for the database connection.
Although the database users are provided for safety (no write access by default)
rather than security, do not put a username and/or password anywhere that’s web-accessible
(including GitHub).
