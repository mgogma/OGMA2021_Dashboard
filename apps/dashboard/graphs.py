######################################################################################################################
"""
graphs.py

Contains functions to generate graphs.
"""
######################################################################################################################

# External Packages
from _datetime import datetime

from flask import session
from parse import parse
import plotly.express as px
import dash_core_components as dcc
import dash_table
import dash_html_components as html
import dash
import pandas as pd
import plotly.graph_objects as go

# Internal Modules
from apps.dashboard.data import get_label, customize_menu_filter, linear_regression, polynomial_regression, \
    data_manipulator


# ***********************************************HELPER FUNCTIONS****************************************************


def set_partial_periods(fig, dataframe, graph_type):
    """Marks partial periods on the graph and returns the updated figure."""
    # ---------------------------------------Variable Declarations------------------------------------------------------
    partial_data_points = dataframe[dataframe['Partial Period'] == get_label('LBL_TRUE')]
    index_vals = list(partial_data_points.index.values)
    partial_pos = {}  # Key: x_val, Value: list of y_vals
    # ------------------------------------------------------------------------------------------------------------------

    for i in range(len(partial_data_points)):
        # Co-ordinates of marker to be labeled
        x_val = partial_data_points.loc[index_vals[i], 'Date of Event']
        y_val = partial_data_points.loc[index_vals[i], 'Measure Value']
        if x_val in partial_pos:
            # Add y_val to list associated with x_val
            current_y_list = partial_pos[x_val]
            current_y_list.append(y_val)
            partial_pos[x_val] = current_y_list
        else:
            # Create new list of y_vals
            partial_pos[x_val] = [y_val]
        partial_pos[x_val].sort(reverse=True)

    # None on bar graph due to formatting
    if graph_type != 'Bar':
        for i in partial_pos:
            for j in range(len(partial_pos[i])):
                if j == 0:
                    # Data point with highest y val (for each x) is labeled
                    fig.add_annotation(
                        x=i,
                        y=partial_pos[i][j],
                        text=get_label("LBL_Partial_Period"),
                        showarrow=True,
                        arrowhead=7,
                        ax=0,
                        ay=-40,
                        bgcolor='#ffffff')
                else:
                    # Unlabeled black dots on lower data points
                    fig.add_annotation(
                        x=i,
                        y=partial_pos[i][j],
                        text="",
                        arrowhead=7,
                        ax=0,
                        ay=0)

    return fig


def get_empty_graph_subtitle(hierarchy_toggle, hierarchy_level_dropdown, hierarchy_path, secondary_type, secondary_path,
                             df_name, df_const):
    """Returns subtitle for empty graph."""
    sub_title = ''
    if df_name is None or df_name not in df_const:
        sub_title = '<br><sub>{}</sub>'.format(get_label('LBL_No_Data_Found'))
    elif hierarchy_toggle == 'Level Filter' and hierarchy_level_dropdown is None \
            or hierarchy_toggle == 'Specific Item' and not hierarchy_path:
        sub_title = '<br><sub>{}</sub>'.format(get_label('LBL_Make_A_Hierarchy_Selection'))
    elif secondary_type == 'Specific Item' and not secondary_path:
        sub_title = '<br><sub>{}</sub>'.format(get_label('LBL_Make_A_Variable_Selection'))
    return sub_title


def get_hierarchy_col(hierarchy_toggle, hierarchy_level_dropdown, hierarchy_graph_children, hierarchy_path,
                      df_const, session_key):
    """Returns the hierarchy column."""
    if hierarchy_toggle == 'Level Filter':
        hierarchy_col = hierarchy_level_dropdown
    elif hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == ['graph_children']:
        hierarchy_col = df_const[session_key]['HIERARCHY_LEVELS'][len(hierarchy_path)]
    else:
        hierarchy_col = df_const[session_key]['HIERARCHY_LEVELS'][len(hierarchy_path) - 1]

    return hierarchy_col


# ************************************************GRAPH FUNCTIONS**************************************************


