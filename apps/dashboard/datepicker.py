######################################################################################################################
"""
datepicker.py

Stores the layout and helper functions for date picker.
"""
######################################################################################################################

# External Packages
from flask import session
import dash_core_components as dcc
import dash_html_components as html

# Internal Modules
from apps.dashboard.data import get_label

# ********************************************DATE-PICKER LAYOUT**************************************************


def get_date_picker(tile, df_name, fiscal_toggle, input_method, num_periods, period_type, df_const,session_key):
    """Returns the date picker layout."""
    language = session["language"]

    if df_name:
        children = [
            html.H6(
                '{}:'.format(get_label("LBL_Calendar_Type")),
                style={'margin-top': '20px', 'color': 'black'} if df_const[session_key]['FISCAL_AVAILABLE']
                else {'display': 'None'}),
            dcc.Tabs([
                dcc.Tab(label="{}".format(get_label("LBL_Gregorian")), value='Gregorian'),
                dcc.Tab(label="{}".format(get_label("LBL_Fiscal")), value='Fiscal')],
                id={'type': 'fiscal-year-toggle', 'index': tile},
                className='toggle-tabs-wrapper',
                value=fiscal_toggle,
                style={'display': 'block', 'text-align': 'center'} if df_const[session_key]['FISCAL_AVAILABLE']
                else {'display': 'none'}),
            html.Div(
                children=[
                    html.H6(
                        '{}:'.format(get_label("LBL_Timeframe")),
                        className='date-picker-option-title'),
                    html.I(
                        html.Span(
                            get_label("LBL_Date_Picker_Info"),
                            className='save-symbols-tooltip'),
                        className='fa fa-question-circle-o',
                        id={'type': 'date-picker-info', 'index': tile},
                        style={'position': 'relative'}),
                ],
                id={'type': 'date-picker-info-wrapper', 'index': tile}
            ),
            dcc.RadioItems(
                id={'type': 'radio-timeframe', 'index': tile},
                options=[
                    {'label': get_label('LBL_All_Time_Monthly'),
                     'value': 'all-time'},
                    {'label': '{}'.format(
                        get_label('LBL_Last') if language == 'En' else '........... ' + get_label('LBL_Last')),
                        'value': 'to-current'},
                    {'label': get_label('LBL_Select_Range'),
                     'value': 'select-range'}],
                value=input_method,
                className='seperated-radio-buttons',
                style={'margin-left': '15px', 'color': 'black'}),
            html.Div([
                dcc.Input(
                    id={'type': 'num-periods', 'index': tile},
                    className='num-periods',
                    value=num_periods,
                    disabled=input_method != 'to-current',
                    type='number',
                    required=True,
                    min=1,
                    style={'width': '45px', 'height': '29px', 'margin': '0', 'padding': '0', 'font-size': '15px',
                           'text-align': 'center', 'padding-top': '3px', 'border-radius': '5px', 'color': '#333',
                           'max-height': '26px'})
            ], style={'width': '0', 'height': '0', 'position': 'relative', 'bottom': '55px',
                      'left': '73px' if language == 'En' else '36px'}),
            html.Div([
                dcc.Dropdown(
                    id={'type': 'period-type', 'index': tile},
                    options=[
                        {'label': get_label('LBL_Years'),
                         'value': 'last-years'},
                        {'label': get_label('LBL_Quarters'),
                         'value': 'last-quarters'},
                        {'label': get_label('LBL_Months'),
                         'value': 'last-months'},
                        {'label': get_label('LBL_Weeks'),
                         'value': 'last-weeks'}],
                    value=period_type,
                    disabled=input_method != 'to-current',
                    clearable=False,
                    style={'width': '110px', 'height': '26px', 'margin': '0', 'padding': '0', 'font-size': '15px',
                           'display': 'flow-root', 'text-align': 'center', 'border-radius': '5px', 'color': '#333',
                           'max-height': '26px'})
            ], style={'width': '0', 'height': '0', 'position': 'relative', 'bottom': '55px',
                      'left': '125px' if language == 'En' else '150px'}),
            html.Div([
                # placeholders for datepicker inputs to avoid callback errors.
                # Inputs are initialized to 1 so that they are
                # only 'None' if an invalid date has been entered.
                html.Div([
                    html.Button(id={'type': 'date-picker-year-button', 'index': tile}),
                    html.Button(id={'type': 'date-picker-quarter-button', 'index': tile}),
                    html.Button(id={'type': 'date-picker-month-button', 'index': tile}),
                    html.Button(id={'type': 'date-picker-week-button', 'index': tile}),
                    dcc.Input(
                        id={'type': 'start-year-input', 'index': tile},
                        value=1),
                    dcc.Input(
                        id={'type': 'end-year-input', 'index': tile},
                        value=1),
                    dcc.Input(
                        id={'type': 'start-secondary-input', 'index': tile},
                        value=1),
                    dcc.Input(
                        id={'type': 'end-secondary-input', 'index': tile},
                        value=1),
                ], style={'width': '0', 'height': '0', 'overflow': 'hidden'})
            ], id={'type': 'div-date-range-selection', 'index': tile}),
            html.P(
                "{}: {} - {}".format(get_label('LBL_Available'), df_const[session_key]['MIN_DATE_UNF'],
                                     df_const[session_key]['MAX_DATE_UNF']),
                className='time-available'),
            # date picker trigger boolean for use in chaining update_date_picker to update_graph
            html.Div(
                id={'type': 'date-picker-trigger', 'index': tile},
                **{'data-boolean': True},
                style={'display': 'none'}),
            # date picker trigger that stores master select range data for use in setting select range when
            # forced un-linking
            html.Div(
                id={'type': 'update-date-picker-trigger', 'index': tile},
                **{'data-boolean': {}},
                style={'display': 'none'})
        ]
    else:
        children = [
            html.H6(
                '{}:'.format(get_label("LBL_Calendar_Type")),
                className='date-picker-option-title'),
            dcc.Tabs([
                dcc.Tab(label="{}".format(get_label("LBL_Gregorian")), value='Gregorian'),
                dcc.Tab(label="{}".format(get_label("LBL_Fiscal")), value='Fiscal')],
                id={'type': 'fiscal-year-toggle', 'index': tile},
                className='toggle-tabs-wrapper',
                value=fiscal_toggle,
                style={'display': 'block', 'text-align': 'center'}),
            html.Div(
                children=[
                    html.H6(
                        '{}:'.format(get_label("LBL_Timeframe")),
                        className='date-picker-option-title'),
                    html.I(
                        html.Span(
                            get_label("LBL_Date_Picker_Info"),
                            className='save-symbols-tooltip'),
                        className='fa fa-question-circle-o',
                        id={'type': 'date-picker-info', 'index': tile},
                        style={'position': 'relative'})],
                id={'type': 'date-picker-info-wrapper', 'index': tile}
            ),
            dcc.RadioItems(
                id={'type': 'radio-timeframe', 'index': tile},
                options=[
                    {'label': get_label('LBL_All_Time_Monthly'),
                     'value': 'all-time'},
                    {'label': '{}'.format(
                        get_label('LBL_Last') if language == 'En' else '........... ' + get_label('LBL_Last')),
                        'value': 'to-current'},
                    {'label': get_label('LBL_Select_Range'),
                     'value': 'select-range'}],
                value=input_method,
                className='seperated-radio-buttons',
                style={'margin-left': '15px', 'color': 'black'}),
            html.Div([
                dcc.Input(
                    id={'type': 'num-periods', 'index': tile},
                    className='num-periods',
                    value=num_periods,
                    disabled=input_method != 'to-current',
                    type='number',
                    required=True,
                    min=1,
                    style={'width': '45px', 'height': '29px', 'margin': '0', 'padding': '0', 'font-size': '15px',
                           'text-align': 'center', 'padding-top': '3px', 'border-radius': '5px', 'color': '#333',
                           'max-height': '26px'})
            ], style={'width': '0', 'height': '0', 'position': 'relative', 'bottom': '55px',
                      'left': '73px' if language == 'En' else '36px'}),
            html.Div([
                dcc.Dropdown(
                    id={'type': 'period-type', 'index': tile},
                    options=[
                        {'label': get_label('LBL_Years'),
                         'value': 'last-years'},
                        {'label': get_label('LBL_Quarters'),
                         'value': 'last-quarters'},
                        {'label': get_label('LBL_Months'),
                         'value': 'last-months'},
                        {'label': get_label('LBL_Weeks'),
                         'value': 'last-weeks'}],
                    value=period_type,
                    disabled=input_method != 'to-current',
                    clearable=False,
                    style={'width': '110px', 'height': '26px', 'margin': '0', 'padding': '0', 'font-size': '15px',
                           'text-align': 'center', 'border-radius': '5px', 'color': '#333', 'max-height': '26px'})
            ], style={'width': '0', 'height': '0', 'position': 'relative', 'bottom': '55px',
                      'left': '125px' if language == 'En' else '150px'}),
            html.P("{}: {} - {}".format(get_label('LBL_Available'), '_', '_'),
                   className='time-available'),
            html.Div([
                # placeholders for datepicker inputs to avoid callback errors. Inputs are initialized to 1 so that they
                # are only 'None' if an invalid date has been entered.
                html.Div([
                    html.Button(id={'type': 'date-picker-year-button', 'index': tile}),
                    html.Button(id={'type': 'date-picker-quarter-button', 'index': tile}),
                    html.Button(id={'type': 'date-picker-month-button', 'index': tile}),
                    html.Button(id={'type': 'date-picker-week-button', 'index': tile}),
                    dcc.Input(
                        id={'type': 'start-year-input', 'index': tile},
                        value=1),
                    dcc.Input(
                        id={'type': 'end-year-input', 'index': tile},
                        value=1),
                    dcc.Input(
                        id={'type': 'start-secondary-input', 'index': tile},
                        value=1),
                    dcc.Input(
                        id={'type': 'end-secondary-input', 'index': tile},
                        value=1),
                ], style={'width': '0', 'height': '0', 'overflow': 'hidden'})
            ], id={'type': 'div-date-range-selection', 'index': tile},
                style={'padding-bottom': '20px'}),
            # date picker trigger boolean for use in chaining update_date_picker to update_graph
            html.Div(
                id={'type': 'date-picker-trigger', 'index': tile},
                **{'data-boolean': True},
                style={'display': 'none'}),
            # date picker trigger that stores master select range data for use in setting select range when
            # forced un-linking
            html.Div(
                id={'type': 'update-date-picker-trigger', 'index': tile},
                **{'data-boolean': {}},
                style={'display': 'none'})
        ]

    return children

