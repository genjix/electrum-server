How to run your own Electrum server
===================================

Abstract
--------

This document is an easy to follow guide to installing and running your own
Electrum server on Linux. It is structured as a series of steps you need to
follow, ordered in the most logical way. The next two sections describe some
conventions we use in this document and hardware, software and expertise
requirements.

The most up-to date version of this document is available at:

    https://github.com/spesmilo/electrum-server/blob/master/HOWTO.md

Conventions
-----------

In this document, lines starting with a hash sign (#) or a dollar sign ($)
contain commands. Commands starting with a hash should be run as root,
commands starting with a dollar should be run as a normal user (in this
document, we assume that user is called 'bitcoin'). We also assume the
bitcoin user has sudo rights, so we use '$ sudo command' when we need to.

Strings that are surrounded by "lower than" and "greater than" ( < and > )
should be replaced by the user with something appropriate. For example,
<password> should be replaced by a user chosen password. Do not confuse this
notation with shell redirection ('command < file' or 'command > file')!

Lines that lack hash or dollar signs are pastes from config files. They
should be copied verbatim or adapted, without the indentation tab.

Prerequisites
-------------

**Expertise.** You should be familiar with Linux command line and
standard Linux commands. You should have basic understanding of git,
Python packages. You should have knowledge about how to install and
configure software on your Linux distribution. You should be able to
add commands to your distribution's startup scripts. If one of the
commands included in this document is not available or does not
perform the operation described here, you are expected to fix the
issue so you can continue following this howto.

**Software.** A recent Linux 64-bit distribution with the following software
installed: `python`, `easy_install`, `git`, standard C/C++
build chain. You will need root access in order to install other software or
Python libraries. 

**Hardware.** The lightest setup is a pruning server with diskspace 
requirements well under 1 GB growing very moderately and less taxing 
on I/O and CPU once it's up and running. However note that you also need
to run bitcoind and keep a copy of the full blockchain, which is roughly
9 GB in April 2013. If you have less than 2 GB of RAM make sure you limit
bitcoind to 8 concurrent connections. If you have more ressources to 
spare you can run the server with a higher limit of historic transactions 
per address. CPU speed is also important, mostly for the initial block 
chain import, but also if you plan to run a public Electrum server, which 
could serve tens of concurrent requests. Any multi-core x86 CPU ~2009 or
newer other than Atom should do for good performance.

Instructions
------------

### Step 1. Create a user for running bitcoind and Electrum server

This step is optional, but for better security and resource separation I
suggest you create a separate user just for running `bitcoind` and Electrum.
We will also use the `~/bin` directory to keep locally installed files
(others might want to use `/usr/local/bin` instead). We will download source
code files to the `~/src` directory.

    # sudo adduser bitcoin
    # su - bitcoin
    $ mkdir ~/bin ~/src
    $ echo $PATH

If you don't see `/home/bitcoin/bin` in the output, you should add this line
to your `.bashrc`, `.profile` or `.bash_profile`, then logout and relogin:

    PATH="$HOME/bin:$PATH"

### Step 2. Download and install Electrum

We will download the latest git snapshot for Electrum and 'install' it in
our ~/bin directory:

    $ mkdir -p ~/src/electrum
    $ cd ~/src/electrum
    $ git clone https://github.com/spesmilo/electrum-server.git server
    $ chmod +x ~/src/electrum/server/server.py
    $ ln -s ~/src/electrum/server/server.py ~/bin/electrum-server

### Step 3. Download Bitcoind stable from git & patch it

In order for the latest versions of Electrum to work properly we will need to use 
bitcoind 0.8.1 stable or higher. It can be downloaded from github and 
it needs to be patched with an electrum specific patch.

    $ cd ~/src && wget http://sourceforge.net/projects/bitcoin/files/Bitcoin/bitcoin-0.8.1/bitcoin-0.8.1-linux.tar.gz
    $ tar xfz bitcoin-0.8.1-linux.tar.gz
    $ cd bitcoin-0.8.1-linux/src
    $ patch -p1 < ~/src/electrum/server/patch/patch
    $ cd src
    $ make USE_UPNP= -f makefile.unix
    $ ln -s ~/src/bitcoin-0.8.1-linux/src/src/bitcoind ~/bin/bitcoind

### Step 4. Configure and start bitcoind

In order to allow Electrum to "talk" to `bitcoind`, we need to set up a RPC
username and password for `bitcoind`. We will then start `bitcoind` and
wait for it to complete downloading the blockchain.

    $ mkdir ~/.bitcoin
    $ $EDITOR ~/.bitcoin/bitcoin.conf

Write this in `bitcoin.conf`:

    rpcuser=<rpc-username>
    rpcpassword=<rpc-password>
    daemon=1

Restart `bitcoind`:

    $ bitcoind

Allow some time to pass, so `bitcoind` connects to the network and starts
downloading blocks. You can check its progress by running:

    $ bitcoind getinfo

You should also set up your system to automatically start bitcoind at boot
time, running as the 'bitcoin' user. Check your system documentation to
find out the best way to do this.

### Step 5. Install Electrum dependencies

Electrum server depends on various standard Python libraries. These will be
already installed on your distribution, or can be installed with your
package manager. Electrum also depends on two Python libraries which we will
need to install "by hand": `JSONRPClib`.

    $ sudo easy_install jsonrpclib
    $ sudo apt-get install python-openssl

### Step 6. Install leveldb

    $ sudo apt-get install python-leveldb
 
See the steps in README.leveldb for further details, especially if your system
doesn't have the python-leveldb package.

### Step 7. Select your limit

Electrum server uses leveldb to store transactions. You can choose
how many spent transactions per address you want to store on the server.
The default is 100, but there are also servers with 1000 or even 10000.
Very few addresses have more than 10000 transactions. A limit this high
can be considered to be equivalent to a "full" server. Full servers previously
used abe to store the blockchain. The use of abe for electrum servers is now
deprecated.

The pruning server uses leveldb and keeps a smaller and
faster database by pruning spent transactions. It's a lot quicker to get up
and running and requires less maintenance and diskspace than abe.

The section in the configuration file looks like this:

     [leveldb]
     path = /path/to/your/database
     # for each address, history will be pruned if it is longer than this limit
     pruning_limit = 100

### Step 8. Import blockchain into the database or download it

As of April 2013 it takes between 6-24 hours to import 230k of blocks, depending
on CPU speed, I/O speed and selected pruning limit.

It's considerably faster to index in memory. You can use /dev/shm or indexing in RAM
or create a tmpfs which will also use swap if you run out of memory:

    $ sudo mount -t tmpfs -o rw,nodev,nosuid,noatime,size=6000M,mode=0777 none /tmpfs

At limit 100 the database comes to 2,6 GB with 230k blocks and takes roughly 6h to import in /dev/shm.
At limit 1000 the database comes to 3,0 GB with 230k blocks and takes roughly 10h to import in /dev/shm.
At limit 10000 the database comes to 3,5 GB with 230k blocks and takes roughly 24h to import in /dev/shm.

Alternatively you can fetch a pre-processed leveldb from the net

You can fetch recent copies of electrum leveldb databases and further instructions 
from the Electrum full archival server foundry at:
http://electrum-foundry.no-ip.org/ 

### Step 9. Configure Electrum server

Electrum reads a config file (/etc/electrum.conf) when starting up. This
file includes the database setup, bitcoind RPC setup, and a few other
options.

    $ sudo cp ~/src/electrum/server/electrum.conf.sample /etc/electrum.conf
    $ sudo $EDITOR /etc/electrum.conf

Go through the sample config options and set them to your liking.
If you intend to run the server publicly have a look at README-IRC.md 

If you're looking to run SSL / HTTPS you need to generate a self-signed certificate
using openssl. Otherwise you can just comment out the SSL / HTTPS ports and run 
without.

### Step 10. (Finally!) Run Electrum server

The magic moment has come: you can now start your Electrum server:

    $ electrum-server

You should see this on the screen:

    starting Electrum server
    cache: yes

If you want to stop Electrum server, open another shell and run:

    $ electrum-server stop

You should also take a look at the 'start' and 'stop' scripts in
`~/src/electrum/server`. You can use them as a starting point to create a
init script for your system.

### Step 11. Test the Electrum server

We will assume you have a working Electrum client, a wallet and some
transactions history. You should start the client and click on the green
checkmark (last button on the right of the status bar) to open the Server
selection window. If your server is public, you should see it in the list
and you can select it. If you server is private, you need to enter its IP
or hostname and the port. Press Ok, the client will disconnect from the
current server and connect to your new Electrum server. You should see your
addresses and transactions history. You can see the number of blocks and
response time in the Server selection window. You should send/receive some
bitcoins to confirm that everything is working properly.

### Step 12. Join us on IRC, subscribe to the server thread

Say hi to the dev crew, other server operators and fans on 
irc.freenode.net #electrum and we'll try to congratulate you
on supporting the community by running an Electrum node

If you're operating a public Electrum server please subscribe
to or regulary check the following thread:
https://bitcointalk.org/index.php?topic=85475.0
It'll contain announcements about important updates to Electrum
server required for a smooth user experience.
