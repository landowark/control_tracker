from re import I
import plotly.express as px
import pandas as pd
from pathlib import Path
from plotly.graph_objects import Figure
import logging
from .excel_functions import get_unique_values_in_df_column

logger = logging.getLogger("controls.tools.vis_functions")

def create_stacked_bar_chart(settings:dict, df:pd.DataFrame, group_name:str) -> Figure:
    """
    Constructs figure based on parsed pandas dataframe.

    Args:
        settings (dict): settings passed down from click
        df (pd.DataFrame): input dataframe
        group_name (str): controltype

    Returns:
        Figure: _description_
    """    
    fig = Figure()
    df = df.dropna()
    genera = []
    for item in df['genus'].to_list():
        try:
            if item[-1] == "*":
                genera.append(item[-1])    
            else:
                genera.append("")
        except IndexError:
            genera.append("")
    # TODO: if there is only 'Off-Target' in targets, set visible to [True, False]
    if len(get_unique_values_in_df_column(df, column_name='target')) == 2:
        contains_vis = [True, True, False, False]
        matches_vis = [False, False, True, True]
    elif len(get_unique_values_in_df_column(df, column_name='target')) == 1:
        contains_vis = [True, False]
        matches_vis = [False, True]
    fig_contains = px.bar(df, x="submitted_date", 
        y="contains_ratio", 
         
        color="target", 
        title=f"{group_name}_contains", 
        barmode='stack', 
        hover_data=["genus", "contains_hashes", "target"], 
        text=genera
    )
    fig_matches = px.bar(df, x="submitted_date", 
        y="matches_ratio", 
        
        color="target", 
        title=f"{group_name}_matches", 
        barmode='stack', 
        hover_data=["genus", "matches_hashes", "target"], 
        text=genera
    )
    fig_contains.update_traces(visible=True)
    fig_matches.update_traces(visible=False)
    # Plotly express returns a full figure, so we have to use the data from that figure only.
    fig.add_traces(fig_contains.data)
    fig.add_traces(fig_matches.data)
    fig.update_xaxes(rangeslider_visible=True)
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
    fig.add_annotation(text='* - Sample submission date parsed from fastq file creation date', 
                    align='left',
                    showarrow=False,
                    xref='paper',
                    yref='paper',
                    x=0.0,
                    y=1.1)
    logger.debug(fig)
    return fig
    
def output_figure(settings:dict, fig:Figure, group_name:str):
    """
    Writes plotly figure to html file.

    Args:
        settings (dict): settings passed down from click
        fig (Figure): input figure object
        group_name (str): controltype
    """    
    fig.write_html(f"{Path(settings['folder']['output']).joinpath(f'{group_name}.html')}")