# ********************************************DATE-PICKER FUNCTIONS**************************************************


def get_date_box(index, value, minimum, maximum, name=None):
    """Returns date picker input box"""
    return dcc.Input(id=index,
                     type='number',
                     value=value,
                     min=minimum,
                     max=maximum,
                     name=name,
                     required=True,
                     style={'width': '100%'})


def get_secondary_data(conditions, fiscal_toggle, df_name, df_const, session_key):
    """
    Returns the defined variables necessary for having secondary input boxes.
    """
    # all tabs are enabled initially but the button for the tab the user is inside is disabled later
    quarter_disabled = month_disabled = week_disabled = False
    # all tabs are initially unselected
    quarter_class_name = month_class_name = week_class_name = 'date-picker-nav'

    # if inside quarter tab
    if conditions[0]:
        new_tab = 'Quarter'
        quarter_class_name = 'date-picker-nav-selected'
        quarter_disabled = True
        default_max = 4
        if fiscal_toggle == 'Gregorian':
            fringe_min = df_const[session_key]['GREGORIAN_QUARTER_FRINGE_MIN']
            fringe_max = df_const[session_key]['GREGORIAN_QUARTER_FRINGE_MAX']
            max_year = df_const[session_key]['GREGORIAN_QUARTER_MAX_YEAR']
        else:
            fringe_min = df_const[session_key]['FISCAL_QUARTER_FRINGE_MIN']
            fringe_max = df_const[session_key]['FISCAL_QUARTER_FRINGE_MAX']
            max_year = df_const[session_key]['FISCAL_QUARTER_MAX_YEAR']
        if fringe_max == 4:
            max_year += 1
            fringe_max = 1
        else:
            fringe_max += 1
    # if inside month tab
    elif conditions[1]:
        new_tab = 'Month'
        month_class_name = 'date-picker-nav-selected'
        month_disabled = True
        default_max = 12
        if fiscal_toggle == 'Gregorian':
            fringe_min = df_const[session_key]['GREGORIAN_MONTH_FRINGE_MIN']
            fringe_max = df_const[session_key]['GREGORIAN_MONTH_FRINGE_MAX']
            max_year = df_const[session_key]['GREGORIAN_MONTH_MAX_YEAR']
        else:
            fringe_min = df_const[session_key]['FISCAL_MONTH_FRINGE_MIN']
            fringe_max = df_const[session_key]['FISCAL_MONTH_FRINGE_MAX']
            max_year = df_const[session_key]['FISCAL_MONTH_MAX_YEAR']
        if fringe_max == 12:
            max_year += 1
            fringe_max = 1
        else:
            fringe_max += 1
    # if inside week tab
    else:
        new_tab = 'Week'
        week_class_name = 'date-picker-nav-selected'
        week_disabled = True
        default_max = 52
        if fiscal_toggle == 'Gregorian':
            fringe_min = df_const[session_key]['GREGORIAN_WEEK_FRINGE_MIN']
            fringe_max = df_const[session_key]['GREGORIAN_WEEK_FRINGE_MAX']
            max_year = df_const[session_key]['GREGORIAN_WEEK_MAX_YEAR']
        else:
            fringe_min = df_const[session_key]['FISCAL_WEEK_FRINGE_MIN']
            fringe_max = df_const[session_key]['FISCAL_WEEK_FRINGE_MAX']
            max_year = df_const[session_key]['FISCAL_WEEK_MAX_YEAR']
        if fringe_max == 52:
            max_year += 1
            fringe_max = 1
        else:
            fringe_max += 1

    return quarter_class_name, quarter_disabled, month_class_name, month_disabled, week_class_name, week_disabled, \
        fringe_min, fringe_max, default_max, max_year, new_tab


