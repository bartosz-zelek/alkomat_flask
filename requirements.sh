sudo apt install libcap-dev libcamera-apps python3-libcamera cmake build-essential python3-dev

rm -rf venv
python3 -m venv --system-site-packages venv
source venv/bin/activate