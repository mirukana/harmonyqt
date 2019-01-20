# harmonyqt

Experimental Qt5 Matrix client with end-to-end encryption support.  
Work in progress, expect problems.


## Installation

Only tested on Void Linux glibc 4.19.13\_1 x86\_64 with Qt 5.11.3\_3,
Python 3.6.8\_1, PyQt5 5.11.3 for now.

Install the **olm** headers from your distro's package manager,
or manually from [here](https://git.matrix.org/git/olm/about/).  
Make sure Qt5, including webengine is installed.

A working C compiler and the Python headers are needed
to build **python\_olm\_harmonyqt** for encryption support.

On Void Linux:

```sh
    sudo xpbs-install -S qt5 qt5-webengine python3-pip python3-devel gcc olm-devel
    pip3 --no-cache-dir install --user --upgrade cffi pycparser
    pip3 --no-cache-dir install --user --upgrade harmonyqt
    harmonyqt
```


## Common problems

If you get a "command not found" error, make sure *$HOME/.local/bin* is added
to your `$PATH`; or launch using the absolute path:

```sh
    python3 ~/.local/bin/harmonyqt
```

If you get a crash on startup due to olm/encryption,  
e.g. `ImportError: cannot import name 'OutboundGroupSession'`:

- Uninstall any conflicting pip package:  
  `pip3 uninstall python_olm olm`  
  `pip3 uninstall olm`

- Try to reinstall **python\_olm\_harmonyqt**:  
  `pip3 uninstall python_olm_harmonyqt`  
  `pip3 --no-cache-dir install --user --upgrade python_olm_harmonyqt`
