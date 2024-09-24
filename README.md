[TOC]

# gLinDA
gLinDA is a peer-to-peer swarm learning implementation of the differential abundance analysis tool LinDA, originally written in R.

## Installation
First of all, copy the repository and resolve all dependencies.

```bash
git clone https://imigitlab.uni-muenster.de/published/glinda.git
cd glinda
pip install -r requirements.txt
```

You can verify the successful installation by running the exemplary S-5000 dataset in the solo mode, just execute
```bash
python glinda.py --config examples/s5000.ini
```

## Running
If you like to open the graphical user interface, just run
```bash
python gui.py
```