def get_line_scatter_figure(arg_value, dff, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                            hierarchy_toggle, hierarchy_graph_children, tile_title, df_name, df_const, xaxis_title,
                            yaxis_title, xlegend, ylegend, gridline, legend, secondary_level_dropdown,
                            secondary_path, secondary_type, secondary_graph_children, session_key, heirarchy_type):
    """Returns the line graph figure."""
    # ------------------------------------------------Arg Values--------------------------------------------------------
    # arg_value[0] = xaxis selector
    # arg_value[1] = measure type selector
    # arg_value[2] = mode
    # arg_value[3] = fit
    # arg_value[4] = degree
    # arg_value[5] = confidence interval
    # arg_value[6] = variable names selector
    # ------------------------------------------------------------------------------------------------------------------

    language = session["language"]

    # Check on whether we have enough information to attempt to get data for a graph
    if hierarchy_toggle == 'Level Filter' and None not in [arg_value, hierarchy_level_dropdown, hierarchy_toggle,
                                                         hierarchy_graph_children, df_name, df_const] \
            or hierarchy_toggle == 'Specific Item' and None not in [arg_value, hierarchy_path, hierarchy_toggle,
                                                                  hierarchy_graph_children, df_name, df_const]:
        # Specialty filtering
        filtered_df = dff.copy()
        if secondary_type == 'Level Filter':
            category = secondary_level_dropdown
        elif secondary_type == 'Specific Item' and secondary_graph_children == ['graph_children']:
            category = df_const[session_key]['SECONDARY_HIERARCHY_LEVELS'][len(secondary_path)]
        else:
            category = df_const[session_key]['SECONDARY_HIERARCHY_LEVELS'][len(secondary_path) - 1] \
                if len(secondary_path) != 0 else 'Variable Name'

        hierarchy_col = get_hierarchy_col(hierarchy_toggle, hierarchy_level_dropdown, hierarchy_graph_children,
                                          hierarchy_path, df_const, session_key)
        # Create title
        if hierarchy_toggle == 'Level Filter' or (hierarchy_toggle == 'Specific Item' and
                                                hierarchy_graph_children == ['graph_children']):
            if tile_title:
                title = tile_title
            else:
                # Generate title if there is no user entered title
                if hierarchy_toggle == 'Level Filter':
                    # Whole level graph title
                    title = '{}: {} vs {}'.format(get_label('LBL_' + hierarchy_level_dropdown, heirarchy_type),
                                                  get_label(arg_value[1], df_name+"_Measure_type"),
                                                  get_label('LBL_Time'))  # hierarchy_level_dropdown
                elif len(hierarchy_path) != 0:
                    # Item's children graph title
                    if language == 'En':
                        title = '{}\'s {}'.format(hierarchy_path[-1], get_label('LBL_Children'))
                    else:
                        title = '{} {}'.format(get_label('LBL_Children_Of'), hierarchy_path[-1])
                    title = title + ': {} vs {}'.format(get_label(arg_value[1], df_name+"_Measure_type"),
                                                        get_label('LBL_Time'))
                else:
                    # Root's children graph title
                    title = '{}: {} vs {}'.format(get_label("LBL_Roots_Children"),
                                                  get_label(arg_value[1], df_name+"_Measure_type"),
                                                  get_label('LBL_Time'))
        else:
            if tile_title:
                title = tile_title
            else:
                # Generate title if there is no user entered title
                if hierarchy_specific_dropdown:
                    title = '{}: {} vs {}'.format(hierarchy_specific_dropdown, get_label(arg_value[1],
                                                                                         df_name+"_Measure_type"),
                                                  get_label('LBL_Time'))
                else:
                    if len(hierarchy_path) == 0:
                        title = ""
                    else:
                        title = '{}: {} vs {}'.format(hierarchy_path[-1], get_label(arg_value[1],
                                                                                    df_name+"_Measure_type"),
                                                      get_label('LBL_Time'))

        # df is not empty, create graph
        if len(filtered_df) != 0:
            title += '<br><sub>{} {} </sub>'.format(get_label('LBL_Data_Accessed_On'), datetime.date(datetime.now()))

            # hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
            if hierarchy_toggle == 'Level Filter' or (hierarchy_toggle == 'Specific Item' and
                                                    hierarchy_graph_children == ['graph_children']):
                color = hierarchy_col
                line_group = category
                legend_title_text = get_label('LBL_' + hierarchy_col, df_name)
            else:
                color = category
                line_group = None
                legend_title_text = get_label('LBL_Variable_Names')

            # filter the dataframe down to the partial period selected
            filtered_df['Partial Period'] = filtered_df['Partial Period'].astype(str).transform(
                lambda j: get_label('LBL_TRUE') if j == 'True' else get_label('LBL_FALSE'))
            filtered_df['Date of Event'] = \
                filtered_df['Date of Event'].transform(lambda y: y.strftime(format='%Y-%m-%d'))
            filtered_df.sort_values(by=[color, 'Date of Event'], inplace=True)
            # generate graph
            color_discrete = color_picker(arg_value[6])

            fig = px.line(
                title=title,
                data_frame=filtered_df,
                x='Date of Event',
                y='Measure Value',
                color=color,
                color_discrete_sequence=color_discrete,
                line_group=line_group,
                custom_data=[hierarchy_col, category])
            fig.update_layout(legend_title_text=legend_title_text)

            # check what arg_value[2]: mode is selected and sets the corresponding trace
            if arg_value[2] == 'Line':
                fig.update_traces(mode='lines')
            elif arg_value[2] == 'Scatter':
                fig.update_traces(mode='markers')
            else:
                fig.update_traces(mode='lines+markers')

            # set up hover label
            hovertemplate = get_label('LBL_Gen_Hover_Data', df_name)
            hovertemplate = hovertemplate.replace('%AXIS-TITLE-A%', get_label('LBL_Date_of_Event', df_name)).replace(
                '%AXIS-A%', '%{x}')
            hovertemplate = hovertemplate.replace('%AXIS-TITLE-B%', get_label(arg_value[1],
                df_name+"_Measure_type")).replace('%AXIS-B%', '%{y}')
            fig.update_traces(hovertemplate=hovertemplate)
            fig = set_partial_periods(fig, filtered_df, 'Line')

            # ------------------------------------------DATA FITTING----------------------------------------------------
            # data fitting options visible when hierarchy toggle is on specific item
            # arg_value[3]: data fitting radio options
            if arg_value[3] == 'linear-fit':
                ci = True if arg_value[5] == ['ci'] else False
                best_fit_data = linear_regression(filtered_df, 'Date of Event', 'Measure Value', ci)
                filtered_df["Best Fit"] = best_fit_data["Best Fit"]
                fig2 = px.line(
                    data_frame=filtered_df,
                    x='Date of Event',
                    y='Best Fit',
                )
                fig2.update_traces(line_color='#A9A9A9')
                fig2.data[0].name = 'Best fit'
                fig2.data[0].showlegend = True
                fig.add_trace(fig2.data[0])
                # arg_value[5]: confidence interval is toggled
                if arg_value[5] == ['ci']:
                    filtered_df["Upper Interval"] = best_fit_data["Upper Interval"]
                    filtered_df["Lower Interval"] = best_fit_data["Lower Interval"]
                    fig3 = px.line(
                        data_frame=filtered_df,
                        x='Date of Event',
                        y='Upper Interval',
                    )
                    fig4 = px.line(
                        data_frame=filtered_df,
                        x='Date of Event',
                        y='Lower Interval',
                    )
                    fig3.update_traces(line_color='#000000')
                    fig3.data[0].showlegend = True
                    fig3.data[0].name = 'Upper Interval'
                    fig.add_trace(fig3.data[0])
                    fig4.update_traces(line_color='#000000')
                    fig4.data[0].showlegend = True
                    fig4.data[0].name = 'Lower Interval'
                    fig.add_trace(fig4.data[0])
            if arg_value[3] == 'curve-fit':
                ci = True if arg_value[5] == ['ci'] else False
                best_fit_data = polynomial_regression(filtered_df, 'Date of Event', 'Measure Value', arg_value[4], ci)
                filtered_df["Best Fit"] = best_fit_data["Best Fit"]
                fig2 = px.line(
                    data_frame=filtered_df,
                    x='Date of Event',
                    y='Best Fit',
                )
                fig2.update_traces(line_color='#A9A9A9')
                fig2.data[0].showlegend = True
                fig2.data[0].name = 'Best Fit'
                fig.add_trace(fig2.data[0])
                # arg_value[5]: confidence interval is toggled
                if arg_value[5] == ['ci']:  # ci
                    filtered_df["Upper Interval"] = best_fit_data["Upper Interval"]
                    filtered_df["Lower Interval"] = best_fit_data["Lower Interval"]
                    fig3 = px.line(
                        data_frame=filtered_df,
                        x='Date of Event',
                        y='Upper Interval',
                    )
                    fig4 = px.line(
                        data_frame=filtered_df,
                        x='Date of Event',
                        y='Lower Interval',
                    )
                    fig3.update_traces(line_color='#000000')
                    fig3.data[0].showlegend = True
                    fig3.data[0].name = 'Upper Interval'
                    fig.add_trace(fig3.data[0])
                    fig4.update_traces(line_color='#000000')
                    fig4.data[0].showlegend = True
                    fig4.data[0].name = 'Lower Interval'
                    fig.add_trace(fig4.data[0])
            # ----------------------------------------------------------------------------------------------------------
        else:
            fig = px.line(
                title=title + get_empty_graph_subtitle(hierarchy_toggle, hierarchy_level_dropdown, hierarchy_path,
                                                       secondary_type, secondary_path, df_name, df_const))
    else:
        fig = px.line(
            title=get_empty_graph_subtitle(hierarchy_toggle, hierarchy_level_dropdown, hierarchy_path, secondary_type,
                                           secondary_path, df_name, df_const))

    # set title
    if xaxis_title is not None and xaxis_title != '':
        xaxis = xaxis_title
    else:
        xaxis = 'Date of Event'

    if yaxis_title in df_const[session_key]["MEASURE_TYPE_VALUES"] or yaxis_title is None or yaxis_title == "":
        yaxis = get_label(arg_value[1], df_name+"_Measure_type")
    else:
        yaxis = yaxis_title

    # set legend position
    if xlegend and ylegend:
        fig.update_layout(legend=dict(
            x=xlegend,
            y=ylegend
        ))

    fig.update_layout(
        yaxis_title=yaxis,
        xaxis_title=xaxis,
        showlegend=False if legend else True,
        overwrite=True,
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)')

    # checks for gridline is toggled
    if gridline:
        fig.update_xaxes(showgrid=True, zeroline=True, gridcolor='Gray')
        fig.update_yaxes(showgrid=True, zeroline=True, gridcolor='Gray')
    else:
        fig.update_xaxes(showgrid=False, zeroline=False)
        fig.update_yaxes(showgrid=False, zeroline=False)

    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=language.lower(), edits=dict(annotationPosition=False, annotationTail=False,
                                                        annotationText=False, colourbarPosition=False,
                                                        ColorbarTitleText=False, legendPosition=True,
                                                        legendText=False, shapePosition=False,
                                                        titleText=False, axisTitleText=True)),
        figure=fig)

    return graph


