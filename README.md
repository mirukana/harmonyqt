# Temporary README

Tested on Void Linux glibc 4.19.13\_1 x86\_64 with Qt 5.11.3\_3,
Python 3.6.8\_1, PyQt5 5.11.3

Install olm/olm-devel from your distro's package manager,
or manually from [here](https://git.matrix.org/git/olm/about/).
Make sure Qt5 is installed.

If no wheel is available for your platform, a working C compiler and the
Python headers are needed.

On Void Linux (`umask` to avoid any permission problems with `pip3`):

```sh
    sudo xpbs-install -S qt5 python3-pip gcc python3-devel olm-devel
    pip3 --no-cache-dir install --user --upgrade harmonyqt
    harmonyqt
```

If you get a "command not found" error, make sure *$HOME/.local/bin* is added
to your `$PATH`; or launch using the absolute path:

```sh
    python3 ~/.local/bin/harmonyqt
```
