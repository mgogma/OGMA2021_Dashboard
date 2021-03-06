######################################################################################################################
"""
saving_loading_callbacks.py

Stores all callbacks for managing saves/loading tiles/dashboards.
"""
######################################################################################################################

# External Packages
import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output, State, ALL, MATCH
from dash.exceptions import PreventUpdate
from re import search
from dash import no_update
import dash_html_components as html
from flask import session

# Internal Modules
from apps.dashboard.layouts import get_data_menu, get_customize_content, get_div_body
from apps.dashboard.app import app
from apps.dashboard.data import get_label, dataset_to_df, generate_constants
from apps.dashboard.saving_functions import delete_layout, save_layout_state, save_layout_to_db, \
    save_dashboard_state, save_dashboard_to_db, delete_dashboard, load_graph_menu

# **********************************************GLOBAL VARIABLES*****************************************************

REPORT_POINTER_PREFIX = 'Report_Ext_'
DASHBOARD_POINTER_PREFIX = 'Dashboard_Ext_'

# ************************************SHARED TILE LOADING/DASHBOARD SAVING*******************************************

# load the tile title
app.clientside_callback(
    """
    function _load_tile_title(tile_load_title, dashboard_load_title){
        const triggered = String(dash_clientside.callback_context.triggered.map(t => t.prop_id));

        if (triggered.includes('data-tile_load_title')){
            return tile_load_title;
        }
        else{
            return dashboard_load_title;
        }
    }
    """,
    Output({'type': 'tile-title', 'index': MATCH}, 'value'),
    [Input({'type': 'set-tile-title-trigger', 'index': MATCH}, 'data-tile_load_title'),
     Input({'type': 'set-tile-title-trigger', 'index': MATCH}, 'data-dashboard_load_title')],
    prevent_initial_call=True
)


# ***********************************************SHARED SAVING*******************************************************


# Update the dropdown options of available tile layouts.
@app.callback(
    Output({'type': 'select-layout-dropdown', 'index': ALL}, 'options'),
    [Input({'type': 'set-dropdown-options-trigger', 'index': ALL}, 'data-tile_saving'),
     Input({'type': 'set-dropdown-options-trigger', 'index': 0}, 'data-dashboard_saving')],
    [State({'type': 'tile-link', 'index': ALL}, 'className')],
    prevent_initial_call=True
)
def _update_tile_loading_dropdown_options(_tile_saving_trigger, _dashboard_saving_trigger, links):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if changed_id == '.':
        raise PreventUpdate

    # graph titles was previously session['saved_layouts']
    return [[{'label': session['saved_layouts'][key]['Title'], 'value': key} for key in
             session['saved_layouts']]] * len(links)


# *************************************************TILE SAVING********************************************************


# Manage tile saves trigger. Formatted in two chained callbacks to mix ALL and y values.
# handles results from float menu prompts
@app.callback(
    Output('tile-save-trigger-wrapper', 'children'),
    [Input({'type': 'save-button', 'index': ALL}, 'n_clicks'),
     Input({'type': 'delete-button', 'index': ALL}, 'n_clicks'),
     Input({'type': 'tile-link', 'index': ALL}, 'n_clicks'),
     Input({'type': 'set-tile-link-trigger', 'index': ALL}, 'link-'),
     Input({'type': 'float-menu-result', 'index': 0}, 'children'),
     Input({'type': 'prompt-result', 'index': 0}, 'children')],
    [State('prompt-title', 'data-'),
     State('float-menu-title', 'data-'),
     State({'type': 'select-layout-dropdown', 'index': ALL}, 'value'),
     State({'type': 'tile-link', 'index': ALL}, 'className')],
    prevent_initial_call=True
)
def _manage_tile_save_and_load_trigger(save_clicks, delete_clicks, _link_clicks, link_trigger, float_menu_result,
                                       prompt_result, prompt_data, float_menu_data, load_state, link_state):
    # -------------------------------------------Variable Declaration---------------------------------------------------
    changed_ids = [p['prop_id'] for p in dash.callback_context.triggered]
    children = []
    # ------------------------------------------------------------------------------------------------------------------

    if changed_ids == '.':
        raise PreventUpdate

    for changed_id in changed_ids:
        if 'prompt-result' in changed_id:
            changed_index = prompt_data[1]
        elif 'float-menu-result' in changed_id:
            changed_index = int(float_menu_data[1])
        else:
            changed_index = int(search(r'\d+', changed_id).group())

        # Blank buttons not clicked, prevent updates
        if '"type":"save-button"}.n_clicks' in changed_id and save_clicks[changed_index] == 0:
            raise PreventUpdate
        if '"type":"delete-button"}.n_clicks' in changed_id and delete_clicks[changed_index] == 0:
            raise PreventUpdate

        if not isinstance(load_state, list):
            load_state = [load_state]
        if 'float-menu-result' in changed_id \
                and (float_menu_data[0] != 'layouts' or load_state[changed_index] is None or float_menu_result != 'ok'):
            raise PreventUpdate
        # do not call if we aren't dealing with tiles
        if changed_index == 4:
            raise PreventUpdate

        # switch statement
        if 'save-button' in changed_id:
            mode = "save"
        elif 'delete-button' in changed_id:
            mode = "delete"
        elif '"type":"select-layout-dropdown"}.value' in changed_id:
            mode = 'fa fa-unlink'
        elif '"type":"tile-link"}.n_clicks' in changed_id:
            # if link button was pressed, toggle the link icon linked <--> unlinked
            if link_state[changed_index] == "fa fa-link":
                mode = 'fa fa-unlink'
            else:
                mode = 'fa fa-link'
        elif '"type":"set-tile-link-trigger"}.link-' in changed_id and link_trigger is not None:
            mode = 'fa fa-unlink'
        elif 'float-menu-result' in changed_id:
            mode = "confirm-load"
        elif prompt_data[0] == 'delete' and prompt_result == 'ok':
            mode = "confirm-delete"
        elif prompt_data[0] == 'overwrite' and prompt_result == 'ok':
            mode = "confirm-overwrite"
        elif prompt_data[0] == 'link' and prompt_result == 'ok':
            mode = "confirm-link"
        else:
            continue

        # even though we can use a direct output method for linking the two callbacks, this is more efficient on page
        # load due to how the dash renderer loads callbacks
        children.append(dcc.Store(id={'type': 'tile-save-trigger', 'index': changed_index}, data=mode))
    return children


