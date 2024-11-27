Check that the xcode command line tools are installed:
```shell
xcode-select -p
```
We assume installation of Python from python.org which, if successful should place python executable in /usr/local/bin/python

In the interest of making the stuff copy-and-pastable, I will write the path using tilde(~) and assume that the shell you are using expands that out to your home directory. In any case, the commands reproduced here are intended to be illustrative only. You may have to run additional ones or some variants. In summary, we need these toolchains:
- Xcode
- virtualenv

now we  create a virtual environment for our tests
```shell
/usr/local/bin/python3 -m venv qt_test
source qt_test/bin/activate
```
This will install the various stuff into the Python virtual environment. We will do the equivalent automatically by listing the actual dependencies in a setup.py file

```shell
pip install PySide6 PySide6_Addons PySide6_Essentials
pip install -U geopandas folium
```

Always handy to have Jupyter!
```shell
pip install jupyter
jupyter notebook --ip 0.0.0.0
```
run the program
```shell
python3 qt_browser_widget.py
```
