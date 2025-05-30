import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import f_oneway, kruskal
from statannotations.Annotator import Annotator
from itertools import combinations
from typing import Iterable

DEFAULT_COLORS = ["#009F80", "#AA87EE", "#F87C00", "#C74B00"]

def cleanDF(df:pd.DataFrame,
            group:str=None,
            group_name:str=None):
    if group or group_name:
        df[group_name] = group # add Group

    df.columns.values[0] = "Sample" # rename first col to Sample
    df = df[~df.Sample.str.contains("Mean|SD")] # remove stats rows (will calculate ourwselves later)
    df = df.dropna(axis=1) # drop any empty columns

    # rename, removing the "| STAT" & and any earlier gating
    df.columns = [col[0].split('/')[-1].strip() for col in df.columns.str.split(r'|')]
    # reindex to leave Sample & Group, & beads at the front
    if group or group_name:
        metadata = ["Sample",group_name]
    else:
        metadata = ["Sample"]
    return df.reindex(columns=metadata+list(df.columns[~df.columns.isin(metadata)]))


def processDF(name:str,
              beads:int=None,
              bead_col:str=None,
              group='Group',
              homedir="../../data",
              ):
    
    # get files
    path = os.path.join(homedir,name)
    files = [file for file in os.listdir(path)]

    # read data in & clean
    dfs = [pd.read_csv(os.path.join(path,file)) for file in files]
    df = pd.concat([cleanDF(df,files[n].split('.')[0],group) for n,df in enumerate(dfs)])
    df = df.reset_index(drop=True)

    # scale data
    if beads:
        df["Scaling"] = beads/df[bead_col]
        metadata = ["Sample",group,bead_col,"Scaling"]
    else:
        metadata = ["Sample",group]
    df[df.columns[~df.columns.isin(metadata)]] = df[df.columns[~df.columns.isin(metadata)]].multiply(df.Scaling,0)
    return df


def processFlowJo(name:str,
                  beads:int=None,
                  bead_col:str=None,
                  groups:Iterable[str]=None,
                  homedir=None,
                  verbose=True,
                  ):
    if homedir is None:
        homedir = "../../data"
        if verbose is True:
            print(f"data directory not given! Defaulting to '{homedir}'")
            
    if beads is None:
        if verbose is True:
            print("Bead count not given. No scaling will be applied.")
    else:
        if bead_col is None:
            raise LookupError(f"Bead count given, but bead column name not provided!")

    # multiple group types
    if groups:
        # process all dfs
        dfs = [processDF(
            name=os.path.join(name,g), beads=beads,
            bead_col=bead_col, group=g, homedir=homedir,)
            for g in groups
        ]
        # merge
        for n in range(len(dfs)-1):
            df = pd.merge(dfs[n],dfs[n+1])
        # reindex
        order = ["Sample"]+groups+[bead_col,'Scaling']
        df = df.reindex(columns=order+list(df.columns[~df.columns.isin(order)]))

    # no grouping
    elif re.search(".csv", name):
        df = cleanDF(pd.read_csv(name))
        # scale data
        if beads:
            df["Scaling"] = beads/df[bead_col]
            metadata = ["Sample",bead_col,"Scaling"]
            df[df.columns[~df.columns.isin(metadata)]] = df[df.columns[~df.columns.isin(metadata)]].multiply(df.Scaling,0)

    # default grouping
    else:
        # process df
        df = processDF(name=name,
                       beads=beads,
                       bead_col=bead_col,
                       homedir=homedir,)

    return df


def flow_plot(df,
              measurement_cols,
              rename=None,
              group_col='Group',
              parametric=True,
              alpha=0.05, 
              ax=None,
              title=None,
              verbose=True
              ):
    
    if ax is None:
        f = plt.figure()

    melted = pd.melt(df[measurement_cols+[group_col]],id_vars=group_col)
    groups = df[group_col].unique()
    n_groups = len(groups)

    # plot data, as a barplot & with datapoints
    sns.barplot(x='variable', y='value', hue=group_col, data=melted, errorbar=None,
                palette=DEFAULT_COLORS, linewidth=1, edgecolor='black',
                ax=ax,
                )
    sns.stripplot(x='variable', y='value', hue=group_col, data=melted,
                  order=measurement_cols, hue_order=groups,
                  dodge=True, palette=DEFAULT_COLORS,
                  alpha=1, linewidth=1, edgecolor='black',
                  ax=ax,
                  )

    # rename measurements if desired
    if rename:
        assert len(measurement_cols) == len(rename)
        kwargs = dict(ticks=range(len(measurement_cols)),
                      labels=rename)
        if ax is None:
            plt.xticks(**kwargs)
        else:
            ax.set_xticks(**kwargs)

    # statistical testing
    pairs = []
    if n_groups == 2:
        # 2 groups
        for col in measurement_cols:
            pairs.append(((col, groups[0]), (col, groups[1])))
        test = 't-test_ind' if parametric else 'Mann-Whitney'
    else:
        # 3+ groups
        if verbose is True:
            print("Multiple groups detected. Performing pairwise comparisons...")
        
        # For each measurement...
        for col in measurement_cols:
            # check if overall test is significant
            col_data = df[df[col].notna()]  # Remove NaN values
            group_data = [col_data[col_data[group_col] == group][col].values 
                         for group in groups if len(col_data[col_data[group_col] == group]) > 0]
            
            if parametric:
                stat, p_overall = f_oneway(*group_data)
            else:
                stat, p_overall = kruskal(*group_data)
            
            if verbose is True:
                print(f"{col}: Overall p-value = {p_overall:.4f}")
            
            # if overall test is significant, do pairwise comparisons
            if p_overall < alpha:
                for group1, group2 in combinations(groups, 2):
                    pairs.append(((col, group1), (col, group2)))
        
        test = 't-test_ind' if parametric else 'Mann-Whitney'
    
    # add annotations to graph
    if pairs:
        annotator = Annotator(ax, pairs, data=melted, x='variable', y='value', hue=group_col)
        
        # Bonferroni correction for 3+ groups
        if n_groups > 2:
            annotator.configure(
                test=test,
                text_format='star',
                loc='outside',
                verbose=1,
                comparisons_correction='bonferroni', 
                alpha=alpha,
            )

        # 2 groups
        else:
            annotator.configure(
                test=test,
                text_format='star',
                loc='outside',
                verbose=1,
                alpha=alpha,
            )
        
        # add annotations
        annotator.apply_and_annotate()

    # labeling
    if ax is None:
        plt.xlabel("Cell Type")
        plt.ylabel("Count")
        if title:
            plt.title(title)
    else:
        ax.set_xlabel("Cell Type")
        ax.set_ylabel("Count")
        handles, labels = ax.get_legend_handles_labels()
        l = ax.legend(handles[0:n_groups], labels[0:n_groups])

        if title:
            ax.set_title(title)

    return