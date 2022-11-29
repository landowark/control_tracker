import plotly.express as px
import pandas as pd
from pathlib import Path
from plotly.graph_objects import Figure
import logging
from .excel_functions import get_unique_values_in_df_column, drop_reruns_from_df
import sys

logger = logging.getLogger("controls.tools.vis_functions")



def create_charts(settings:dict, df:pd.DataFrame, group_name:str) -> list:
    """
    Constructs figures based on parsed pandas dataframe.

    Args:
        settings (dict): settings passed down from click
        df (pd.DataFrame): input dataframe
        group_name (str): controltype

    Returns:
        Figure: _description_
    """    
    
    genera = []
    figs = []
    for item in df['genus'].to_list():
        try:
            if item[-1] == "*":
                genera.append(item[-1])    
            else:
                genera.append("")
        except IndexError:
            genera.append("")
    df['genus'] = df['genus'].replace({'\*':''}, regex=True)
    df['genera'] = genera
    df = df.dropna()
    df = drop_reruns_from_df(settings=settings, df=df)
    logger.debug(f"Unique names: {get_unique_values_in_df_column(df, column_name='name')}")
    df.to_excel("test_drop_from_run.xlsx", engine="openpyxl")
    # sys.exit(df)
    run_ref = True
    for mode in settings['modes']:
        if mode == "contains" or mode == "matches":
            if run_ref:
                func = function_map["construct_refseq_chart"]
                run_ref = False
            else:
                continue
        else:
            func = function_map[f"construct_{mode}_chart"]
        figs.append(func(settings=settings, df=df, group_name=group_name, mode=mode))
    return figs
    
    

    # TODO: replace these with functions for each bar type.
    # fig_contains = ref_seq_masher_barchart(settings=settings, df=df, group_name=group_name, mode="contains", genera=genera)
    # fig_contains.update_traces(visible=False)
    # fig_matches = ref_seq_masher_barchart(settings=settings, df=df, group_name=group_name, mode="matches", genera=genera)
    # fig_matches.update_traces(visible=False)
    # fig_kraken = kraken_barchart(settings=settings, df=df, group_name=group_name, genera=genera)
    # fig_kraken.update_traces(visible=True)
    
    # fig.add_traces(fig_contains.data)
    # fig.add_traces(fig_matches.data)
    # fig.add_traces(fig_kraken.data)
    

def generic_figure_markers(fig:Figure) -> Figure:
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    fig.update_layout(xaxis_title="Submitted Date (* - Date parsed from fastq file creation date)")
    # fig.add_annotation(text='* - Sample submission date parsed from fastq file creation date', 
    #                 align='left',
    #                 showarrow=False,
    #                 xref='paper',
    #                 yref='paper',
    #                 x=0.0,
    #                 y=1.1)
    logger.debug(fig)
    return fig

def output_figures(settings:dict, figs:list, group_name:str):
    """
    Writes plotly figure to html file.

    Args:
        settings (dict): settings passed down from click
        fig (Figure): input figure object
        group_name (str): controltype
    """
    with open(Path(settings['folder']['output']).joinpath(f'{group_name}.html'), "w") as f:
        for fig in figs:
            f.write(fig.to_html(full_html=False, include_plotlyjs='cdn'))

# Below are the individual construction functions. They must be named "construct_{mode}_chart" and 
# take only json_in and mode to hook into the main processor.

def construct_refseq_chart(settings:dict, df:pd.DataFrame, group_name:str, mode:str):
    fig = Figure()
    
    # if there is only 'Off-Target' in targets, set visible to [True, False]
    if len(get_unique_values_in_df_column(df, column_name='target')) == 2:
        # Contains_OffTarget, Contains_Target, Matches_OffTarget, Matches_Target
        contains_vis = [True, True, False, False]
        matches_vis = [False, False, True, True]
    elif len(get_unique_values_in_df_column(df, column_name='target')) == 1:
        contains_vis = [True, False]
        matches_vis = [False, True]
    for mode in ['contains', 'matches']: 
        bar = px.bar(df, x="submitted_date", 
            y=f"{mode}_ratio", 
            color="target", 
            title=f"{group_name}_{mode}", 
            barmode='stack', 
            hover_data=["genus", "name", f"{mode}_hashes", "target"], 
            text="genera"
        )
        bar.update_traces(visible = mode == 'contains')
        # Plotly express returns a full figure, so we have to use the data from that figure only.
        fig.add_traces(bar.data)
    fig.update_layout(
        barmode='stack',
        title=group_name,
        yaxis_title="Hashes as Decimal (Stacked)",
        
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=0.7,
                y=1.2,
                showactive=True,
                buttons=list(
                    [
                        dict(
                            label="Contains",
                            method="update",
                            args=[
                                {"visible": contains_vis},
                                {"yaxis.title.text": "Contains Ratio"},
                            ],
                        ),
                        dict(
                            label="Matches",
                            method="update",
                            args=[
                                {"visible": matches_vis},
                                {"yaxis.title.text": "Matches Ratio"},
                            ],
                        ),
                    ]
                ),
            )
        ]
    )
    return generic_figure_markers(fig=fig)

def construct_kraken_chart(settings:dict, df:pd.DataFrame, group_name:str, mode:str):
    df[f'{mode}_count'] = pd.to_numeric(df[f'{mode}_count'],errors='coerce')
    df['updated_percent'] = 100 * df[f'{mode}_count'] / df.groupby('submitted_date')[f'{mode}_count'].transform('sum')
    fig = px.bar(df, x="submitted_date",
        # y=f"{mode}_percent",
        y="updated_percent",
        color="genus",
        title=f"{group_name}_percent_reads",
        barmode='stack',
        hover_data=["genus", "name", f"{mode}_percent"],
        text="genera"
    )
    fig.update_layout(barmode='relative',
        yaxis_title="% of reads ",
    )
    return generic_figure_markers(fig=fig)

########This must be at bottom of module###########

function_map = {}
for item in dict(locals().items()):
    try:
        if dict(locals().items())[item].__module__ == __name__:
            try:
                function_map[item] = dict(locals().items())[item]
            except KeyError:
                pass
    except AttributeError:
        pass
###################################################