def get_bubble_figure(arg_value, dff, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                      hierarchy_toggle, hierarchy_graph_children, tile_title, df_name, df_const, xaxis_title,
                      yaxis_title, xlegend, ylegend, gridline, legend, session_key, heirarchy_type):
    """Returns the bubble graph figure."""
    # ------------------------------------------------Arg Values--------------------------------------------------------
    # args_value[0] = x-axis
    # args_value[1] = x-axis measure
    # args_value[2] = y-axis
    # args_value[3] = y-axis measure
    # args_value[4] = size
    # args_value[5] = size measure
    # ------------------------------------------------------------------------------------------------------------------

    language = session["language"]
    xaxis = None
    yaxis = None
    filtered_df = []
    arg_value[1] = get_label(arg_value[1], df_name+"_Measure_type")
    arg_value[3] = get_label(arg_value[3], df_name + "_Measure_type")
    arg_value[5] = get_label(arg_value[5], df_name + "_Measure_type")
    # Check whether we have enough information to attempt getting data for a graph
    if hierarchy_toggle == 'Level Filter' and None not in [arg_value, hierarchy_level_dropdown, hierarchy_toggle,
                                                         hierarchy_graph_children, df_name, df_const] \
            or hierarchy_toggle == 'Specific Item' and None not in [arg_value, hierarchy_path, hierarchy_toggle,
                                                                  hierarchy_graph_children, df_name, df_const]:

        color = get_hierarchy_col(hierarchy_toggle, hierarchy_level_dropdown, hierarchy_graph_children, hierarchy_path,
                                  df_const, session_key)
        if len(dff) != 0:
            if arg_value[0] == 'Time':
                filtered_df = dff.copy().query(
                    "`{0}` == @arg_value[0] or "
                    "(`{0}` == @arg_value[2] and `Measure Type` == @arg_value[3]) or "
                    "(`{0}` == @arg_value[4] and `Measure Type` == @arg_value[5])".format(
                    df_const[session_key]['VARIABLE_LEVEL']))
                filtered_df[['Date of Event', 'Variable Name', 'Partial Period', color]] = \
                    filtered_df[
                        ['Date of Event', df_const[session_key]['VARIABLE_LEVEL'], 'Partial Period', color]].astype(str)
                filtered_df = filtered_df.pivot_table(index=['Date of Event', 'Partial Period', color],
                                                      columns=[df_const[session_key]['VARIABLE_LEVEL'], 'Measure Type'],
                                                      values='Measure Value').reset_index()
            else:
                # Specialty filtering
                # pandas.core.computation.ops.UndefinedVariableError: name 'BACKTICK_QUOTED_STRING__LBRACE_0_RBRACE_'
                # is not defined # TODO: Error
                filtered_df = dff.copy().query(
                    "(`{0}` == @arg_value[0] and `Measure Type` == @arg_value[1]) or "
                    "(`{0}` == @arg_value[2] and `Measure Type` == @arg_value[3]) or "
                    "(`{0}` == @arg_value[4] and `Measure Type` == @arg_value[5])".format(
                        df_const[session_key]['VARIABLE_LEVEL']))
                filtered_df[
                    ['Date of Event', 'Measure Type', df_const[session_key]['VARIABLE_LEVEL'], 'Partial Period',
                     color]] = \
                filtered_df[
                    ['Date of Event', 'Measure Type', df_const[session_key]['VARIABLE_LEVEL'], 'Partial Period',
                     color]].astype(str)
                filtered_df = filtered_df.pivot_table(index=['Date of Event', 'Partial Period', color],
                                                      columns=[df_const[session_key]['VARIABLE_LEVEL'], 'Measure Type'],
                                                      values='Measure Value').reset_index()

            filtered_df = filtered_df.dropna()

        # hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
        if hierarchy_toggle == 'Level Filter' or (hierarchy_toggle == 'Specific Item' and
                                                hierarchy_graph_children == ['graph_children']):
            # Title setup
            if tile_title:
                title = tile_title
            else:
                # Generate title if there is no user entered title
                if hierarchy_toggle == 'Level Filter':
                    # Whole level graph title
                    title = '{}: {} vs {}'.format(get_label('LBL_' + hierarchy_level_dropdown, heirarchy_type),
                                                  arg_value[2],  arg_value[4])
                elif len(hierarchy_path) != 0:
                    # Specific item's children graph title
                    if language == 'En':
                        title = '{}\'s {}'.format(hierarchy_path[-1], get_label('LBL_Children'))
                    else:
                        title = '{} {}'.format(get_label('LBL_Children_Of'), hierarchy_path[-1])
                    title = title + ': {} vs {}'.format(arg_value[2], arg_value[4])
                else:
                    # Root's children graph title
                    title = '{}: {} vs {}'.format(get_label("LBL_Roots_Children"), arg_value[2], arg_value[4])

        # hierarchy type is specific item while "Graph all in Dropdown" is unselected
        else:
            # Title setup
            if tile_title:
                title = tile_title
            else:
                if hierarchy_specific_dropdown:
                    title = '{}: {} vs {}'.format(hierarchy_specific_dropdown, arg_value[2], arg_value[4])
                else:
                    if len(hierarchy_path) == 0:
                        title = ""
                    else:
                        title = '{}: {} vs {}'.format(hierarchy_path[-1], arg_value[2], arg_value[4])

        # df is not empty, create graph
        if len(filtered_df) != 0:
            title += '<br><sub>{} {} </sub>'.format(get_label('LBL_Data_Accessed_On'), datetime.date(datetime.now()))
            legend_title_text = get_label(
                'LBL_' + hierarchy_level_dropdown, heirarchy_type) if hierarchy_toggle == 'Level Filter' else 'Traces'
            # filter the dataframe down to the partial period selected
            filtered_df['Partial Period'] = filtered_df['Partial Period'].astype(str).transform(
                lambda j: get_label('LBL_TRUE') if j == 'True' else get_label('LBL_FALSE'))
            # lambda j: get_label('LBL_TRUE') if j != 'nan' else get_label('LBL_FALSE'))
            filtered_df.sort_values(by=['Date of Event', color], inplace=True)
            filtered_df['Date of Event'] = filtered_df['Date of Event'].astype(str)

            if arg_value[0] == 'Time':
                color_discrete = color_picker(arg_value[6])

                fig = px.scatter(
                    title=title,
                    x=filtered_df['Date of Event'],
                    y=filtered_df[arg_value[2], arg_value[3]],
                    size=filtered_df[arg_value[4], arg_value[5]],
                    color=filtered_df[color],
                    color_discrete_sequence=color_discrete,
                    custom_data=[filtered_df[color], filtered_df['Date of Event'], filtered_df[arg_value[4],
                                                                                               arg_value[5]]]
                )
                fig.update_layout(
                    legend_title_text='Size: <br> &#9; {} ({})<br> <br>{}'.format(arg_value[4], arg_value[5],
                                                                                  legend_title_text))
                # set up hover label
                hovertemplate = get_label('LBL_Bubble_Fixed_Hover_Data', df_name)
                hovertemplate = hovertemplate.replace('%AXIS-X-A%', get_label('LBL_Date_of_Event', df_name)). \
                    replace('%X-AXIS%', '%{x}')
                hovertemplate = hovertemplate.replace('%AXIS-Y-A%', arg_value[2]).replace('%AXIS-Y-B%',
                    arg_value[3]).replace('%Y-AXIS%', '%{y}')
                hovertemplate = hovertemplate.replace('%AXIS-Z-A%', arg_value[4]).replace('%AXIS-Z-B%',
                    arg_value[5]).replace('%Z-AXIS%', '%{customdata[2]}')
                fig.update_traces(hovertemplate=hovertemplate)
            else:
                color_discrete = color_picker(arg_value[6])
                # generate graph
                fig = px.scatter(
                    title=title,
                    x=filtered_df[arg_value[0], arg_value[1]],
                    y=filtered_df[arg_value[2], arg_value[3]],
                    size=filtered_df[arg_value[4], arg_value[5]],
                    animation_frame=filtered_df['Date of Event'],
                    color=filtered_df[color],
                    color_discrete_sequence=color_discrete,
                    range_x=[0, filtered_df[arg_value[0], arg_value[1]].max()+100],
                    range_y=[0, filtered_df[arg_value[2], arg_value[3]].max()+100],
                    labels={'animation_frame': 'Date of Event'},
                    custom_data=[filtered_df[color], filtered_df['Date of Event'], filtered_df[arg_value[4],
                                                                                               arg_value[5]]]
                )
                fig.update_layout(
                    legend_title_text='Size: <br> &#9; {} ({})<br> <br>{}'.format(arg_value[4], arg_value[5],
                                                        legend_title_text), transition={'duration': 4000})
                fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1000
                # set up hover label
                hovertemplate = get_label('LBL_Bubble_Hover_Data', df_name)
                hovertemplate = hovertemplate.replace('%Date%', get_label('LBL_Date_of_Event', df_name)). \
                    replace('%Date-Value%', '%{customdata[1]}')
                hovertemplate = hovertemplate.replace('%AXIS-X-A%', arg_value[0]).replace('%AXIS-X-B%',
                   arg_value[1]).replace('%X-AXIS%', '%{x}')
                hovertemplate = hovertemplate.replace('%AXIS-Y-A%', arg_value[2]).replace('%AXIS-Y-B%',
                    arg_value[3]).replace('%Y-AXIS%', '%{y}')
                hovertemplate = hovertemplate.replace('%AXIS-Z-A%', arg_value[4]).replace('%AXIS-Z-B%',
                    arg_value[5]).replace('%Z-AXIS%', '%{customdata[2]}')
                fig.update_traces(hovertemplate=hovertemplate)
        # filtered is empty, create default empty graph
        else:
            fig = px.scatter(
                title=title + get_empty_graph_subtitle(hierarchy_toggle, hierarchy_level_dropdown, hierarchy_path,
                                                       {None}, arg_value[2], df_name, df_const))
    else:
        fig = px.scatter(
            title=get_empty_graph_subtitle(hierarchy_toggle, hierarchy_level_dropdown, hierarchy_path, {None},
                                           arg_value[2], df_name, df_const))

    # set title
    if xaxis_title:
        if arg_value[0] != 'Time' and xaxis_title == 'Time':
            xaxis_title = '{} ({})'.format(arg_value[0], arg_value[1])
        result = parse('{} ({})', xaxis_title)
        if result is None:
            xaxis = xaxis_title
        elif any(element in result[0] for element in df_const[session_key]['VARIABLE_OPTION_LISTS']) and \
                result[1] in df_const[session_key]["MEASURE_TYPE_VALUES"]:
            xaxis = '{} ({})'.format(arg_value[0], arg_value[1])
    elif arg_value[0] == 'Time' and (xaxis_title == 'Time' or xaxis_title is None):
        xaxis = '{}'.format(arg_value[0])
    else:
        xaxis = '{} ({})'.format(arg_value[0], arg_value[1])

    if yaxis_title:
        result = parse('{} ({})', yaxis_title)
        if result is None:
            yaxis = yaxis_title
        elif any(element in result[0] for element in df_const[session_key]['VARIABLE_OPTION_LISTS']) and \
                result[1] in df_const[session_key]["MEASURE_TYPE_VALUES"]:
            yaxis = '{} ({})'.format(arg_value[2], arg_value[3])
    else:
        yaxis = '{} ({})'.format(arg_value[2], arg_value[3])

    # set legend position
    if xlegend and ylegend:
        fig.update_layout(legend=dict(
            x=xlegend,
            y=ylegend
        ))

    fig.update_layout(
        xaxis_title=xaxis,
        yaxis_title=yaxis,
        showlegend=False if legend else True,
        overwrite=True,
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)')
    # checks for gridline is toggled
    if gridline:
        fig.update_xaxes(showgrid=True, zeroline=True, gridcolor='Gray')
        fig.update_yaxes(showgrid=True, zeroline=True, gridcolor='Gray')
    else:
        fig.update_xaxes(showgrid=False, zeroline=False)
        fig.update_yaxes(showgrid=False, zeroline=False)

    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=language.lower(), edits=dict(annotationPosition=False, annotationTail=False,
                                                        annotationText=False, colourbarPosition=False,
                                                        ColorbarTitleText=False, legendPosition=True,
                                                        legendText=False, shapePosition=False,
                                                        titleText=False, axisTitleText=True)),
        figure=fig)

    return graph