def update_date_columns(changed_id, selected_min_year, min_year, fringe_min, selected_max_year, max_year, fringe_max,
                        default_max, tab, selected_secondary_min, selected_secondary_max, tile):
    """Creates left and right columns for tabs with secondary time options (beneath years)."""
    # if max/min year changed, reset corresponding max/min (period) selection to max/min
    if 'start-year-input' in changed_id:
        if selected_min_year == min_year:
            selected_secondary_min = fringe_min
        else:
            selected_secondary_min = 1
    elif 'end-year-input' in changed_id:
        if selected_max_year == max_year:
            selected_secondary_max = fringe_max
        else:
            selected_secondary_max = default_max
    # Fiscal <---> Gregorian changed, reset to maximum boundaries
    elif 'fiscal-year-toggle' in changed_id:
        selected_min_year = min_year
        selected_max_year = max_year
        selected_secondary_min = fringe_min
        selected_secondary_max = fringe_max

    # if min and max years are the same
    if selected_min_year == selected_max_year:
        modifier_min = 0
        modifier_max = 1
        if (selected_min_year == min_year) & (selected_min_year == max_year):
            min_min = fringe_min
            min_max = selected_secondary_max
            max_min = selected_secondary_min
            max_max = fringe_max
        elif selected_min_year == min_year:
            min_min = fringe_min
            min_max = selected_secondary_max
            max_min = selected_secondary_min
            max_max = default_max
        elif selected_min_year == max_year:
            min_min = 1
            min_max = selected_secondary_max
            max_min = selected_secondary_min
            max_max = fringe_max
        else:
            min_min = 1
            min_max = selected_secondary_max
            max_min = selected_secondary_min
            max_max = default_max
    # else, min and max years are different
    else:
        modifier_min = 1
        modifier_max = 0
        if selected_min_year == min_year:
            min_min = fringe_min
            min_max = default_max
        else:
            min_min = 1
            min_max = default_max
        if selected_max_year == max_year:
            max_min = 1
            max_max = fringe_max
        else:
            max_min = 1
            max_max = default_max

    # if min (period) is (default_max), don't allow max year to be same year
    if selected_secondary_min == default_max:
        year_modifier_max = 1
    else:
        year_modifier_max = 0
    # if max (period) is 1, don't allow min year to be same year
    if selected_secondary_max == 1:
        year_modifier_min = 0
    else:
        year_modifier_min = 1

    # min year changed - change min year and reset min (period)
    if 'start-year-input' in changed_id:
        min_value = min_min
        min_max += modifier_min
        max_value = selected_secondary_max
        max_min += modifier_max
        max_max += 1
    # max year changed - change max year and reset max (period)
    elif 'end-year-input' in changed_id:
        min_value = selected_secondary_min
        min_max += modifier_min
        max_value = max_max
        max_min += modifier_max
        max_max += 1
    # (period) changed, apply change
    else:
        min_value = selected_secondary_min
        min_max += modifier_min
        max_value = selected_secondary_max
        max_min += modifier_max
        max_max += 1

    year_input_min = get_date_box(index={'type': 'start-year-input', 'index': tile},
                                  value=selected_min_year,
                                  minimum=min_year,
                                  maximum=selected_max_year + year_modifier_min - 1,
                                  name=tab)
    year_input_max = get_date_box(index={'type': 'end-year-input', 'index': tile},
                                  value=selected_max_year,
                                  minimum=selected_min_year + year_modifier_max,
                                  maximum=max_year)
    secondary_input_min = get_date_box(index={'type': 'start-secondary-input', 'index': tile},
                                       value=min_value,
                                       minimum=min_min,
                                       maximum=min_max - 1)
    secondary_input_max = get_date_box(index={'type': 'end-secondary-input', 'index': tile},
                                       value=max_value,
                                       minimum=max_min,
                                       maximum=max_max - 1)
    return [year_input_min, secondary_input_min], [year_input_max, secondary_input_max]
