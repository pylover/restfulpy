# restfulpy
A tool-chain for creating restful web applications.

[![Build Status](http://img.shields.io/pypi/v/restfulpy.svg)](https://pypi.python.org/pypi/restfulpy)
[![Gitter](https://img.shields.io/gitter/room/Carrene/restfulpy.svg)](https://gitter.im/Carrene/restfulpy)
     
## Branches

### master

[![Build Status](https://travis-ci.org/Carrene/restfulpy.svg?branch=master)](https://travis-ci.org/Carrene/restfulpy)
[![Coverage Status](https://coveralls.io/repos/github/Carrene/restfulpy/badge.svg?branch=master)](https://coveralls.io/github/Carrene/restfulpy?branch=master)

### develop

[![Build Status](https://travis-ci.org/Carrene/restfulpy.svg?branch=develop)](https://travis-ci.org/Carrene/restfulpy)
[![Coverage Status](https://coveralls.io/repos/github/Carrene/restfulpy/badge.svg?branch=develop)](https://coveralls.io/github/Carrene/restfulpy?branch=develop)



## Goals:
 
- Automatically transform the SqlAlchemy models and queries into JSON with standard 
naming(camelCase).
- Http form validation based on SqlAlchemy models.
- A testing framework for REST application
- Generating the REST API documentation while the tests are passing. It helps to 
always deliver fresh API documentation.



#### Enabling the bash auto completion for restfulpy

```bash
$ echo "eval \"\$(register-python-argcomplete restfulpy)\"" >> $VIRTUAL_ENV/bin/postactivate
$ deactivate && workon restfulpy
```


## Mockup Server

A simple mockup server is available to wrap a process (normally a test runner). it helps to start an HTTP server before
the tests are started in the other environments.


Without spawning a subprocess:

```bash
$ restfulpy mockup-server
```

With a subprocess:


```bash
$ restfulpy mockup-server sleep 10
```

Also, you have to know about the server's URL: the `{url}` expression in the command will be replaced by the actual url
of the server:

This example is showing how to use the famous `curl` command as a subprocess to get the help:

```bash
$ restfulpy mockup-server curl {url}
```

More info?

```bash
$ restfulpy mockup-server -h
usage: restfulpy mockup-server [-h] [-c FILE] [-b {HOST:}PORT] [-v] ...

positional arguments:
  command               The command to run tests.

optional arguments:
  -h, --help            show this help message and exit
  -c FILE, --config-file FILE
                        List of configuration files separated by space.
                        Default: ""
  -b {HOST:}PORT, --bind {HOST:}PORT
                        Bind Address. default is 8080, A free tcp port will be
                        choosed automatically if the 0 (zero) is given
  -v, --version         Show the mockup server's version.
```