# bar graph layout TODO: VERTICAL TICKS OVERLAPPING WITH THE ANIMATION SLIDER
def get_bar_figure(arg_value, dff, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                   hierarchy_toggle, hierarchy_graph_children, tile_title, df_name, df_const, xaxis_title, yaxis_title,
                   xlegend, ylegend, gridline, legend, secondary_level_dropdown,
                   secondary_path, secondary_type, secondary_graph_children, session_key, heirarchy_type):
    """Returns the bar graph figure."""
    # ------------------------------------------------Arg Values--------------------------------------------------------
    # arg_value[0] = group by (x axis)
    # arg_value[1] = measure type selector
    # arg_value[2] = variable names selector
    # arg_value[3] = orientation
    # arg_value[4] = animation bool
    # ---------------------------------------Variable Declarations------------------------------------------------------
    language = session["language"]
    filtered_df = None
    # ------------------------------------------------------------------------------------------------------------------

    # Check whether we have enough information to attempt getting data for a graph
    if hierarchy_toggle == 'Level Filter' and None not in [arg_value, hierarchy_level_dropdown, hierarchy_toggle,
                                                         hierarchy_graph_children, df_name, df_const] \
            or hierarchy_toggle == 'Specific Item' and None not in [arg_value, hierarchy_path, hierarchy_toggle,
                                                                  hierarchy_graph_children, df_name, df_const]:
        # Specialty filtering
        filtered_df = dff.copy()
        if secondary_type == 'Level Filter':
            category = secondary_level_dropdown
        elif secondary_type == 'Specific Item' and secondary_graph_children == ['graph_children']:
            category = df_const[session_key]['SECONDARY_HIERARCHY_LEVELS'][len(secondary_path)]
        else:
            category = df_const[session_key]['SECONDARY_HIERARCHY_LEVELS'][len(secondary_path) - 1] \
                if len(secondary_path) != 0 else 'Variable Name'

        hierarchy_col = get_hierarchy_col(hierarchy_toggle, hierarchy_level_dropdown, hierarchy_graph_children,
                                          hierarchy_path, df_const, session_key)

        # hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
        if hierarchy_toggle == 'Level Filter' or (hierarchy_toggle == 'Specific Item' and
                                                hierarchy_graph_children == ['graph_children']):
            # Title setup
            if tile_title:
                title = tile_title
            else:
                if hierarchy_toggle == 'Level Filter':

                    if arg_value[0] == 'Variable Names':
                        title = '{}: {} vs {}'.format(get_label('LBL_' + hierarchy_level_dropdown, heirarchy_type),
                                                      get_label(arg_value[1], df_name+"_Measure_type"),
                                                      get_label('LBL_Variable_Names'))
                    else:
                        # Whole level graph title
                        title = '{0}: {1} vs {0}'.format(get_label('LBL_' + hierarchy_level_dropdown, heirarchy_type),
                                                         get_label(arg_value[1], df_name+"_Measure_type"))
                elif len(hierarchy_path) != 0:
                    # Specific item's children graph title
                    if language == 'En':
                        title = '{}\'s {}'.format(hierarchy_path[-1], get_label('LBL_Children'))
                    else:
                        title = '{} {}'.format(get_label('LBL_Children_Of'), hierarchy_path[-1])
                    if arg_value[0] == 'Variable Names':
                        title = title + ': {} vs {}'.format(get_label(arg_value[1], df_name+"_Measure_type"),
                                                            get_label('LBL_Variable_Names'))
                    else:
                        title = title + ': {} vs {}'.format(get_label(arg_value[1], df_name+"_Measure_type"),
                                                            hierarchy_path[-1])
                else:
                    if arg_value[0] == 'Variable Names':
                        title = '{}: {} vs {}'.format(get_label("LBL_Roots_Children"),
                                                      get_label(arg_value[1], df_name+"_Measure_type"),
                                                      get_label('LBL_Variable_Names'))
                    else:
                        # Root's children graph title
                        title = '{}: {} vs {}'.format(get_label("LBL_Roots_Children"),
                                                      get_label(arg_value[1], df_name+"_Measure_type"),
                                                      get_label('LBL_Root'))
        # hierarchy type is specific item while "Graph all in Dropdown" is unselected
        else:
            # Title setup
            if tile_title:
                title = tile_title
            else:
                # Generate title if there is no user entered title
                if arg_value[0] == 'Variable Names':
                    title = '{}: {} vs {}'.format(hierarchy_specific_dropdown,
                                                  get_label(arg_value[1], df_name+"_Measure_type"),
                                                  get_label('LBL_Variable_Names'))
                else:
                    if hierarchy_specific_dropdown:
                        title = '{}: {} vs {}'.format(hierarchy_specific_dropdown,
                                                      get_label(arg_value[1], df_name+"_Measure_type"),
                                                      get_label('LBL_Time'))
                    else:
                        if len(hierarchy_path) == 0:
                            title = ""
                        else:
                            title = '{}: {} vs {}'.format(hierarchy_path[-1],
                                                          get_label(arg_value[1], df_name+"_Measure_type"),
                                                          get_label('LBL_Time'))

        group_by_item = arg_value[0] != 'Variable Names'
        title += '<br><sub>{} {} </sub>'.format(get_label('LBL_Data_Accessed_On'), datetime.date(datetime.now()))

        # hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
        if hierarchy_toggle == 'Level Filter' or (hierarchy_toggle == 'Specific Item' and
                                                hierarchy_graph_children == ['graph_children']):
            # Axis and color logic
            if not group_by_item:
                x = category
                if hierarchy_toggle == 'Level Filter':
                    color = hierarchy_level_dropdown
                else:
                    color = df_const[session_key]['HIERARCHY_LEVELS'][len(hierarchy_path)]
            elif hierarchy_toggle == 'Level Filter':
                x = hierarchy_level_dropdown
                color = category
            else:
                x = df_const[session_key]['HIERARCHY_LEVELS'][len(hierarchy_path)]
                color = category
            legend_title_text = get_label('LBL_' + color.replace(' ', '_'), df_name)
        # hierarchy type is specific item while "Graph all in Dropdown" is unselected
        else:
            color = category if group_by_item else 'Partial Period'
            x = 'Date of Event' if group_by_item and not arg_value[3] else category
            legend_title_text = get_label('LBL_Variable_Name', df_name) if group_by_item else get_label(
                'LBL_Partial_Period', df_name)
            # if group_by_item and not arg_value[4]:
            #     xaxis = {'type': 'date'}

        # df is not empty, create graph
        if len(filtered_df) != 0:
            # filter the dataframe down to the partial period selected
            filtered_df['Partial Period'] = filtered_df['Partial Period'].astype(str).transform(
                lambda y: get_label('LBL_TRUE') if y != 'nan' else get_label('LBL_FALSE'))
            filtered_df['Date of Event'] = \
                filtered_df['Date of Event'].transform(lambda y: y.strftime(format='%Y-%m-%d'))

            # checks if arg_value[4]: animation is toggled
            # if arg_value[3] and (hierarchy_toggle == 'Level Filter' or (hierarchy_toggle == 'Specific Item' and
            #                                             hierarchy_graph_children == ['graph_children'])):
            #     # TODO: Remove in production when there is a full dataset
            #     for i in filtered_df['Date of Event'].unique():
            #         for j in filtered_df[hierarchy_col].unique():
            #             for k in filtered_df[color].unique():
            #                 if filtered_df.query(
            #                         "`Date of Event` == @i and `{}` == @j and `{}` == @k".format(x,
            #                                                                                      color)).empty:
            #                     filtered_df = filtered_df.append(
            #                         {'Date of Event': i, hierarchy_col: j, color: k, 'Measure Value': 0},
            #                         ignore_index=True)

            filtered_df.sort_values(by=['Date of Event', hierarchy_col, color], inplace=True)

            color_discrete = color_picker(arg_value[4])
            # generate graph
            fig = px.bar(
                title=title,
                data_frame=filtered_df,
                x=x if arg_value[2] == 'Vertical' else 'Measure Value',
                y='Measure Value' if arg_value[2] == 'Vertical' else x,
                orientation='v' if arg_value[2] == 'Vertical' else 'h',
                color=color,
                color_discrete_sequence=color_discrete,
                barmode='group',
                animation_frame='Date of Event' if arg_value[3] else None,
                custom_data=[hierarchy_col, color, 'Date of Event'])
            fig.update_layout(legend_title_text=legend_title_text)
            # set up hover label
            hovertemplate = get_label('LBL_Gen_Hover_Data', df_name)
            hovertemplate = hovertemplate.replace('%AXIS-TITLE-A%', get_label('LBL_Date_of_Event', df_name))
            hovertemplate = hovertemplate.replace('%AXIS-A%', '%{customdata[2]}').replace('%AXIS-TITLE-B%',
                                                  get_label(arg_value[1], df_name+"_Measure_type"))
            if arg_value[3]:
                fig.update_layout(transition={'duration': 2000})
                fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1000
            if arg_value[2] == 'Vertical':
                hovertemplate = hovertemplate.replace('%AXIS-B%', '%{y}')
            else:
                hovertemplate = hovertemplate.replace('%AXIS-B%', '%{x}')
            fig.update_traces(hovertemplate=hovertemplate)

            fig = set_partial_periods(fig, filtered_df, 'Bar')

        # filtered is empty, create default empty graph
        else:
            fig = px.bar(
                title=title + get_empty_graph_subtitle(hierarchy_toggle, hierarchy_level_dropdown, hierarchy_path,
                                                       secondary_type, secondary_path, df_name, df_const))
    else:
        fig = px.bar(
            title=get_empty_graph_subtitle(hierarchy_toggle, hierarchy_level_dropdown, hierarchy_path, secondary_type,
                                           secondary_path, df_name, df_const))

    # set title
    if arg_value[2] == 'Vertical':
        if xaxis_title != '' and xaxis_title is not None:
            xaxis = xaxis_title
        # default x-axis label
        else:
            xaxis = ''

        if yaxis_title not in df_const[session_key]["MEASURE_TYPE_VALUES"] and yaxis_title is not None:
            yaxis = yaxis_title
        # default y-axis label
        else:
            yaxis = get_label(arg_value[1], df_name+"_Measure_type")

    else:
        if yaxis_title not in df_const[session_key]["MEASURE_TYPE_VALUES"] and yaxis_title is not None:
            xaxis = yaxis_title
        else:
            xaxis = get_label(arg_value[1], df_name+"_Measure_type")

        if xaxis_title != '' and xaxis_title is not None:
            yaxis = xaxis_title
        else:
            yaxis = ''

    # set legend position
    if xlegend and ylegend:
        fig.update_layout(legend=dict(
            x=xlegend,
            y=ylegend
        ))

    fig.update_layout(
        # x and y-axis location change depending on graph arg_value[4] orientation
        xaxis_title=xaxis,
        yaxis_title=yaxis,
        showlegend=False if legend else True,
        overwrite=True,
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)')

    # checks for gridline is toggled
    if gridline:
        fig.update_xaxes(showgrid=True, zeroline=True, gridcolor='Gray')
        fig.update_yaxes(showgrid=True, zeroline=True, gridcolor='Gray')
    else:
        fig.update_xaxes(showgrid=False, zeroline=False)
        fig.update_yaxes(showgrid=False, zeroline=False)

    # set ranges
    if arg_value[3]:
        if arg_value[2] == 'Vertical':
            fig.update_yaxes(range=[0, filtered_df['Measure Value'].max()])
        else:
            fig.update_xaxes(range=[0, filtered_df['Measure Value'].max()])

    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=language.lower(), edits=dict(annotationPosition=False, annotationTail=False,
                                                        annotationText=False, colourbarPosition=False,
                                                        ColorbarTitleText=False, legendPosition=True,
                                                        legendText=False, shapePosition=False,
                                                        titleText=False, axisTitleText=True)),
        figure=fig)

    return graph


