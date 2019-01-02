# Temporary README

Tested on Void Linux 4.18.14 x64 with Qt 5.10.1, Python 3.6.6, PyQt5 5.11.3

Install olm/olm-devel from your distro's package manager,
or manually from [here](https://git.matrix.org/git/olm/about/).
Make sure Qt 5.x is installed

If no wheel is available for your platform, a working C compiler and the
Python headers are needed.

On Void Linux:

```sh
    sudo xpbs-install -S gcc python3-devel qt5 olm-devel
    sudo pip3 install harmonyqt
    harmonyqt
```
