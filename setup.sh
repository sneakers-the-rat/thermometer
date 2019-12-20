

#####################3
# make venv and install depends

sudo apt-get update
sudo apt-get install -y python3-pip \
  python3-virtualenv \
  python3-numpy \
  qt5-default \
  libqt5xmlpatterns5-dev \
  libclang-dev \
  llvm \
  clang \
  cmake

python3 -m venv env
source env/bin/activate

pip3 install wheel

#######################################
# if we haven't already, get our submodules
git submodule update --init --recursive

# make and install the driver
cd mlx90640-library
make all
sudo make install

# and then python bindings
cd python/library
make build
sudo make install
cd ../../../

##################################
# pyside

cd pyside-setup
# or be more sophisticated about checking what version of qt was installed above
git checkout 5.11

python setup.py install