def get_box_figure(arg_value, dff, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                   hierarchy_toggle, hierarchy_graph_children, tile_title, df_name, df_const, xaxis_title, yaxis_title,
                   xlegend, ylegend, gridline, legend, secondary_level_dropdown, secondary_path, secondary_type,
                   secondary_graph_children, session_key, heirarchy_type):
    """Returns the box plot figure."""
    # ------------------------------------------------Arg Values--------------------------------------------------------
    # arg_value[0] = measure type selector
    # arg_value[1] = orientation toggle
    # arg_value[2] = variable selector
    # arg_value[3] = data points toggle
    # ---------------------------------------Variable Declarations------------------------------------------------------
    language = session["language"]
    # ------------------------------------------------------------------------------------------------------------------

    # Check on whether we have enough information to attempt to get data for a graph
    if hierarchy_toggle == 'Level Filter' and None not in [arg_value, hierarchy_level_dropdown, hierarchy_toggle,
                                                         hierarchy_graph_children, df_name, df_const] \
            or hierarchy_toggle == 'Specific Item' and None not in [arg_value, hierarchy_path, hierarchy_toggle,
                                                                  hierarchy_graph_children, df_name, df_const]:
        # Specialty filtering
        filtered_df = dff.copy()
        if secondary_type == 'Level Filter':
            category = secondary_level_dropdown
        elif secondary_type == 'Specific Item' and secondary_graph_children == ['graph_children']:
            category = df_const[session_key]['SECONDARY_HIERARCHY_LEVELS'][len(secondary_path)]
        else:
            category = df_const[session_key]['SECONDARY_HIERARCHY_LEVELS'][len(secondary_path) - 1] if \
                len(secondary_path) != 0 else 'Vairable Name'

        # hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
        if hierarchy_toggle == 'Level Filter' or (hierarchy_toggle == 'Specific Item' and
                                                hierarchy_graph_children == ['graph_children']):
            # Title setup
            if tile_title:
                title = tile_title
            else:
                if hierarchy_toggle == 'Level Filter':
                    # Whole level graph title
                    title = '{}: {} {}'.format(get_label('LBL_' + hierarchy_level_dropdown, heirarchy_type),
                                               get_label(arg_value[0], df_name+"_Measure_type"),
                                               get_label('LBL_Distribution'))
                elif len(hierarchy_path) != 0:
                    # Specific item's children graph title
                    if language == 'En':
                        title = '{}\'s {}'.format(hierarchy_path[-1], get_label('LBL_Children'))
                    else:
                        title = '{} {}'.format(get_label('LBL_Children_Of'), hierarchy_path[-1])
                    title = title + ': {} {}'.format(get_label(arg_value[0], df_name+"_Measure_type"),
                                                     get_label('LBL_Distribution'))
                else:
                    # Roots children graph title
                    title = '{}: {} {}'.format(get_label("LBL_Roots_Children"),
                                               get_label(arg_value[0], df_name+"_Measure_type"),
                                               get_label('LBL_Distribution'))
        # hierarchy type is specific item while "Graph all in Dropdown" is unselected
        else:
            # Title setup
            if tile_title:
                title = tile_title
            else:
                if hierarchy_specific_dropdown:
                    title = '{}: {} {}'.format(hierarchy_specific_dropdown,
                                               get_label(arg_value[0], df_name+"_Measure_type"),
                                               get_label('LBL_Distribution'))
                else:
                    if len(hierarchy_path) == 0:
                        title = ""
                    else:
                        title = '{}: {} {}'.format(hierarchy_path[-1],
                                                   get_label(arg_value[0], df_name+"_Measure_type"),
                                                   get_label('LBL_Distribution'))

        # df is not empty, create graph
        if len(filtered_df) != 0:
            title += '<br><sub>{} {} </sub>'.format(get_label('LBL_Data_Accessed_On'), datetime.date(datetime.now()))

            # if hierarchy type is "Level Filter", or "Specific Item" while "Graph all in Dropdown" is selected
            if hierarchy_toggle == 'Level Filter' or (hierarchy_toggle == 'Specific Item' and
                                                    hierarchy_graph_children == ['graph_children']):
                x = 'Measure Value'
                if hierarchy_toggle == 'Level Filter':
                    y = hierarchy_level_dropdown
                else:
                    y = df_const[session_key]['HIERARCHY_LEVELS'][len(hierarchy_path)]
                filtered_df.sort_values(by=[category, y, x], inplace=True)
            # hierarchy type is specific item while "Graph all in Dropdown" is unselected
            else:
                x = 'Measure Value'
                y = None
                filtered_df.sort_values(by=[category, 'Measure Value'], inplace=True)

            # filter the dataframe down to the partial period selected
            filtered_df['Date of Event'] = filtered_df['Date of Event'].transform(
                lambda i: i.strftime(format='%Y-%m-%d'))
            filtered_df['Partial Period'] = filtered_df['Partial Period'].astype(str).transform(
                lambda j: get_label('LBL_TRUE') if j == 'True' else get_label('LBL_FALSE'))

            color_discrete = color_picker(arg_value[3])
            # generate graph
            fig = px.box(
                title=title,
                data_frame=filtered_df,
                # check arg_value[1]: orientation assign to corresponding x and y-axis
                x=x if arg_value[1] == 'Horizontal' else y,
                y=y if arg_value[1] == 'Horizontal' else x,
                color=category,
                color_discrete_sequence=color_discrete,
                points='all' if arg_value[2] else False)

            fig.update_layout(legend_title_text=get_label('LBL_Variable_Names'))
        # filtered is empty, create default empty graph
        else:
            fig = px.box(
                title=title + get_empty_graph_subtitle(hierarchy_toggle, hierarchy_level_dropdown, hierarchy_path,
                                                       secondary_type, secondary_path, df_name, df_const))
    else:
        fig = px.box(
            title=get_empty_graph_subtitle(hierarchy_toggle, hierarchy_level_dropdown, hierarchy_path, secondary_type,
                                           secondary_path, df_name, df_const))

    # set title
    # x and y-axis location change depending on graph arg_value[1]: orientation
    if arg_value[1] == 'Horizontal':
        if xaxis_title not in df_const[session_key]["MEASURE_TYPE_VALUES"] and xaxis_title is not None:
            xaxis = xaxis_title
        else:
            xaxis = get_label(arg_value[0], df_name + "_Measure_type")

        if yaxis_title != '' and yaxis_title is not None:
            yaxis = yaxis_title
        else:
            yaxis = ''
    else:
        if xaxis_title not in df_const[session_key]["MEASURE_TYPE_VALUES"] and xaxis_title is not None:
            yaxis = xaxis_title
        else:
            yaxis = get_label(arg_value[0], df_name + "_Measure_type")

        if yaxis_title != '' and yaxis_title is not None:
            xaxis = yaxis_title
        else:
            xaxis = ''

    # set legend position
    if xlegend and ylegend:
        fig.update_layout(legend=dict(
            x=xlegend,
            y=ylegend
        ))

    fig.update_layout(
        xaxis_title=xaxis,
        yaxis_title=yaxis,
        legend_title_text=get_label('LBL_Variable_Names'),
        showlegend=False if legend else True,
        boxgap=0.1,
        boxgroupgap=0.5,
        overwrite=True,
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)')

    # checks for gridline is toggled
    if gridline:
        fig.update_xaxes(showgrid=True, zeroline=True, gridcolor='Gray')
        fig.update_yaxes(showgrid=True, zeroline=True, gridcolor='Gray')
    else:
        fig.update_xaxes(showgrid=False, zeroline=False)
        fig.update_yaxes(showgrid=False, zeroline=False)

    graph = dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=language.lower(), edits=dict(annotationPosition=False, annotationTail=False,
                                                        annotationText=False, colourbarPosition=False,
                                                        ColorbarTitleText=False, legendPosition=True,
                                                        legendText=False, shapePosition=False,
                                                        titleText=False, axisTitleText=True)),
        figure=fig)

    return graph