# Tile saving/save deleting/tile loading - serves prompt.
for y in range(4):
    @app.callback(
        # LAYOUT components
        [Output({'type': 'prompt-trigger-wrapper', 'index': y}, 'children'),
         Output({'type': 'set-dropdown-options-trigger', 'index': y}, 'data-tile_saving'),
         Output({'type': 'minor-popup', 'index': y}, 'children'),
         Output({'type': 'minor-popup', 'index': y}, 'is_open'),
         # load tile layout outputs
         Output({'type': 'set-tile-title-trigger', 'index': y}, 'data-tile_load_title'),
         Output({'type': 'tile-customize-content', 'index': y}, 'children'),
         Output({'type': 'data-menu-tile-loading', 'index': y}, 'children'),
         Output({'type': 'select-range-trigger', 'index': y}, 'data-tile-tab'),
         Output({'type': 'select-range-trigger', 'index': y}, 'data-tile-start_year'),
         Output({'type': 'select-range-trigger', 'index': y}, 'data-tile-end_year'),
         Output({'type': 'select-range-trigger', 'index': y}, 'data-tile-start_secondary'),
         Output({'type': 'select-range-trigger', 'index': y}, 'data-tile-end_secondary'),
         Output({'type': 'tile-link-wrapper', 'index': y}, 'children'),
         Output({'type': 'df-constants-storage-tile-wrapper', 'index': y}, 'children'),
         # tile link appearance
         Output({'type': 'tile-link', 'index': y}, 'className')],
        [Input({'type': 'tile-save-trigger', 'index': y}, 'data')],
        # Tile features
        [State({'type': 'tile-title', 'index': y}, 'value'),
         State({'type': 'tile-link', 'index': y}, 'className'),
         State({'type': 'graph-type-dropdown', 'index': y}, 'value'),
         State({'type': 'args-value: {}'.replace("{}", str(y)), 'index': ALL}, 'value'),
         State({'type': 'graph_display', 'index': y}, 'children'),
         State({'type': 'x-modified', 'index': y}, 'data'),
         State({'type': 'y-modified', 'index': y}, 'data'),
         State({'type': 'gridline', 'index': y}, 'value'),
         State({'type': 'legend', 'index': y}, 'value'),
         # Data set states
         State({'type': 'data-set', 'index': y}, 'value'),
         State({'type': 'data-set', 'index': 4}, 'value'),
         # parent data menu states
         State({'type': 'start-year-input', 'index': 4}, 'value'),
         State({'type': 'end-year-input', 'index': 4}, 'value'),
         State({'type': 'hierarchy_type_dropdown', 'index': 4}, 'value'),
         State({'type': 'hierarchy-toggle', 'index': 4}, 'value'),
         State({'type': 'hierarchy_level_dropdown', 'index': 4}, 'value'),
         State({'type': 'hierarchy_display_button', 'index': 4}, 'children'),
         State({'type': 'graph_children_toggle', 'index': 4}, 'value'),
         State({'type': 'fiscal-year-toggle', 'index': 4}, 'value'),
         State({'type': 'radio-timeframe', 'index': 4}, 'value'),
         State({'type': 'start-secondary-input', 'index': 4}, 'value'),
         State({'type': 'end-secondary-input', 'index': 4}, 'value'),
         State({'type': 'num-periods', 'index': 4}, 'value'),
         State({'type': 'period-type', 'index': 4}, 'value'),
         State({'type': 'start-year-input', 'index': 4}, 'name'),
         State({'type': 'time-period', 'index': 4}, 'value'),
         # tile data menu states
         State({'type': 'start-year-input', 'index': y}, 'value'),
         State({'type': 'end-year-input', 'index': y}, 'value'),
         State({'type': 'hierarchy_type_dropdown', 'index': y}, 'value'),
         State({'type': 'hierarchy-toggle', 'index': y}, 'value'),
         State({'type': 'hierarchy_level_dropdown', 'index': y}, 'value'),
         State({'type': 'hierarchy_display_button', 'index': y}, 'children'),
         State({'type': 'graph_children_toggle', 'index': y}, 'value'),
         State({'type': 'fiscal-year-toggle', 'index': y}, 'value'),
         State({'type': 'radio-timeframe', 'index': y}, 'value'),
         State({'type': 'start-secondary-input', 'index': y}, 'value'),
         State({'type': 'end-secondary-input', 'index': y}, 'value'),
         State({'type': 'num-periods', 'index': y}, 'value'),
         State({'type': 'period-type', 'index': y}, 'value'),
         State({'type': 'start-year-input', 'index': y}, 'name'),
         State({'type': 'time-period', 'index': y}, 'value'),
         # Seconday hierarchy
         State({'type': 'secondary_hierarchy_display_button', 'index': y}, 'children'),
         State({'type': 'secondary_hierarchy-toggle', 'index': y}, 'value'),
         State({'type': 'secondary_hierarchy_level_dropdown', 'index': y}, 'value'),
         State({'type': 'secondary_hierarchy_children_toggle', 'index': y}, 'value'),
         State({'type': 'secondary_hierarchy_specific_dropdown', 'index': y}, 'options'),
         # load layout states
         State({'type': 'select-layout-dropdown', 'index': y}, 'value'),
         State('df-constants-storage', 'data')],
        prevent_initial_call=True
    )
    def _manage_tile_saves(trigger, graph_title, link_state, graph_type, args_list, graph_display, xmodified, ymodified,
                           gridline, legend, df_name, parent_df_name, parent_year_start, parent_year_end,
                           parent_hierarchy_type, parent_hierarchy_toggle, parent_hierarchy_level_dropdown,
                           parent_state_of_display, parent_graph_children_toggle, parent_fiscal_toggle,
                           parent_input_method, parent_secondary_start, parent_secondary_end, parent_x_time_period,
                           parent_period_type, parent_tab, parent_time_period, year_start, year_end, hierarchy_type,
                           hierarchy_toggle, hierarchy_level_dropdown, state_of_display, graph_children_toggle,
                           fiscal_toggle, input_method, secondary_start, secondary_end, x_time_period, period_type, tab,
                           time_period, secondary_button_path, secondary_toggle, secondary_level, secondary_graph_all,
                           secondary_options, selected_layout, df_const):

        if link_state == 'fa fa-link':
            fiscal_toggle = parent_fiscal_toggle
            year_start = parent_year_start
            year_end = parent_year_end
            secondary_start = parent_secondary_start
            secondary_end = parent_secondary_end
            x_time_period = parent_x_time_period
            period_type = parent_period_type
            input_method = parent_input_method
            hierarchy_type = parent_hierarchy_type
            hierarchy_toggle = parent_hierarchy_toggle
            hierarchy_level_dropdown = parent_hierarchy_level_dropdown
            state_of_display = parent_state_of_display
            tab = parent_tab
            df_name = parent_df_name
            graph_children_toggle = parent_graph_children_toggle
            time_period = parent_time_period

        # creates a hierarchy trail from the display of hierarchy selection
        if type(state_of_display) == dict:
            state_of_display = [state_of_display]

        nid_path = "root"
        for button in state_of_display:
            nid_path += '^||^{}'.format(button['props']['children'])  # formatting to be able to split it up later

        # creates a hierarchy trail from the display of secondary hierarchy selection
        if type(secondary_button_path) == dict:
            secondary_button_path = [secondary_button_path]

        secondary_nid_path = "root"
        for button in secondary_button_path:
            secondary_nid_path += '^||^{}'.format(button['props']['children'])

        tile = int(dash.callback_context.inputs_list[0]['id']['index'])
        # Outputs
        update_options_trigger = no_update
        prompt_trigger = no_update
        popup_text = no_update
        popup_is_open = no_update
        tile_title_trigger = no_update
        customize_content = no_update
        data_content = no_update
        tab_output = no_update
        start_year = no_update
        end_year = no_update
        start_secondary = no_update
        end_secondary = no_update
        unlink = no_update
        link_output = no_update
        df_const_output = no_update
        graph_options = [None, None, None, None, xmodified, ymodified, gridline, legend]
        graph_variable = [secondary_level, secondary_nid_path, secondary_toggle, secondary_graph_all, secondary_options]

        # if save requested or the over-write was confirmed, check for exceptions and save
        if trigger == 'save' or trigger == 'confirm-overwrite':
            intermediate_pointer = REPORT_POINTER_PREFIX + graph_title.replace(" ", "")
            graph_titles = []

            for layout in session['saved_layouts']:
                graph_titles.append(session['saved_layouts'][layout]['Title'])

            # if user is trying to save an empty graph, warn them that they must have a graph to save
            if not graph_display:
                prompt_trigger = dcc.Store(id={'type': 'prompt-trigger', 'index': tile},
                                           data=[['empty_graph', tile], {}, get_label('LBL_Empty_Graph'),
                                                 get_label('LBL_Empty_Graph_Prompt'), False])
            # if tile is untitled, prevent updates but return save message
            elif graph_title == '':
                prompt_trigger = dcc.Store(id={'type': 'prompt-trigger', 'index': tile},
                                           data=[['empty_title', tile], {}, get_label('LBL_Untitled_Graph'),
                                                 get_label('LBL_Untitled_Graph_Prompt'), False])
            # if conflicting tiles and overwrite not requested, prompt overwrite
            elif intermediate_pointer in session['saved_layouts'] \
                    and session['saved_layouts'][intermediate_pointer]['Title'] == graph_title \
                    and 'confirm-overwrite' != trigger:
                prompt_trigger = dcc.Store(id={'type': 'prompt-trigger', 'index': tile},
                                           data=[['overwrite', tile], {}, get_label('LBL_Overwrite_Graph'),
                                                 get_label('LBL_Overwrite_Graph_Prompt'), False])
            # else, title is valid to be saved
            else:
                while True:
                    if intermediate_pointer in session['saved_layouts'] and trigger != "confirm-overwrite":
                        layout_pointer = intermediate_pointer + "_"
                        intermediate_pointer = layout_pointer
                    else:
                        layout_pointer = intermediate_pointer
                        break
                if 'figure' in graph_display['props']:
                    if 'xaxis' in graph_display['props']['figure']['layout']:
                        if 'title' in graph_display['props']['figure']['layout']['xaxis']:
                            graph_options[0] = graph_display['props']['figure']['layout']['xaxis']['title']['text']
                    if 'yaxis' in graph_display['props']['figure']['layout']:
                        if 'text' in graph_display['props']['figure']['layout']['yaxis']['title']:
                            graph_options[1] = graph_display['props']['figure']['layout']['yaxis']['title']['text']
                    if 'legend' in graph_display['props']['figure']['layout']:
                        if 'x' in graph_display['props']['figure']['layout']['legend']:
                            graph_options[2] = graph_display['props']['figure']['layout']['legend']['x']
                        if 'y' in graph_display['props']['figure']['layout']['legend']:
                            graph_options[3] = graph_display['props']['figure']['layout']['legend']['y']

                if graph_type == 'Bar':
                    if args_list[2] == 'Horizontal':
                        temp_variable = graph_options[1]
                        graph_options[1] = graph_options[0]
                        graph_options[0] = temp_variable

                elif graph_type == 'Box_Plot':
                    if args_list[1] == 'Vertical':
                        temp_variable = graph_options[1]
                        graph_options[1] = graph_options[0]
                        graph_options[0] = temp_variable

                elements_to_save = {'Graph Type': graph_type,
                                    'Args List': args_list,
                                    'Graph Options': graph_options,
                                    'Fiscal Toggle': fiscal_toggle,
                                    'Timeframe': input_method,
                                    'Num Periods': x_time_period,
                                    'Period Type': period_type,
                                    'Hierarchy Type': hierarchy_type,
                                    'Hierarchy Toggle': hierarchy_toggle,
                                    'Level Value': hierarchy_level_dropdown,
                                    'Data Set': df_name,
                                    'Time Period': time_period,
                                    'Graph All Toggle': graph_children_toggle,
                                    'NID Path': nid_path,
                                    'Title': graph_title,
                                    'Graph Variable': graph_variable}
                # if input method is 'select-range', add the states of the select range inputs
                if input_method == 'select-range':
                    elements_to_save['Date Tab'] = tab
                    elements_to_save['Start Year'] = year_start
                    elements_to_save['End Year'] = year_end
                    elements_to_save['Start Secondary'] = secondary_start
                    elements_to_save['End Secondary'] = secondary_end

                # calls the save_graph_state function to save the graph to the sessions dictionary
                save_layout_state(layout_pointer, elements_to_save)
                # saves the graph title and layout to the file where you are storing all the saved layouts
                # save_layout_to_file(session['saved_layouts'])
                # saves the graph layout to the database
                save_layout_to_db(layout_pointer, graph_title, 'save' == trigger)
                popup_text = get_label('LBL_Your_Graph_Has_Been_Saved').format(graph_title)
                popup_is_open = True
                update_options_trigger = 'trigger'
        # if delete button was pressed, prompt delete
        elif trigger == 'delete':
            intermediate_pointer = REPORT_POINTER_PREFIX + graph_title.replace(" ", "")
            graph_titles = []
            for layout in session['saved_layouts']:
                graph_titles.append(session['saved_layouts'][layout]['Title'])

            # if tile exists in session, send delete prompt
            if intermediate_pointer in session['saved_layouts'] \
                    and session['saved_layouts'][intermediate_pointer]['Title'] == graph_title:
                prompt_trigger = dcc.Store(id={'type': 'prompt-trigger', 'index': tile},
                                           data=[['delete', tile], {}, get_label('LBL_Delete_Graph'),
                                                 get_label('LBL_Delete_Graph_Prompt').format(graph_title), False])
        # If prompt result confirm delete button has been pressed
        elif trigger == 'confirm-delete':
            intermediate_pointer = REPORT_POINTER_PREFIX + graph_title.replace(" ", "")
            delete_layout(intermediate_pointer)
            update_options_trigger = 'trigger'
            popup_text = get_label('LBL_Your_Graph_Has_Been_Deleted').format(graph_title)
            popup_is_open = True
        # if confirm-load then we load what was selected from menu
        elif trigger == 'confirm-load':
            df_name = session['saved_layouts'][selected_layout]['Data Set']
            time_period = session['saved_layouts'][selected_layout]['Time Period']
            if df_name != 'OPG010':
                session_key = df_name + time_period
            else:
                session_key = df_name
            # check if data is loaded
            if session_key not in session or (df_const is not None and session_key not in df_const):
                session[session_key] = dataset_to_df(df_name, time_period)
                if df_const is None:
                    df_const = {}
                df_const[session_key] = generate_constants(df_name, session_key)

            #  --------- create customize menu ---------
            graph_type = session['saved_layouts'][selected_layout]['Graph Type']
            time_period = session['saved_layouts'][selected_layout]['Time Period']
            args_list = session['saved_layouts'][selected_layout]['Args List']
            graph_options = session['saved_layouts'][selected_layout]['Graph Options']
            graph_variable = session['saved_layouts'][selected_layout]['Graph Variable']
            graph_menu = load_graph_menu(graph_type=graph_type, tile=tile, df_name=df_name, args_list=args_list,
                                         graph_options=graph_options, graph_variable=graph_variable, df_const=df_const,
                                         session_key=session_key)
            customize_content = get_customize_content(tile=tile, graph_type=graph_type, graph_menu=graph_menu,
                                                      df_name=df_name)

            #  --------- create data side menu ---------
            # set hierarchy type
            hierarchy_type = session['saved_layouts'][selected_layout]['Hierarchy Type']
            # set hierarchy toggle value (level vs specific)
            hierarchy_toggle = session['saved_layouts'][selected_layout]['Hierarchy Toggle']
            # set level value selection
            level_value = session['saved_layouts'][selected_layout]['Level Value']
            # retrieve nid string
            nid_path = session['saved_layouts'][selected_layout]['NID Path']
            # set the value of "Graph All" checkbox
            graph_all_toggle = session['saved_layouts'][selected_layout]['Graph All Toggle']
            # set gregorian/fiscal toggle value
            fiscal_toggle = session['saved_layouts'][selected_layout]['Fiscal Toggle']
            # set timeframe radio buttons selection
            input_method = session['saved_layouts'][selected_layout]['Timeframe']
            # set num periods
            num_periods = session['saved_layouts'][selected_layout]['Num Periods']
            # set period type
            period_type = session['saved_layouts'][selected_layout]['Period Type']

            data_content = get_data_menu(tile=tile, df_name=df_name, mode='tile-loading',
                                         hierarchy_toggle=hierarchy_toggle, level_value=level_value,
                                         nid_path=nid_path, graph_all_toggle=graph_all_toggle,
                                         fiscal_toggle=fiscal_toggle, input_method=input_method,
                                         num_periods=num_periods, time_period=time_period,
                                         period_type=period_type, df_const=df_const, session_key=session_key,
                                         hier_type=hierarchy_type)

            # show and set 'Select Range' inputs if selected, else leave hidden and unset
            if session['saved_layouts'][selected_layout]['Timeframe'] == 'select-range':
                tab_output = session['saved_layouts'][selected_layout]['Date Tab']
                start_year = session['saved_layouts'][selected_layout]['Start Year']
                end_year = session['saved_layouts'][selected_layout]['End Year']
                start_secondary = session['saved_layouts'][selected_layout]['Start Secondary']
                end_secondary = session['saved_layouts'][selected_layout]['End Secondary']
            else:
                tab_output = start_year = end_year = start_secondary = end_secondary = no_update

            df_const_output = dcc.Store(
                id='df-constants-storage',
                storage_type='memory',
                data=df_const)
            for x in range(tile):
                df_const_output = html.Div(
                    df_const_output,
                    id={'type': 'df-constants-storage-tile-wrapper', 'index': x}
                )

            session['tile_edited'][tile] = 'Load'
            unlink = html.I(
                className='fa fa-unlink',
                id={'type': 'tile-link', 'index': tile},
                style={'position': 'relative'})
            tile_title_trigger = session['saved_layouts'][selected_layout]['Title']
        # if we have linking inputs
        elif trigger == 'fa fa-unlink':
            link_output = 'fa fa-unlink'
        elif trigger == 'fa fa-link':
            if df_name != parent_df_name:
                prompt_trigger = dcc.Store(id={'type': 'prompt-trigger', 'index': tile},
                                           data=[['link', tile], {}, get_label('LBL_Link_Graph'),
                                                 get_label('LBL_Link_Graph_Prompt'), False])
            else:
                link_output = 'fa fa-link'
        elif trigger == 'confirm-link':
            link_output = 'fa fa-link'

        return prompt_trigger, update_options_trigger, popup_text, popup_is_open, tile_title_trigger, \
            customize_content, data_content, tab_output, start_year, end_year, start_secondary, \
            end_secondary, unlink, df_const_output, link_output


