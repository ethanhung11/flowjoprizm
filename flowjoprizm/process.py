import os
import re
import pandas as pd
from typing import Iterable


def cleanDF(df:pd.DataFrame,
            group:str=None,
            group_name:str='Group'):
    if group:
        df[group_name] = group
    else:
        df[group_name]="No Group Provided"

    df.columns.values[0] = "Sample" # rename first col to Sample
    df = df[~df.Sample.str.contains("Mean|SD")] # remove stats rows (will calculate ourwselves later)
    df = df.dropna(axis=1) # drop any empty columns

    # rename, removing the "| STAT" & and any earlier gating
    df.columns = [col[0].split('/')[-1].strip() for col in df.columns.str.split(r'|')]
    # reindex to leave Sample & Group, & beads at the front
    metadata = ["Sample",group_name]
    return df.reindex(columns=metadata+list(df.columns[~df.columns.isin(metadata)]))


def processDF(name:str,
              beads:int=None,
              bead_col:str=None,
              group='Group',
              homedir="./data",
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
        homedir = "./data"
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