def get_table_figure(arg_value, dff, tile, hierarchy_specific_dropdown, hierarchy_level_dropdown, hierarchy_path,
                     hierarchy_toggle, hierarchy_graph_children, tile_title, df_name, heirarchy_type):
    """Returns the table figure."""
    # ------------------------------------------------Arg Values--------------------------------------------------------
    # arg_value[0] = tile index
    # arg_value[1] = page_size
    # ---------------------------------------Variable Declarations------------------------------------------------------
    language = session["language"]
    title = ''
    # Clean dataframe to display nicely
    dff = dff.dropna(how='all', axis=1)
    # ------------------------------------------------------------------------------------------------------------------

    # use special data title if no data
    if hierarchy_toggle == 'Level Filter' and None in [arg_value, hierarchy_level_dropdown, hierarchy_toggle,
                                                     hierarchy_graph_children, df_name] \
            or hierarchy_toggle == 'Specific Item' and None in [arg_value, hierarchy_path, hierarchy_toggle,
                                                              hierarchy_graph_children, df_name]:
        if df_name is None:
            title = '{}'.format(get_label('LBL_No_Data_Found'))
        elif hierarchy_toggle == 'Level Filter' and hierarchy_level_dropdown is None \
                or hierarchy_toggle == 'Specific Item' and not hierarchy_path:
            title = '{}'.format(get_label('LBL_Make_A_Hierarchy_Selection'))
    # use manual title, if any
    elif tile_title:
        title = tile_title
    # no manual title and filtering based on level, use level selection as title
    elif hierarchy_toggle == 'Level Filter':
        title = get_label('LBL_' + hierarchy_level_dropdown, heirarchy_type)
    # no manual title and filtering based on specific item
    else:
        # "graph all in dropdown" is selected
        if hierarchy_graph_children == ['graph_children']:
            # if not roots children
            if len(hierarchy_path) != 0:
                # Specific item's children graph title
                if language == 'En':
                    title = '{}\'s {}'.format(hierarchy_path[-1], get_label('LBL_Children'))
                else:
                    title = '{} {}'.format(get_label('LBL_Children_Of'), hierarchy_path[-1])
            # Roots children graph title
            else:
                title = '{}'.format(get_label("LBL_Roots_Children"))
        # "graph all in dropdown" is unselected
        else:
            if hierarchy_specific_dropdown:
                title = '{}'.format(hierarchy_specific_dropdown)
            else:
                if len(hierarchy_path) == 0:
                    title = ""
                else:
                    title = '{}'.format(hierarchy_path[-1])

    # Create table
    # If dataframe has a link column Links should be displayed in markdown w/ the form (https://www.---------):
    columns_for_dash_table = []

    for i in dff.columns:
        if i == "Link":
            columns_for_dash_table.append(
                {"name": get_label("LBL_Link", df_name), "id": i, "type": "text", "presentation": "markdown",
                 "hideable": True})
        else:
            columns_for_dash_table.append(
                {"name": get_label('LBL_' + i.replace(' ', '_'), df_name), "id": i, "hideable": True})

    cond_style = []

    # appends dff columns to build the table
    for col in dff.columns:
        name_length = len(get_label('LBL_' + col.replace(' ', '_')))
        pixel = 50 + round(name_length * 6)
        pixel = str(pixel) + "px"
        cond_style.append({'if': {'column_id': col}, 'minWidth': pixel})

    cond_style.append({'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'})

    cond_style.append(
        {'if': {'column_id': 'Link'}, 'cursor': 'pointer', 'color': 'blue', 'text-decoration': 'underline',
        'overflow': 'hidden',
        'maxWidth': 0})

    # check arg_value[1]: num of pages is a whole integer if not assign 10
    if arg_value[1] is None or type(arg_value[1]) is not int:
        arg_value[1] = 10

    table = html.Div([
        html.Div(style={'height': '28px'}),
        html.Plaintext(title,
                       style={'font-family': 'Open Sans, verdana, arial, sans-serif', 'font-size': '17px',
                              'white-space': 'pre', 'margin': '0', 'margin-left': 'calc(5% - 9px)',
                              'cursor': 'default'}),
        html.Sub('{} {}'.format(get_label('LBL_Data_Accessed_On'), datetime.date(datetime.now())),
                 style={'margin-left': 'calc(5% - 9px)', 'cursor': 'default', 'font-size': '12px',
                        'font-family': '"Open Sans", verdana, arial, sans-serif'}),
        dash_table.DataTable(
            id={'type': 'datatable', 'index': tile},
            columns=columns_for_dash_table,

            page_current=0,
            page_size=int(arg_value[1]),
            page_action="custom",

            filter_action='custom',
            filter_query='',

            sort_action='custom',
            sort_mode='multi',
            sort_by=[],

            cell_selectable=False,
            style_cell={'textAlign': 'left'},
            style_data_conditional=cond_style,

            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},

            style_table={'margin-top': '10px', 'overflow': 'auto'},
        ),
        dcc.Store(id={'type': 'tile-df-name', 'index': tile}, data=df_name)],
        style={'height': '90%', 'width': 'auto', 'overflow-y': 'auto', 'overflow-x': 'hidden',
                   'margin-left': '10px', 'margin-right': '10px'})

    return table


