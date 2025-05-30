# FlowJoPrizm

Prism analysis dupe! Put your data in `./data/[experiment]`, then run `processFlowJo()` and `flow_plot()`.

## TLDR

1. Install Python.
    1. (optional) Install Rye. I recommend this over Conda unless you're running a complex environment.
2. Install this package (`flowjoprizm`).
3. Save your data following the directory structure (see Recommended Usage).
4. Run `processFlowJo()` to prepare your data for plotting.
5. Run `flow_plot()` to plot relevant populations. There are additional parameters for plotting adjustments. More will be added eventually.

See `sample.ipynb` for an example usage!

## Installation
* I use Rye for lightweight package management.

**Rye:**
```bash
rye add flowjoprizm --git https://github.com/ethanhung11/flowjoprizm.git
```
**Pip:**
```bash
pip install flowjoprizm @ git+https://github.com/ethanhung11/flowjoprizm.git
```
**Conda:**
```bash
conda install git pip
pip install flowjoprizm @ git+https://github.com/ethanhung11/flowjoprizm.git
```

## Recommended Usage
Gate your FlowJo populations, then save the counts (or any other statistic!). Data must saved in one of the following directories structures:
```
.
└── data
    ├── EXPERIMENT_1.csv
    │
    ├── EXPERIMENT_2
    │   ├── GROUP_CATEGORY_1.csv
    │   ├── GROUP_CATEGORY_2.csv
    │   └── ...
    │
    └── EXPERIMENT_3
        ├── GROUP_TYPE_1
        │   ├── GROUP_CATEGORY_1.csv
        │   ├── GROUP_CATEGORY_2.csv
        │   └── ...
        ├── GROUP_TYPE_2
        └── ...
```
#### EXPERIMENT 1
- Assumes there are not groups to compare.

#### EXPERIMENT 2
- Assumes there is only one group to compare. Each `GROUP_CATEGORY` is named by the .csv it references. The `GROUP_TYPE` will default to `"Group"` will not have a desired name.

#### EXPERIMENT 3
- Assume there is ≥1 groups you're compare, possibly at once (e.g. tissue type, measurements type, etc.).
- Grouping type name is determined by the name of the `GROUP_TYPE` folder
- Each `GROUP_CATEGORY` is named by the .csv it references.


### NOTES
- Any sample to be analyzed must be saved to at least one of the .csv files. If multiple groups are given, then any sample not referenced anywhere in that `GROUP_TYPE` folder's .csv files will be left as NA.
