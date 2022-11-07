from re import I
import plotly.express as px
import pandas as pd
from pathlib import Path
from plotly.graph_objects import Figure
import logging

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

    fig_contains = px.bar(df, x="submitted_date", y="contains_ratio", color="target", title=f"{group_name}_contains", barmode='stack', hover_data=["genus", "contains_hashes", "target"])
    fig_matches = px.bar(df, x="submitted_date", y="matches_ratio", color="target", title=f"{group_name}_matches", barmode='stack', hover_data=["genus", "matches_hashes", "target"])
    fig_contains.update_traces(visible=True)
    fig_matches.update_traces(visible=False)
    # fig.add_traces(fig_contains)
    # fig_contains = go.Bar(x=df['submitted_date'], y=df['contains_ratio'])
    # fig_matches = go.Bar(x=df['submitted_date'], y=df['matches_ratio'])
    # Plotly express returns a full figure, so we have to use the data from that figure only.
    fig.add_traces(fig_contains.data)
    fig.add_traces(fig_matches.data)
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_layout(
        barmode='stack',
        title=group_name,
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
                                {"visible": [True, True, False, False]},
                                {"yaxis.title.text": "Contains Ratio"},
                            ],
                        ),
                        dict(
                            label="Matches",
                            method="update",
                            args=[
                                {"visible": [False, False, True, True]},
                                {"yaxis.title.text": "Matches Ratio"},
                            ],
                        ),
                    ]
                ),
            )
        ]
    )
    # fig.for_each_trace(
    #     lambda trace: trace.update(visible=False) if "matches" in trace.title else (),
    # )
    logger.debug(fig)
    if settings['test']:
        fig_contains.write_html(f"{Path(settings['folder']['output']).joinpath(f'{group_name}_contains.html')}")
        fig_matches.write_html(f"{Path(settings['folder']['output']).joinpath(f'{group_name}_matches.html')}")
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