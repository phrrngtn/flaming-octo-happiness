# check that the xcode command line tools are installed.
xcode-select -p

brew update
brew install pyenv
brew install cmake openssl readline sqlite3 xz zlib

# See what revisions are available to install
pyenv install --list
pyenv install 3.9.4

# this will install it to a path like this one. 
# First thing we do is upgrade the pip installation itself
/Users/phrrngtn/.pyenv/versions/3.9.4/bin/python3.9 -m pip install --upgrade pip

# Now virtualenv
/Users/phrrngtn/.pyenv/versions/3.9.4/bin/pip install virtualenv


# now we  create a virtual environment for our tests
/Users/phrrngtn/.pyenv/versions/3.9.4/bin/virtualenv wx_test
source wx_test/bin/activate

# this will install the various stuff into the Python virtual environment. We
# will do the equivalent automatically by listing the actual dependencies in a 
# setup.py file
pip install pyqt5 PyQtWebEngine
pip install PySide2

#pip install jupyter
#jupyter notebook --ip 0.0.0.0

# run the program
python qt_browser_widget.py