def get_sankey_figure(dff, hierarchy_level_dropdown, hierarchy_path, hierarchy_toggle, tile_title, df_name,
                      df_const, secondary_level_dropdown, secondary_path, secondary_type,
                      secondary_graph_children, secondary_options, session_key):
    """Returns the sankey graph figure."""
    # ------------------------------------------------Arg Values--------------------------------------------------------
    # arg_value[0] = variable selector
    # ------------------------------------------Variable Declarations---------------------------------------------------
    language = session["language"]
    title = tile_title
    # ------------------------------------------------------------------------------------------------------------------

    # Specialty filtering
    filtered_df = customize_menu_filter(dff, 'Link', df_const, secondary_path,
                                        secondary_type, secondary_level_dropdown, secondary_graph_children,
                                        secondary_options, session_key)

    # df is not empty, create empty sankey graph
    if len(filtered_df) == 0:
        title += get_empty_graph_subtitle(hierarchy_toggle, hierarchy_level_dropdown, hierarchy_path, secondary_type,
                                           secondary_path, df_name, df_const)
        return dcc.Graph(
            id='graph-display',
            className='fill-container',
            responsive=True,
            config=dict(locale=language.lower()),
            figure=go.Figure(
                layout={'title_text': title, 'plot_bgcolor': 'rgba(0, 0, 0, 0)', 'paper_bgcolor': 'rgba(0, 0, 0, 0)'},
                data=[go.Sankey()]))

    title += '<br><sub>{} {} </sub>'.format(get_label('LBL_Data_Accessed_On'), datetime.date(datetime.now()))

    node_df = session[df_name + "_NodeData"]

    label_numpy = []
    custom_numpy = []
    x_numpy = []
    y_numpy = []
    node_colour_numpy = []

    for index, row in node_df.iterrows():
        label_numpy.append(get_label("LBL_" + row['node_id'], df_name))
        custom_numpy.append(get_label("".join(["LBL_", row['node_id'], '_Long']), df_name))
        x_numpy.append(row['x_coord'])
        y_numpy.append(row['y_coord'])
        node_colour_numpy.append(row['colour'])

    source_numpy = []
    target_numpy = []
    value_numpy = []
    link_colour_numpy = []

    for index, row in filtered_df.iterrows():
        source_numpy.append(row['Measure Id'])
        target_numpy.append(row['MeasQual1'])
        value_numpy.append(row['MeasQual2'])
        link_colour_numpy.append(node_colour_numpy[int(row['Measure Id'])])

    # set up hover labels
    node_hover_template = get_label('LBL_Node_HoverTemplate', df_name)
    node_hover_template = node_hover_template.replace("%VALUE%", "%{value}")
    node_hover_template = node_hover_template.replace("%NODE%", "%{customdata}")
    link_hover_template = get_label("LBL_Link_HoverTemplate", df_name)
    link_hover_template = link_hover_template.replace("%VALUE%", "%{value}")
    link_hover_template = link_hover_template.replace("%SOURCE-NODE%", "%{source.customdata}")
    link_hover_template = link_hover_template.replace("%TARGET-NODE%", "%{target.customdata}")

    fig = go.Figure(data=[go.Sankey(
        # arrangement
        # valueformat
        # valuesuffix
        node=dict(
            pad=15,
            # thickness=20,
            # line=dict(color="black", width=0.5),
            label=label_numpy,  # label=["A1", "A2", "B1", "B2", "C1", "C2"],
            x=x_numpy,
            y=y_numpy,
            customdata=custom_numpy,
            hovertemplate=node_hover_template,
            color=node_colour_numpy
        ),
        link=dict(
            source=source_numpy,  # source=[0, 1, 0, 2, 3, 3],  # indices correspond to labels, eg A1, A2, A2, B1, ...
            target=target_numpy,  # target=[2, 3, 3, 4, 4, 5],
            value=value_numpy,  # value=[8, 4, 2, 8, 4, 2]
            # customdata
            hovertemplate=link_hover_template,
            color=link_colour_numpy
            # label
        )
    )])

    fig.update_layout(
        # hovermode
        # plot_bgcolor
        # paper_bgcolor
        title_text=title,
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)')  # ,
    # font=dict(size=19, color='white'),
    # font_size=10)

    return dcc.Graph(
        id='graph-display',
        className='fill-container',
        responsive=True,
        config=dict(locale=language.lower()),
        figure=fig)


