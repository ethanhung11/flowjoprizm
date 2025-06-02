import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import f_oneway, kruskal
from statannotations.Annotator import Annotator
from itertools import combinations

def DEFAULT_COLORS(n=4):
    return ["#009F80", "#AA87EE", "#F87C00", "#C74B00"][:n]

def flow_plot(df,
              measurement_cols,
              rename=None,
              group_type='Group',
              extra_group=[],
              parametric=True,
              alpha=0.05, 
              ax=None,
              title=None,
              verbose=True,
              colors=None,
              ):

    if ax is None:
        plt.figure()

    cols_to_keep = measurement_cols+[group_type]+extra_group
    melted = pd.melt(df[cols_to_keep],id_vars=[group_type]+extra_group)
    groups = df[group_type].unique()
    n_groups = len(groups)
    n_groups_extra = np.prod([len(df[x].unique()) for x in extra_group]) if len(extra_group)>0 else 1
    print(melted.head())

    if colors is None:
        colors = DEFAULT_COLORS(n_groups)
    if n_groups_extra>1:
        # TODO: add random variation between groups
        colors = n_groups_extra*4

    # return melted

    # plot data, as a barplot & with datapoints
    if extra_group:
        hues = melted[[group_type]+extra_group].agg(', '.join, axis=1)
    else:
        hues = group_type

    sns.barplot(x='variable', y='value', hue=hues, data=melted, errorbar=None,
                palette=colors, linewidth=1, edgecolor='black',
                ax=ax,
                )
    sns.stripplot(x='variable', y='value', hue=hues, data=melted,
                order=measurement_cols, hue_order=groups,
                dodge=True, palette=colors,
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

    if n_groups>1:
        # statistical testing
        pairs = []
        if n_groups*n_groups_extra == 2:
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
                group_data = [col_data[col_data[group_type] == group][col].values 
                            for group in groups if len(col_data[col_data[group_type] == group]) > 0]
                
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
            annotator = Annotator(ax, pairs, data=melted, x='variable', y='value', hue=group_type)
            
            # Bonferroni correction for 3+ groups
            if n_groups*n_groups_extra > 2:
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
        l = ax.legend(handles[0:n_groups*n_groups_extra], labels[0:n_groups*n_groups_extra])

        if title:
            ax.set_title(title)

    return melted