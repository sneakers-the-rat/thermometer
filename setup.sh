

#####################3
# make venv and install depends

sudo apt-get update
sudo apt-get install -y python3-pip \
  python3-virtualenv \
  python3-numpy \
  python3-scipy
  qt5-default \
  libqt5xmlpatterns5-dev \
  libatlast-base-deb \
  libclang-dev \
  libi2c-dev \
  swig \
  llvm \
  clang \
  cmake
  
  
# enable i2c module
sudo sed -i 's/^#dtparam=i2c_arm=on/dtparam=i2c_arm=on/g' /boot/config.txt

# increase baudrate
sudo sed -i '$s/$/\ndtparam=i2c_arm_baudrate=1000000/' /boot/config.txt


python3 -m venv --system-site-packages env
source env/bin/activate

#pip3 install wheel pyqtgraph

#######################################
# if we haven't already, get our submodules
git submodule update --init --recursive

# make and install the driver
cd mlx90640-library
make all
sudo make install

# and then python bindings
cd python/library
python ./setup.py install
#make build
#sudo make install
cd ../../../

##################################
# pyside

cd pyside-setup
# by default expects 5.11, but we can be more sophisticated w/ qmake --version

python setup.py install

cd ../

###########
# pyqtgraph
cd pyqtgraph

python setup.py install

cd ../