# **********************************************DASHBOARD MENU*******************************************************


# Dashboard saving/save deleting/loading - triggers prompt and menu.
@app.callback(
    [Output('select-dashboard-dropdown', 'options'),
     Output({'type': 'set-dropdown-options-trigger', 'index': 0}, 'data-dashboard_saving'),
     Output({'type': 'set-tile-title-trigger', 'index': 0}, 'data-dashboard_load_title'),
     Output({'type': 'set-tile-title-trigger', 'index': 1}, 'data-dashboard_load_title'),
     Output({'type': 'set-tile-title-trigger', 'index': 2}, 'data-dashboard_load_title'),
     Output({'type': 'set-tile-title-trigger', 'index': 3}, 'data-dashboard_load_title'),
     # menu and prompt outputs
     Output({'type': 'prompt-trigger-wrapper', 'index': 4}, 'children'),
     Output({'type': 'float-menu-trigger-wrapper', 'index': 4}, 'children'),
     Output({'type': 'minor-popup', 'index': 4}, 'children'),
     Output({'type': 'minor-popup', 'index': 4}, 'is_open'),
     # outputs for dashboard loading
     Output('dashboard-title', 'value'),
     # tile content
     Output('div-body-wrapper', 'children'),
     # data tile 0
     Output({'type': 'data-menu-dashboard-loading', 'index': 0}, 'children'),
     Output({'type': 'select-range-trigger', 'index': 0}, 'data-dashboard-tab'),
     Output({'type': 'select-range-trigger', 'index': 0}, 'data-dashboard-start_year'),
     Output({'type': 'select-range-trigger', 'index': 0}, 'data-dashboard-end_year'),
     Output({'type': 'select-range-trigger', 'index': 0}, 'data-dashboard-start_secondary'),
     Output({'type': 'select-range-trigger', 'index': 0}, 'data-dashboard-end_secondary'),
     # data tile 1
     Output({'type': 'data-menu-dashboard-loading', 'index': 1}, 'children'),
     Output({'type': 'select-range-trigger', 'index': 1}, 'data-dashboard-tab'),
     Output({'type': 'select-range-trigger', 'index': 1}, 'data-dashboard-start_year'),
     Output({'type': 'select-range-trigger', 'index': 1}, 'data-dashboard-end_year'),
     Output({'type': 'select-range-trigger', 'index': 1}, 'data-dashboard-start_secondary'),
     Output({'type': 'select-range-trigger', 'index': 1}, 'data-dashboard-end_secondary'),
     # data tile 2
     Output({'type': 'data-menu-dashboard-loading', 'index': 2}, 'children'),
     Output({'type': 'select-range-trigger', 'index': 2}, 'data-dashboard-tab'),
     Output({'type': 'select-range-trigger', 'index': 2}, 'data-dashboard-start_year'),
     Output({'type': 'select-range-trigger', 'index': 2}, 'data-dashboard-end_year'),
     Output({'type': 'select-range-trigger', 'index': 2}, 'data-dashboard-start_secondary'),
     Output({'type': 'select-range-trigger', 'index': 2}, 'data-dashboard-end_secondary'),
     # data tile 3
     Output({'type': 'data-menu-dashboard-loading', 'index': 3}, 'children'),
     Output({'type': 'select-range-trigger', 'index': 3}, 'data-dashboard-tab'),
     Output({'type': 'select-range-trigger', 'index': 3}, 'data-dashboard-start_year'),
     Output({'type': 'select-range-trigger', 'index': 3}, 'data-dashboard-end_year'),
     Output({'type': 'select-range-trigger', 'index': 3}, 'data-dashboard-start_secondary'),
     Output({'type': 'select-range-trigger', 'index': 3}, 'data-dashboard-end_secondary'),
     # data tile 4
     Output({'type': 'data-menu-dashboard-loading', 'index': 4}, 'children'),
     Output({'type': 'select-range-trigger', 'index': 4}, 'data-dashboard-tab'),
     Output({'type': 'select-range-trigger', 'index': 4}, 'data-dashboard-start_year'),
     Output({'type': 'select-range-trigger', 'index': 4}, 'data-dashboard-end_year'),
     Output({'type': 'select-range-trigger', 'index': 4}, 'data-dashboard-start_secondary'),
     Output({'type': 'select-range-trigger', 'index': 4}, 'data-dashboard-end_secondary'),
     # close tile
     Output('tile-closed-input-trigger', 'data'),
     # num tiles update
     Output('num-tiles-4', 'data-num-tiles'),
     Output('df-constants-storage-dashboard-wrapper', 'children'),
     Output('dashboard-reset-confirmation', 'data-')],
    [Input('save-dashboard', 'n_clicks'),
     Input('delete-dashboard', 'n_clicks'),
     Input('load-dashboard', 'n_clicks'),
     Input({'type': 'float-menu-result', 'index': 1}, 'children'),
     Input({'type': 'prompt-result', 'index': 1}, 'children'),
     Input('dashboard-reset', 'n_clicks'),
     Input({'type': 'tile-close', 'index': ALL}, 'n_clicks')],
    # prompt and menu info
    [State('prompt-title', 'data-'),
     State('float-menu-title', 'data-'),
     State('select-dashboard-dropdown', 'value'),
     # dashboard info
     State('dashboard-title', 'value'),
     # tile info
     State({'type': 'tile-title', 'index': ALL}, 'value'),
     State({'type': 'tile-link', 'index': ALL}, 'className'),
     State({'type': 'graph-type-dropdown', 'index': ALL}, 'value'),
     State({'type': 'args-value: {}'.replace("{}", str(0)), 'index': ALL}, 'value'),
     State({'type': 'args-value: {}'.replace("{}", str(1)), 'index': ALL}, 'value'),
     State({'type': 'args-value: {}'.replace("{}", str(2)), 'index': ALL}, 'value'),
     State({'type': 'args-value: {}'.replace("{}", str(3)), 'index': ALL}, 'value'),
     State({'type': 'xaxis-title', 'index': ALL}, 'value'),
     State({'type': 'yaxis-title', 'index': ALL}, 'value'),
     State({'type': 'x-pos-legend', 'index': ALL}, 'value'),
     State({'type': 'y-pos-legend', 'index': ALL}, 'value'),
     State({'type': 'x-modified', 'index': ALL}, 'data'),
     State({'type': 'y-modified', 'index': ALL}, 'data'),
     State({'type': 'gridline', 'index': ALL}, 'value'),
     State({'type': 'legend', 'index': ALL}, 'value'),
     # data sets
     State({'type': 'data-set', 'index': 0}, 'value'),
     State({'type': 'data-set', 'index': 1}, 'value'),
     State({'type': 'data-set', 'index': 2}, 'value'),
     State({'type': 'data-set', 'index': 3}, 'value'),
     State({'type': 'data-set', 'index': 4}, 'value'),
     # time periods
     State({'type': 'time-period', 'index': 0}, 'value'),
     State({'type': 'time-period', 'index': 1}, 'value'),
     State({'type': 'time-period', 'index': 2}, 'value'),
     State({'type': 'time-period', 'index': 3}, 'value'),
     State({'type': 'time-period', 'index': 4}, 'value'),
     # start years
     State({'type': 'start-year-input', 'index': 0}, 'value'),
     State({'type': 'start-year-input', 'index': 1}, 'value'),
     State({'type': 'start-year-input', 'index': 2}, 'value'),
     State({'type': 'start-year-input', 'index': 3}, 'value'),
     State({'type': 'start-year-input', 'index': 4}, 'value'),
     # end years
     State({'type': 'end-year-input', 'index': 0}, 'value'),
     State({'type': 'end-year-input', 'index': 1}, 'value'),
     State({'type': 'end-year-input', 'index': 2}, 'value'),
     State({'type': 'end-year-input', 'index': 3}, 'value'),
     State({'type': 'end-year-input', 'index': 4}, 'value'),
     # hieratchy types
     State({'type': 'hierarchy_type_dropdown', 'index': 0}, 'value'),
     State({'type': 'hierarchy_type_dropdown', 'index': 1}, 'value'),
     State({'type': 'hierarchy_type_dropdown', 'index': 2}, 'value'),
     State({'type': 'hierarchy_type_dropdown', 'index': 3}, 'value'),
     State({'type': 'hierarchy_type_dropdown', 'index': 4}, 'value'),
     # hierarchy toggles
     State({'type': 'hierarchy-toggle', 'index': 0}, 'value'),
     State({'type': 'hierarchy-toggle', 'index': 1}, 'value'),
     State({'type': 'hierarchy-toggle', 'index': 2}, 'value'),
     State({'type': 'hierarchy-toggle', 'index': 3}, 'value'),
     State({'type': 'hierarchy-toggle', 'index': 4}, 'value'),
     # graph children toggles
     State({'type': 'graph_children_toggle', 'index': 0}, 'value'),
     State({'type': 'graph_children_toggle', 'index': 1}, 'value'),
     State({'type': 'graph_children_toggle', 'index': 2}, 'value'),
     State({'type': 'graph_children_toggle', 'index': 3}, 'value'),
     State({'type': 'graph_children_toggle', 'index': 4}, 'value'),
     # hierarchy level dropdown values
     State({'type': 'hierarchy_level_dropdown', 'index': 0}, 'value'),
     State({'type': 'hierarchy_level_dropdown', 'index': 1}, 'value'),
     State({'type': 'hierarchy_level_dropdown', 'index': 2}, 'value'),
     State({'type': 'hierarchy_level_dropdown', 'index': 3}, 'value'),
     State({'type': 'hierarchy_level_dropdown', 'index': 4}, 'value'),
     # hierarchy display paths children
     State({'type': 'hierarchy_display_button', 'index': 0}, 'children'),
     State({'type': 'hierarchy_display_button', 'index': 1}, 'children'),
     State({'type': 'hierarchy_display_button', 'index': 2}, 'children'),
     State({'type': 'hierarchy_display_button', 'index': 3}, 'children'),
     State({'type': 'hierarchy_display_button', 'index': 4}, 'children'),
     # fiscal year toggle
     State({'type': 'fiscal-year-toggle', 'index': 0}, 'value'),
     State({'type': 'fiscal-year-toggle', 'index': 1}, 'value'),
     State({'type': 'fiscal-year-toggle', 'index': 2}, 'value'),
     State({'type': 'fiscal-year-toggle', 'index': 3}, 'value'),
     State({'type': 'fiscal-year-toggle', 'index': 4}, 'value'),
     # radio timeframes
     State({'type': 'radio-timeframe', 'index': 0}, 'value'),
     State({'type': 'radio-timeframe', 'index': 1}, 'value'),
     State({'type': 'radio-timeframe', 'index': 2}, 'value'),
     State({'type': 'radio-timeframe', 'index': 3}, 'value'),
     State({'type': 'radio-timeframe', 'index': 4}, 'value'),
     # start secondary values
     State({'type': 'start-secondary-input', 'index': 0}, 'value'),
     State({'type': 'start-secondary-input', 'index': 1}, 'value'),
     State({'type': 'start-secondary-input', 'index': 2}, 'value'),
     State({'type': 'start-secondary-input', 'index': 3}, 'value'),
     State({'type': 'start-secondary-input', 'index': 4}, 'value'),
     # end secondary values
     State({'type': 'end-secondary-input', 'index': 0}, 'value'),
     State({'type': 'end-secondary-input', 'index': 1}, 'value'),
     State({'type': 'end-secondary-input', 'index': 2}, 'value'),
     State({'type': 'end-secondary-input', 'index': 3}, 'value'),
     State({'type': 'end-secondary-input', 'index': 4}, 'value'),
     # num periods values
     State({'type': 'num-periods', 'index': 0}, 'value'),
     State({'type': 'num-periods', 'index': 1}, 'value'),
     State({'type': 'num-periods', 'index': 2}, 'value'),
     State({'type': 'num-periods', 'index': 3}, 'value'),
     State({'type': 'num-periods', 'index': 4}, 'value'),
     # period types
     State({'type': 'period-type', 'index': 0}, 'value'),
     State({'type': 'period-type', 'index': 1}, 'value'),
     State({'type': 'period-type', 'index': 2}, 'value'),
     State({'type': 'period-type', 'index': 3}, 'value'),
     State({'type': 'period-type', 'index': 4}, 'value'),
     # select-range tabs
     State({'type': 'start-year-input', 'index': 0}, 'name'),
     State({'type': 'start-year-input', 'index': 1}, 'name'),
     State({'type': 'start-year-input', 'index': 2}, 'name'),
     State({'type': 'start-year-input', 'index': 3}, 'name'),
     State({'type': 'start-year-input', 'index': 4}, 'name'),
     # document display path
     State({'type': 'secondary_hierarchy_display_button', 'index': ALL}, 'children'),
     # document toggle
     State({'type': 'secondary_hierarchy-toggle', 'index': ALL}, 'value'),
     # document level val
     State({'type': 'secondary_hierarchy_level_dropdown', 'index': ALL}, 'value'),
     # document graph all
     State({'type': 'secondary_hierarchy_children_toggle', 'index': ALL}, 'value'),
     # document options
     State({'type': 'secondary_hierarchy_specific_dropdown', 'index': ALL}, 'options'),
     # dashboard layout
     State('div-body', 'layouts'),
     # df_const
     State('df-constants-storage', 'data')],
    prevent_initial_call=True
)
def _manage_dashboard_saves_and_reset(_save_clicks, _delete_clicks, _load_clicks, float_menu_result, prompt_result,
                                      _reset_clicks, _close_clicks, prompt_data, float_menu_data, selected_dashboard,
                                      dashboard_title, tile_titles, links, graph_types,
                                      args_list_0, args_list_1, args_list_2, args_list_3,
                                      xaxis_titles, yaxis_titles, x_leg_pos, y_leg_pos, xmodified, ymodified, gridline,
                                      legend, df_name_0, df_name_1, df_name_2, df_name_3, df_name_4, time_period_0,
                                      time_period_1, time_period_2, time_period_3, time_period_4,
                                      start_year_0, start_year_1, start_year_2, start_year_3, start_year_4,
                                      end_year_0, end_year_1, end_year_2, end_year_3, end_year_4,
                                      hierarchy_type_0, hierarchy_type_1, hierarchy_type_2, hierarchy_type_3,
                                      hierarchy_type_4,
                                      hierarchy_toggle_0, hierarchy_toggle_1, hierarchy_toggle_2, hierarchy_toggle_3,
                                      hierarchy_toggle_4,
                                      graph_all_toggle_0, graph_all_toggle_1, graph_all_toggle_2, graph_all_toggle_3,
                                      graph_all_toggle_4,
                                      level_value_0, level_value_1, level_value_2, level_value_3, level_value_4,
                                      button_path_0, button_path_1, button_path_2, button_path_3, button_path_4,
                                      fiscal_toggle_0, fiscal_toggle_1, fiscal_toggle_2, fiscal_toggle_3,
                                      fiscal_toggle_4,
                                      timeframe_0, timeframe_1, timeframe_2, timeframe_3, timeframe_4,
                                      start_secondary_0, start_secondary_1, start_secondary_2, start_secondary_3,
                                      start_secondary_4,
                                      end_secondary_0, end_secondary_1, end_secondary_2, end_secondary_3,
                                      end_secondary_4,
                                      num_periods_0, num_periods_1, num_periods_2, num_periods_3, num_periods_4,
                                      period_type_0, period_type_1, period_type_2, period_type_3, period_type_4,
                                      date_tab_0, date_tab_1, date_tab_2, date_tab_3, date_tab_4,
                                      secondary_button_path, secondary_toggle, secondary_level, secondary_graph_all,
                                      secondary_options, layout, df_const):
    # ---------------------------------------Variable Declarations------------------------------------------------------
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    # loading Outputs
    options = no_update
    update_graph_options_trigger = no_update
    tile_title_returns = [no_update] * 4
    auto_named_titles = [no_update] * 4
    prompt_trigger = no_update
    float_menu_trigger = no_update
    popup_text = no_update
    popup_is_open = no_update
    dashboard_title_output = no_update
    tile_content_children = no_update
    dms = [{'Content': no_update, 'Tab': no_update, 'Start Year': no_update, 'End Year': no_update,
            'Start Secondary': no_update, 'End Secondary': no_update},
           {'Content': no_update, 'Tab': no_update, 'Start Year': no_update, 'End Year': no_update,
            'Start Secondary': no_update, 'End Secondary': no_update},
           {'Content': no_update, 'Tab': no_update, 'Start Year': no_update, 'End Year': no_update,
            'Start Secondary': no_update, 'End Secondary': no_update},
           {'Content': no_update, 'Tab': no_update, 'Start Year': no_update, 'End Year': no_update,
            'Start Secondary': no_update, 'End Secondary': no_update},
           {'Content': no_update, 'Tab': no_update, 'Start Year': no_update, 'End Year': no_update,
            'Start Secondary': no_update, 'End Secondary': no_update}]
    num_tiles = no_update
    df_const_wrapper = no_update
    dashboard_reset_trigger = no_update
    close_trigger = no_update
    # ------------------------------------------------------------------------------------------------------------------

    if changed_id == '.':
        raise PreventUpdate

    # if delete button was pressed, prompt delete
    if 'delete-dashboard' in changed_id:
        intermediate_pointer = DASHBOARD_POINTER_PREFIX + dashboard_title.replace(" ", "")
        dashboard_titles = []
        for dashboard in session['saved_dashboards']:
            dashboard_titles.append(session['saved_dashboards'][dashboard]['Dashboard Title'])

        # if tile exists in session, send delete prompt
        if intermediate_pointer in session['saved_dashboards'] \
                and session['saved_dashboards'][intermediate_pointer]['Dashboard Title'] == dashboard_title:
            prompt_trigger = dcc.Store(id={'type': 'prompt-trigger', 'index': 4},
                                       data=[['delete_dashboard', 4], {}, get_label('LBL_Delete_Dashboard'),
                                             get_label('LBL_Delete_Dashboard_Prompt').format(dashboard_title), False])
    elif 'dashboard-reset' in changed_id:
        prompt_trigger = dcc.Store(id={'type': 'prompt-trigger', 'index': 4},
                                   data=[['reset', 4], {}, get_label('LBL_Reset_Dashboard'),
                                         get_label('LBL_Reset_Dashboard_Prompt'),
                                         False])
    # if load button was pressed, send load menu
    elif 'load-dashboard' in changed_id:
        float_menu_trigger = dcc.Store(id={'type': 'float-menu-trigger', 'index': 4},
                                       data=[['dashboard_layouts', 4], {}, get_label('LBL_Load_Dashboard'),
                                             session['tile_edited'][4]])
    elif 'tile-close' in changed_id:
        if [p['value'] for p in dash.callback_context.triggered][0] is None:
            pass
        elif session['tile_edited'][int(search(r'\d+', changed_id).group())]:
            prompt_trigger = dcc.Store(id={'type': 'prompt-trigger', 'index': 4},
                                       data=[['close', int(search(r'\d+', changed_id).group())], {},
                                             get_label('LBL_Close_Graph'),
                                             get_label('LBL_Close_Graph_Prompt'), False])
        else:
            close_trigger = int(search(r'\d+', changed_id).group())
    # if confirm load, load dashboard
    elif 'float-menu-result' in changed_id \
            and float_menu_data[0] == 'dashboard_layouts' and selected_dashboard is not None \
            and float_menu_result == 'ok':
        tile_keys = [{}] * 4
        num_tiles = 0

        for dict_key, dict_value in session['saved_dashboards'][selected_dashboard].items():

            if 'Tile' in dict_key:

                num_tiles += 1

                tile_index = data_index = int(search(r'\d+', dict_key).group())

                # Change key to Tile Pointer instead of Tile Title
                tile_pointer = dict_value['Tile Pointer']
                link_state = dict_value['Link']

                if tile_pointer in session['saved_layouts']:
                    tile_data = session['saved_layouts'][tile_pointer].copy()
                    tile_title = tile_data.pop("Title")
                # TODO: In 'prod' we will check for pointers and only do a 'virtual' delete for
                #  the single user
                else:
                    tile_title = "This Graph has been deleted"
                    tile_data = {
                        "Args List": ["", "", ""],
                        "Graph Options": ["", "", "", "", "", ""],
                        "Data Set": "OPG011",  # "Data Set": "OPG001_2016-17_Week_v3.csv",
                        "Fiscal Toggle": "Gregorian",
                        "Graph All Toggle": [],
                        "Graph Type": "Line",
                        "Hierarchy Toggle": "Level Filter",
                        "Level Value": None,
                        "NID Path": "root",
                        "Num Periods": "5",
                        "Period Type": "last-years",
                        "Timeframe": "all-time",
                        "Title": "This Graph has been deleted"}

                # pop graph_type/args_list/graph_options/graph_variable to compare the dashboard parent data menu to
                # the saved tile data menu
                graph_type = tile_data.pop('Graph Type')
                args_list = tile_data.pop('Args List')
                graph_options = tile_data.pop('Graph Options')
                df_name = tile_data['Data Set']
                time_period = tile_data['Time Period']
                graph_variable = tile_data.pop('Graph Variable')

                if df_name != 'OPG010':
                    session_key = df_name + time_period
                else:
                    session_key = df_name

                # check if data is loaded
                if session_key not in session or (df_const is not None and session_key not in df_const):
                    session[session_key] = dataset_to_df(df_name, time_period)
                    if df_const is None:
                        df_const = {}
                    df_const[session_key] = generate_constants(df_name, session_key)

                if link_state == 'fa fa-link':
                    # if tile was linked but its data menu has changed and no longer matches parent data, unlink
                    if tile_data != session['saved_dashboards'][selected_dashboard]['Parent Data']:
                        link_state = 'fa fa-unlink'

                    # else, the tile is valid to be linked, generate parent menu if it has not been created yet
                    else:
                        data_index = 4

                # create tile keys
                graph_menu = load_graph_menu(graph_type=graph_type, tile=tile_index, df_name=df_name,
                                             args_list=args_list, graph_options=graph_options,
                                             graph_variable=graph_variable, df_const=df_const, session_key=session_key)

                customize_content = get_customize_content(tile=tile_index, graph_type=graph_type, graph_menu=graph_menu,
                                                          df_name=df_name)
                tile_key = {'Tile Title': tile_title,
                            'Link': link_state,
                            'Customize Content': customize_content,
                            'Rebuild Menu': False}
                tile_keys[tile_index] = tile_key

                # if tile is unlinked, or linked while the parent does not exist, create data menu
                if link_state == 'fa fa-unlink' or (link_state == 'fa fa-link' and dms[4]['Content'] == no_update):

                    hierarchy_type = tile_data['Hierarchy Type']
                    hierarchy_toggle = tile_data['Hierarchy Toggle']
                    level_value = tile_data['Level Value']
                    nid_path = tile_data['NID Path']
                    graph_all_toggle = tile_data['Graph All Toggle']
                    fiscal_toggle = tile_data['Fiscal Toggle']
                    timeframe = tile_data['Timeframe']
                    num_periods = tile_data['Num Periods']
                    period_type = tile_data['Period Type']

                    dms[data_index]['Content'] = get_data_menu(
                        tile=data_index, df_name=df_name, mode='dashboard-loading', hierarchy_toggle=hierarchy_toggle,
                        level_value=level_value, nid_path=nid_path,
                        graph_all_toggle=graph_all_toggle, fiscal_toggle=fiscal_toggle, input_method=timeframe,
                        num_periods=num_periods, period_type=period_type, prev_selection=None, time_period=time_period,
                        df_const=df_const, session_key=session_key, hier_type=hierarchy_type)

                    if timeframe == 'select-range':
                        dms[data_index]['Tab'] = tile_data['Date Tab']
                        dms[data_index]['Start Year'] = tile_data['Start Year']
                        dms[data_index]['End Year'] = tile_data['End Year']
                        dms[data_index]['Start Secondary'] = tile_data['Start Secondary']
                        dms[data_index]['End Secondary'] = tile_data['End Secondary']

        # outputs
        dashboard_title_output = session['saved_dashboards'][selected_dashboard]['Dashboard Title']
        tile_content_children = get_div_body(num_tiles=num_tiles,
                                             tile_keys=tile_keys,
                                             layout=session['saved_dashboards'][selected_dashboard]['Dashboard Layout'])
        df_const_wrapper = html.Div(
            html.Div(
                html.Div(
                    html.Div(
                        dcc.Store(
                            id='df-constants-storage',
                            storage_type='memory',
                            data=df_const),
                        id={'type': 'df-constants-storage-tile-wrapper', 'index': 0}),
                    id={'type': 'df-constants-storage-tile-wrapper', 'index': 1}),
                id={'type': 'df-constants-storage-tile-wrapper', 'index': 2}),
            id={'type': 'df-constants-storage-tile-wrapper', 'index': 3}),
        session['tile_edited'][4] = num_tiles  # set for load warning
    elif prompt_data is not None or 'save-dashboard' in changed_id:
        # if save requested or the over-write was confirmed, check for exceptions and save
        if 'save-dashboard' in changed_id or (prompt_data[0] == 'overwrite_dashboard' and prompt_result == 'ok'):
            dashboard_pointer = DASHBOARD_POINTER_PREFIX + dashboard_title.replace(" ", "")
            # regex.sub('[^A-Za-z0-9]+', '', dashboard_title)
            used_dashboard_titles = []

            for dashboard_layout in session['saved_dashboards']:
                used_dashboard_titles.append(session['saved_dashboards'][dashboard_layout]['Dashboard Title'])

            # auto name blank tile titles
            for idx, tile_title in enumerate(tile_titles):
                if tile_title == '':
                    auto_named_titles[idx] = tile_titles[idx] = dashboard_title + '-' + str(idx + 1)

            used_titles = []

            for tile_layout in session['saved_layouts']:
                used_titles.append(session['saved_layouts'][tile_layout]["Title"])

            # check if the dashboard title is blank
            if dashboard_title == '':
                prompt_trigger = dcc.Store(id={'type': 'prompt-trigger', 'index': 4},
                                           data=[['empty_title', 4], {}, get_label('LBL_Untitled_Dashboard'),
                                                 get_label('LBL_Untitled_Dashboard_Prompt'), False])
                # get_label('LBL_Dashboards_Require_A_Title_To_Be_Saved')
            # check if the dashboard is empty
            elif len(links) == 0:
                prompt_trigger = dcc.Store(id={'type': 'prompt-trigger', 'index': 4},
                                           data=[['empty_dashboard', 4], {}, get_label('LBL_Empty_Dashboard'),
                                                 get_label('LBL_Empty_Dashboard_Prompt'), False])
                # get_label('LBL_Dashboard_Must_Not_Be_Empty')
            # if conflicting tiles or dashboard and overwrite not requested, prompt overwrite
            elif ((dashboard_title in used_dashboard_titles or any(x in used_titles for x in tile_titles))
                  and 'prompt-result' not in changed_id):
                # dashboard-overwrite index 0 = confirm overwrite
                # dashboard-overwrite index 1 = cancel overwrite
                # if conflicting graph titles

                if any(x in used_titles for x in tile_titles or dashboard_title in used_dashboard_titles):
                    conflicting_graphs = ''
                    conflicting_graphs_list = [i for i in tile_titles if i in used_titles]
                    for idx, conflicting_graph in enumerate(conflicting_graphs_list):
                        conflicting_graphs += '\'' + conflicting_graph + '\''
                        if idx != (len(conflicting_graphs_list) - 1):
                            conflicting_graphs += ', '
                    # if conflicting graph titles and dashboard title
                    if dashboard_title in used_dashboard_titles:  # was session['saved_dashboards']
                        prompt_trigger = dcc.Store(id={'type': 'prompt-trigger', 'index': 4},
                                                   data=[['overwrite_dashboard', 4], {},
                                                         get_label('LBL_Overwrite_Dashboard'),
                                                         get_label(
                                                             'LBL_Overwrite_Dashboard_C_Title_Graph_Prompt').format(
                                                             dashboard_title, conflicting_graphs_list), False])
                    # else, just conflicting graph titles
                    else:
                        prompt_trigger = dcc.Store(id={'type': 'prompt-trigger', 'index': 4},
                                                   data=[['overwrite_dashboard', 4], {},
                                                         get_label('LBL_Overwrite_Dashboard'),
                                                         get_label('LBL_Overwrite_Dashboard_C_Graph_Prompt').format(
                                                             conflicting_graphs_list), False])
                # else, just conflicting dashboard title
                else:
                    prompt_trigger = dcc.Store(id={'type': 'prompt-trigger', 'index': 4},
                                               data=[['overwrite_dashboard', 4], {},
                                                     get_label('LBL_Overwrite_Dashboard'),
                                                     get_label('LBL_Overwrite_Dashboard_C_Title_Prompt').format(
                                                         dashboard_title),
                                                     False])
            # else, save/overwrite the dashboard and contained tiles
            else:
                df_names = [df_name_0, df_name_1, df_name_2, df_name_3, df_name_4]
                time_periods = [time_period_0, time_period_1, time_period_2, time_period_3, time_period_4]
                start_years = [start_year_0, start_year_1, start_year_2, start_year_3, start_year_4]
                end_years = [end_year_0, end_year_1, end_year_2, end_year_3, end_year_4]
                hierarchy_types = [hierarchy_type_0, hierarchy_type_1, hierarchy_type_2, hierarchy_type_3,
                                   hierarchy_type_4]
                hierarchy_toggles = [hierarchy_toggle_0, hierarchy_toggle_1, hierarchy_toggle_2, hierarchy_toggle_3,
                                     hierarchy_toggle_4]
                graph_all_toggles = [graph_all_toggle_0, graph_all_toggle_1, graph_all_toggle_2, graph_all_toggle_3,
                                     graph_all_toggle_4]
                level_values = [level_value_0, level_value_1, level_value_2, level_value_3, level_value_4]
                button_paths = [button_path_0, button_path_1, button_path_2, button_path_3, button_path_4]
                fiscal_toggles = [fiscal_toggle_0, fiscal_toggle_1, fiscal_toggle_2, fiscal_toggle_3, fiscal_toggle_4]
                timeframes = [timeframe_0, timeframe_1, timeframe_2, timeframe_3, timeframe_4]
                start_secondaries = [start_secondary_0, start_secondary_1, start_secondary_2, start_secondary_3,
                                     start_secondary_4]
                end_secondaries = [end_secondary_0, end_secondary_1, end_secondary_2, end_secondary_3, end_secondary_4]
                num_periods = [num_periods_0, num_periods_1, num_periods_2, num_periods_3, num_periods_4]
                period_types = [period_type_0, period_type_1, period_type_2, period_type_3, period_type_4]
                date_tabs = [date_tab_0, date_tab_1, date_tab_2, date_tab_3, date_tab_4]
                dashboard_saves = {'Dashboard Title': dashboard_title, 'Dashboard Layout': layout}
                arg_list_all = [args_list_0, args_list_1, args_list_2, args_list_3]
                graph_options_all = [xaxis_titles, yaxis_titles, x_leg_pos, y_leg_pos, xmodified, ymodified, gridline,
                                     legend]

                # if any tiles are linked, save the parent data menu
                if links.count('fa fa-link') > 0:
                    if type(button_paths[4]) == dict:
                        button_paths[4] = [button_paths[4]]

                    # Creates a hierarchy trail from the display buttons
                    parent_nid_path = "root"
                    for button in button_paths[4]:
                        parent_nid_path += '^||^{}'.format(button['props']['children'])

                    parent_data = {
                        'Fiscal Toggle': fiscal_toggles[4],
                        'Timeframe': timeframes[4],
                        'Num Periods': num_periods[4],
                        'Hierarchy Type': hierarchy_types[4],
                        'Hierarchy Toggle': hierarchy_toggles[4],
                        'Period Type': period_types[4],
                        'Level Value': level_values[4],
                        'Data Set': df_names[4],
                        'Time Period': time_periods[4],
                        'Graph All Toggle': graph_all_toggles[4],
                        'NID Path': parent_nid_path,
                    }

                    # if input method is 'select-range', add the states of the select range inputs
                    if timeframes[4] == 'select-range':
                        parent_data['Date Tab'] = date_tabs[4]
                        parent_data['Start Year'] = start_years[4]
                        parent_data['End Year'] = end_years[4]
                        parent_data['Start Secondary'] = start_secondaries[4]
                        parent_data['End Secondary'] = end_secondaries[4]

                    dashboard_saves['Parent Data'] = parent_data

                for i in range(len(links)):
                    tile_pointer = REPORT_POINTER_PREFIX + tile_titles[i].replace(" ", "")
                    # regex.sub('[^A-Za-z0-9]+', '', tile_titles[i])
                    used_titles = []

                    for key in session['saved_layouts']:
                        used_titles.append(session['saved_layouts'][key]["Title"])

                    if type(secondary_button_path[i]) == dict:
                        secondary_button_path[i] = [secondary_button_path[i]]

                    # Creates a secondary hierarchy trail from the display buttons
                    secondary_nid_path = "root"
                    for button in secondary_button_path[i]:
                        secondary_nid_path += '^||^{}'.format(button['props']['children'])

                    # set up Graph Options, Graph Variable and args
                    args_list = arg_list_all[i]
                    graph_options = [x[i] for x in graph_options_all if len(x) >= (i + 1)]
                    graph_variable = [secondary_level[i], secondary_nid_path, secondary_toggle[i],
                                      secondary_graph_all[i], secondary_options[i]]

                    if type(button_paths[i]) == dict:
                        button_paths[i] = [button_paths[i]]
                    # Creates a hierarchy trail from the display buttons
                    nid_path = "root"
                    for button in button_paths[i]:
                        nid_path += '^||^{}'.format(button['props']['children'])

                    # ---------- save dashboard reference to tile ----------
                    dashboard_saves['Tile ' + str(i)] = {
                        'Tile Pointer': tile_pointer,
                        # 'Tile Title': tile_titles[i],
                        'Link': links[i]
                    }
                    # ---------- save tile ----------
                    # if tile is unlinked, save data menu
                    if links[i] == 'fa fa-unlink':
                        tile_data = {
                            'Fiscal Toggle': fiscal_toggles[i],
                            'Timeframe': timeframes[i],
                            'Num Periods': num_periods[i],
                            'Hierarchy Type': hierarchy_types[i],
                            'Hierarchy Toggle': hierarchy_toggles[i],
                            'Period Type': period_types[i],
                            'Level Value': level_values[i],
                            'Data Set': df_names[i],
                            'Time Period': time_periods[i],
                            'Graph All Toggle': graph_all_toggles[i],
                            'NID Path': nid_path,
                        }

                        # if input method is 'select-range', add the states of the select range inputs
                        if timeframes[i] == 'select-range':
                            tile_data['Date Tab'] = date_tabs[i]
                            tile_data['Start Year'] = start_years[i]
                            tile_data['End Year'] = end_years[i]
                            tile_data['Start Secondary'] = start_secondaries[i]
                            tile_data['End Secondary'] = end_secondaries[i]
                    else:
                        tile_data = dashboard_saves['Parent Data']

                    # save tile to file
                    save_layout_state(tile_pointer, {'Graph Type': graph_types[i], 'Args List': args_list,
                                                     'Graph Options': graph_options, **tile_data,
                                                     'Title': tile_titles[i], 'Graph Variable': graph_variable})
                    # save_layout_to_file(session['saved_layouts'])
                    save_layout_to_db(tile_pointer, tile_titles[i], tile_titles[i] not in used_titles)

                # save dashboard to file
                # Change to a dashboard pointer from dashboard_title
                save_dashboard_state(dashboard_pointer, dashboard_saves)
                # save_dashboard_to_file(session['saved_dashboards'])
                save_dashboard_to_db(dashboard_pointer, dashboard_title, dashboard_title not in used_dashboard_titles)
                update_graph_options_trigger = 'trigger'
                tile_title_returns = auto_named_titles
                options = [{'label': session['saved_dashboards'][key]['Dashboard Title'], 'value': key} for key in
                           session['saved_dashboards']]
                popup_text = get_label('LBL_Your_Dashboard_Has_Been_Saved').format(dashboard_title)
                popup_is_open = True

        # if prompt result confirm delete, has been pressed
        elif prompt_data[0] == 'delete_dashboard' and prompt_result == 'ok':
            intermediate_pointer = DASHBOARD_POINTER_PREFIX + dashboard_title.replace(" ", "")
            delete_dashboard(intermediate_pointer)
            update_graph_options_trigger = 'trigger'
            options = [{'label': session['saved_dashboards'][key]["Dashboard Title"], 'value': key} for key
                       in session['saved_dashboards']]
            popup_text = get_label('LBL_Your_Dashboard_Has_Been_Deleted').format(dashboard_title)
            popup_is_open = True
        # if reset confirmed, trigger reset
        elif prompt_data[0] == 'reset' and 'prompt-result' in changed_id and prompt_result == 'ok':
            dashboard_reset_trigger = 'trigger'
            popup_text = get_label('LBL_Your_Dashboard_Has_Been_Reset')
            popup_is_open = True
        elif prompt_data[0] == 'close' and prompt_result == 'ok':
            close_trigger = prompt_data[1]

    return options, update_graph_options_trigger, tile_title_returns[0], tile_title_returns[1], tile_title_returns[2], \
        tile_title_returns[3], prompt_trigger, float_menu_trigger, popup_text, popup_is_open, dashboard_title_output, \
        tile_content_children, \
        dms[0]['Content'], dms[0]['Tab'], dms[0]['Start Year'], dms[0]['End Year'], dms[0]['Start Secondary'], \
        dms[0]['End Secondary'], \
        dms[1]['Content'], dms[1]['Tab'], dms[1]['Start Year'], dms[1]['End Year'], dms[1]['Start Secondary'], \
        dms[1]['End Secondary'], \
        dms[2]['Content'], dms[2]['Tab'], dms[2]['Start Year'], dms[2]['End Year'], dms[2]['Start Secondary'], \
        dms[2]['End Secondary'], \
        dms[3]['Content'], dms[3]['Tab'], dms[3]['Start Year'], dms[3]['End Year'], dms[3]['Start Secondary'], \
        dms[3]['End Secondary'], \
        dms[4]['Content'], dms[4]['Tab'], dms[4]['Start Year'], dms[4]['End Year'], dms[4]['Start Secondary'], \
        dms[4]['End Secondary'], \
        close_trigger, num_tiles, df_const_wrapper, dashboard_reset_trigger