def __update_graph(df_name, graph_options, graph_type, graph_title, num_periods, period_type,
                   hierarchy_toggle, hierarchy_level_dropdown, hierarchy_graph_children, hierarchy_options,
                   state_of_display, secondary_type, timeframe, fiscal_toggle, start_year, end_year, start_secondary,
                   end_secondary, df_const, xtitle, ytitle, xlegend, ylegend, gridline, legend,
                   secondary_level_dropdown, secondary_state_of_display, secondary_toggle,
                   secondary_graph_children, secondary_options, session_key, hierarchy_type):
    """Update graph internal - can be called from callbacks or programmatically"""
    # Creates a hierarchy trail from the display
    if type(state_of_display) == dict:
        state_of_display = [state_of_display]

    list_of_names = []

    if len(state_of_display) > 0:
        for obj in state_of_display:
            list_of_names.append(obj['props']['children'])

    if hierarchy_toggle == 'Specific Item' and hierarchy_graph_children == ['graph_children']:
        # If at a leaf node then display its parents data
        nid_path = "root"
        for x in list_of_names:
            nid_path += ('^||^{}'.format(x))
        if not hierarchy_options:
            list_of_names.pop()

    # hierarchy specific dropdown selection is last item in list_of_names, otherwise None
    hierarchy_specific_dropdown = list_of_names[-1] if len(list_of_names) > 0 else None

    # Creates a secondary hierarchy trail from the display
    if type(secondary_state_of_display) == dict:
        secondary_state_of_display = [secondary_state_of_display]

    list_of_secondary_names = []

    if len(secondary_state_of_display) > 0:
        for obj in secondary_state_of_display:
            list_of_secondary_names.append(obj['props']['children'])

    if secondary_toggle == 'Specific Item' and secondary_graph_children == ['graph_children']:
        # If at a leaf node then display its parents data
        nid_path = "root"
        for x in list_of_secondary_names:
            nid_path += ('^||^{}'.format(x))
        if not secondary_options:
            list_of_secondary_names.pop()

    # If "Last ___ ____" is active and the num_periods is invalid (None), return an empty graph
    if timeframe == 'to-current' and not num_periods:
        filtered_df = pd.DataFrame(columns=df_const[session_key]['COLUMN_NAMES'])
    # else, filter normally
    else:
        filtered_df = data_manipulator(list_of_names, hierarchy_toggle, hierarchy_level_dropdown,
                                       hierarchy_graph_children, df_name, df_const, secondary_type, end_secondary,
                                       end_year, start_secondary, start_year, timeframe, fiscal_toggle, num_periods,
                                       period_type, graph_options, graph_type, list_of_secondary_names,
                                       secondary_toggle, secondary_level_dropdown, secondary_graph_children,
                                       secondary_options, session_key)

    # line and scatter graph creation
    if graph_type == 'Line' or graph_type == 'Scatter':
        return get_line_scatter_figure(graph_options, filtered_df, hierarchy_specific_dropdown,
                                       hierarchy_level_dropdown, list_of_names, hierarchy_toggle,
                                       hierarchy_graph_children, graph_title, df_name, df_const, xtitle, ytitle,
                                       xlegend, ylegend, gridline, legend,
                                       secondary_level_dropdown, list_of_secondary_names, secondary_toggle,
                                       secondary_graph_children, session_key, hierarchy_type)
    # bubble graph creation
    elif graph_type == 'Bubble':
        return get_bubble_figure(graph_options, filtered_df, hierarchy_specific_dropdown, hierarchy_level_dropdown,
                                 list_of_names, hierarchy_toggle, hierarchy_graph_children, graph_title, df_name,
                                 df_const, xtitle, ytitle, xlegend, ylegend, gridline, legend, session_key,
                                 hierarchy_type)
    # bar graph creation
    elif graph_type == 'Bar':
        return get_bar_figure(graph_options, filtered_df, hierarchy_specific_dropdown, hierarchy_level_dropdown,
                              list_of_names, hierarchy_toggle, hierarchy_graph_children, graph_title, df_name,
                              df_const, xtitle, ytitle, xlegend, ylegend, gridline, legend,
                              secondary_level_dropdown, list_of_secondary_names, secondary_toggle,
                              secondary_graph_children, session_key, hierarchy_type)
    # box plot creation
    elif graph_type == 'Box_Plot':
        return get_box_figure(graph_options, filtered_df, hierarchy_specific_dropdown, hierarchy_level_dropdown,
                              list_of_names, hierarchy_toggle, hierarchy_graph_children, graph_title, df_name,
                              df_const, xtitle, ytitle, xlegend, ylegend, gridline, legend,
                              secondary_level_dropdown, list_of_secondary_names, secondary_toggle,
                              secondary_graph_children, session_key, hierarchy_type)
    # table creation
    elif graph_type == 'Table':
        changed_index = dash.callback_context.inputs_list[2]['id']['index']
        return get_table_figure(graph_options, filtered_df, changed_index, hierarchy_specific_dropdown,
                                hierarchy_level_dropdown, list_of_names, hierarchy_toggle, hierarchy_graph_children,
                                graph_title, df_name, hierarchy_type)
    # sankey creation
    elif graph_type == 'Sankey':
        return get_sankey_figure(filtered_df, hierarchy_level_dropdown, list_of_names, hierarchy_toggle,
                                 graph_title, df_name, df_const, secondary_level_dropdown, list_of_secondary_names,
                                 secondary_toggle, secondary_graph_children, secondary_options, session_key)
    # If no graph_type is given
    else:
        return None


# different colour palette colour hex codes
def color_picker(palette):
    if palette == 'G10':
        color = ["#3366CC", "#DC3912", "#FF9900", "#109618", "#990099",
                 "#0099C6", "#DD4477", "#66AA00", "#B82E2E", "#316395"]
    elif palette == 'Bold':
        color = ["rgb(127, 60, 141)", "rgb(17, 165, 121)", "rgb(57, 105, 172)", "rgb(242, 183, 1)",
                 "rgb(231, 63, 116)", "rgb(128, 186, 90)", "rgb(230, 131, 16)", "rgb(0, 134, 149)",
                 "rgb(207, 28, 144)", "rgb(249, 123, 114)", "rgb(165, 170, 153)"]
    elif palette == 'Vivid':
        color = ["rgb(229, 134, 6)", "rgb(93, 105, 177)", "rgb(82, 188, 163)", "rgb(153, 201, 69)",
                 "rgb(204, 97, 176)", "rgb(36, 121, 108)", "rgb(218, 165, 27)", "rgb(47, 138, 196)",
                 "rgb(118, 78, 159)", "rgb(237, 100, 90)", "rgb(165, 170, 153)"]
    elif palette == 'Dark24':
        color = ["#2E91E5", "#E15F99", "#1CA71C", "#FB0D0D", "#DA16FF", "#222A2A", "#B68100", "#750D86",
                 "#EB663B", "#511CFB", "#00A08B", "#FB00D1", "#FC0080", "#B2828D", "#6C7C32", "#778AAE",
                 "#862A16", "#A777F1", "#620042", "#1616A7", "#DA60CA", "#6C4516", "#0D2A63", "#AF0038"]
    elif palette == 'Pastel':
        color = ["rgb(102, 197, 204)", "rgb(246, 207, 113)", "rgb(248, 156, 116)", "rgb(220, 176, 242)",
                 "rgb(135, 197, 95)", "rgb(158, 185, 243)", "rgb(254, 136, 177)", "rgb(201, 219, 116)",
                 "rgb(139, 224, 164)", "rgb(180, 151, 231)", "rgb(179, 179, 179)"]
    else:
        # color blind friendly palette
        color = ["#000000", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"]
    return color
