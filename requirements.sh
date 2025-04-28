sudo apt install libcap-dev
sudo apt install libcamera-apps python3-libcamera
sudo apt install -y cmake build-essential python3-dev

deactivate
rm -rf venv
python3 -m venv --system-site-packages venv
source venv/bin/activate