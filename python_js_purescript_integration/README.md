Check that the xcode command line tools are installed:
```shell
xcode-select -p
```

Now do some maintenance with brew

```shell
brew update
brew install pyenv
brew install cmake openssl readline sqlite3 xz zlib
```

pyenv is used as a kind of _switcher_ to help with having multiple revisions of Python installed.
```shell
# See what revisions are available to install
pyenv install --list
pyenv install 3.9.4
```
This will install it to a user-specific path like this one:
```shell
/Users/phrrngtn/.pyenv/versions/3.9.4
```
In the interest of making the stuff copy-and-pastable, I will write the path using tilde(~) and assume that the shell you are using expands that out to your home directory. In any case, the commands reproduced here are intended to be illustrative only. You may have to run additional ones or some variants. In summary, we need these toolchains:
- Xcode
- brew
- pyenv
- virtualenv
- pip

First thing we do is upgrade the pip installation itself
```shell
~/.pyenv/versions/3.9.4/bin/python3.9 -m pip install --upgrade pip
```
Now virtualenv
```shell
~/.pyenv/versions/3.9.4/bin/pip install virtualenv
```

now we  create a virtual environment for our tests
```shell
~/.pyenv/versions/3.9.4/bin/virtualenv wx_test
source wx_test/bin/activate
```
This will install the various stuff into the Python virtual environment. We will do the equivalent automatically by listing the actual dependencies in a setup.py file

```shell
pip install pyqt5 PyQtWebEngine
pip install PySide2
```

Always handy to have Jupyter!
```shell
pip install jupyter
jupyter notebook --ip 0.0.0.0
```
run the program
```shell
python qt_browser_widget.py
```