# *********************************************SHARED LOADING********************************************************

# Load select range inputs, prompting the date picker callback to instantiate the layout of the date-picker for us.
@app.callback(
    [Output({'type': 'start-year-input', 'index': MATCH}, 'name'),
     Output({'type': 'start-year-input', 'index': MATCH}, 'value'),
     Output({'type': 'end-year-input', 'index': MATCH}, 'value'),
     Output({'type': 'start-secondary-input', 'index': MATCH}, 'value'),
     Output({'type': 'end-secondary-input', 'index': MATCH}, 'value')],
    [Input({'type': 'select-range-trigger', 'index': MATCH}, 'data-tile-tab'),
     Input({'type': 'select-range-trigger', 'index': MATCH}, 'data-dashboard-tab')],
    [State({'type': 'select-range-trigger', 'index': MATCH}, 'data-tile-start_year'),
     State({'type': 'select-range-trigger', 'index': MATCH}, 'data-tile-end_year'),
     State({'type': 'select-range-trigger', 'index': MATCH}, 'data-tile-start_secondary'),
     State({'type': 'select-range-trigger', 'index': MATCH}, 'data-tile-end_secondary'),
     State({'type': 'select-range-trigger', 'index': MATCH}, 'data-dashboard-start_year'),
     State({'type': 'select-range-trigger', 'index': MATCH}, 'data-dashboard-end_year'),
     State({'type': 'select-range-trigger', 'index': MATCH}, 'data-dashboard-start_secondary'),
     State({'type': 'select-range-trigger', 'index': MATCH}, 'data-dashboard-end_secondary')],
    prevent_initial_call=True
)
def _load_select_range_inputs(tile_tab, dashboard_tab, tile_start_year, tile_end_year, tile_start_secondary,
                              tile_end_secondary, dashboard_start_year, dashboard_end_year, dashboard_start_secondary,
                              dashboard_end_secondary):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if changed_id == '.':
        raise PreventUpdate

    # if loading type is tile
    if 'data-tile-tab' in changed_id:
        date_tab = tile_tab
        start_year = tile_start_year
        end_year = tile_end_year
        start_secondary = tile_start_secondary
        end_secondary = tile_end_secondary
    # else, loading type is dashboard
    else:
        date_tab = dashboard_tab
        start_year = dashboard_start_year
        end_year = dashboard_end_year
        start_secondary = dashboard_start_secondary
        end_secondary = dashboard_end_secondary

    return date_tab, start_year, end_year, start_secondary, end_secondary


# Resets selected dashboard dropdown value to ''.
app.clientside_callback(
    """
    function(_trigger){
        return null;
    }
    """,
    Output('select-dashboard-dropdown', 'value'),
    [Input({'type': 'data-menu-dashboard-loading', 'index': ALL}, 'children')],
    prevent_initial_call=True
)
