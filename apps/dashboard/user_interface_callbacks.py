######################################################################################################################
"""
user_interface_callbacks.py

stores all callbacks for the user interface
"""
######################################################################################################################

# External Packages
# from datetime import datetime

import dash
import dash_html_components as html
import copy
from dash.dependencies import Input, Output, State, ALL, MATCH, ClientsideFunction
from dash.exceptions import PreventUpdate
from re import search
from dash import no_update
from urllib.parse import parse_qsl
from flask import url_for

# Internal Packages
from apps.dashboard.layouts import get_line_graph_menu, get_bar_graph_menu, get_scatter_graph_menu, get_table_graph_menu, \
    get_tile_layout, change_index, get_box_plot_menu, get_default_tab_content, get_layout_dashboard, get_layout_graph, \
    get_data_menu, get_sankey_menu, get_dashboard_title_input, get_bubble_graph_menu
from apps.dashboard.app import app
from apps.dashboard.data import VIEW_CONTENT_HIDE, VIEW_CONTENT_SHOW, CUSTOMIZE_CONTENT_HIDE, CUSTOMIZE_CONTENT_SHOW, \
    DATA_CONTENT_HIDE, DATA_CONTENT_SHOW, get_label, LAYOUT_CONTENT_SHOW, LAYOUT_CONTENT_HIDE, X_AXIS_OPTIONS, \
    session, BAR_X_AXIS_OPTIONS, generate_constants, dataset_to_df


# Contents:
#   MAIN LAYOUT
#       - _generate_layout()
#       - _new_and_delete()
#       - _unlock_new_button()
#   TAB LAYOUT
#       - _change_tab()
#       - _update_num_tiles()
#       - _update_tab_tile()
#   TILE LAYOUT
#       - _switch_tile_tab()
#   CUSTOMIZE TAB
#       - _update_graph_menu()
#   DATA SIDE-MENU
#       - _change_link()
#       - _manage_data_sidemenus()
#       - _highlight_slaved_tiles()


# *************************************************MAIN LAYOUT********************************************************

# determine layout on callback
# https://community.plotly.com/t/dash-on-multi-page-site-app-route-flask-to-dash/4582/11
@app.callback(Output('page-content', 'children'),
              [Input('url', 'href')],
              [State('url', 'pathname'), State('url', 'search')],
              prevent_initial_call=True)
def _generate_layout(href, pathname, query_string):
    # print('HREF:', href)
    # print('PATHNAME:', pathname)
    # print('SEARCH:', query_string)

    if not query_string:
        query_string = '?'

    query_params = dict(parse_qsl(query_string.strip('?')))

    if 'reportName' in query_params and query_params['reportName']:
        return [get_layout_graph(query_params['reportName'])]
    else:
        if session['language'] == 'En':
            return [get_layout_dashboard()]
        else:
            return [html.Div([get_layout_dashboard(),
                              html.Link(rel='stylesheet', href=url_for("static",filename="BBB - french stylesheet1.css"))])]


# Handles Resizing of ContentWrapper, uses tab-content-wrapper n-clicks as a throw away output
# takes x,y,z and throw away inputs to trigger when tabs are modified
app.clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='resizeContentWrapper'
    ),
    Output('tab-content-wrapper', 'n_clicks'),
    [Input({'type': 'dashboard-tab', 'index': ALL}, 'n_clicks'),
     Input({'type': 'dashboard-tab-close', 'index': ALL}, 'n_clicks'),
     Input('tab-add', 'n_clicks')]
)


# NEW and DELETE button functionality
@app.callback(
    [Output('div-body', 'children'),
     Output('button-new-wrapper', 'children'),
     Output('tile-closed-trigger', 'data-'),
     Output('num-tiles-2', 'data-num-tiles'),
     Output('dashboard-reset-trigger', 'data-')],
    [Input('button-new', 'n_clicks'),
     Input({'type': 'tile-close', 'index': ALL}, 'n_clicks'),
     Input('confirm-dashboard-reset', 'n_clicks')],
    [State({'type': 'tile', 'index': ALL}, 'children'),
     State('num-tiles', 'data-num-tiles'),
     State('button-new', 'disabled'),
     State('df-constants-storage', 'data')],
    prevent_initial_call=True
)
def _new_and_delete(new_clicks, _close_clicks, dashboard_reset, input_tiles, num_tiles, new_disabled, df_const):
    """
    :param new_clicks: Detects user clicking 'NEW' button in master navigation bar and encodes the number of tiles to
    display
    :param _close_clicks: Detects user clicking close ('x') button in top right of tile
    :param input_tiles: State of all currently existing tiles
    :return: Layout of tiles for the main body, a new NEW button whose n_clicks data encodes the number of tiles to
    display, and updates the tile-closed-trigger div with the index of the deleted tile
    """

    # if NEW callback chain has not been completed and NEW button enabled, prevent update
    if new_disabled:
        raise PreventUpdate

    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    changed_value = [p['value'] for p in dash.callback_context.triggered][0]
    deleted_tile = no_update
    dashboard_reset_trigger = no_update

    # if DELETE button pressed: pop deleted input_tile index and shift following indices left and adjust main layout
    if 'tile-close' in changed_id and num_tiles != 0 and changed_value is not None:
        num_tiles -= 1
        flag = False
        for i in range(len(input_tiles)):
            if '{"index":{},"type":"tile-close"}.n_clicks'.replace("{}", str(i)) in changed_id:
                input_tiles.pop(i)
                flag = True
                deleted_tile = str(i)
            elif flag:
                input_tiles[i - 1] = change_index(input_tiles[i - 1], i - 1)
        children = get_tile_layout(num_tiles, input_tiles, df_const=df_const)
    # if NEW button pressed: adjust main layout and disable NEW button until it is unlocked at the end of callback chain
    elif 'button-new' in changed_id:
        if num_tiles == 4:
            raise PreventUpdate
        num_tiles += 1
        children = get_tile_layout(num_tiles, input_tiles, df_const=df_const)
    # if RESET dashboard requested, set dashboard to default appearance
    elif 'dashboard-reset' in changed_id:
        num_tiles = 1
        children = get_tile_layout(num_tiles, [], df_const=df_const)
        dashboard_reset_trigger = 'trigger'
    # else, a tab change was made, prevent update
    else:
        raise PreventUpdate
    # disable the NEW button
    new_button = html.Button(
        className='master-nav', n_clicks=0, children=get_label('LBL_New'), id='button-new', disabled=True)
    return children, new_button, deleted_tile, num_tiles, dashboard_reset_trigger


# unlock NEW button after end of callback chain
@app.callback(
    Output('button-new', 'disabled'),
    [Input({'type': 'div-graph-options', 'index': ALL}, 'children')],
    [State('button-new', 'disabled')],
    prevent_initial_call=True
)
def _unlock_new_button(graph_options, disabled):
    """
    :param graph_options: Detects when the last callback, _update_graph_menu, in the UI update order finishes and
    encodes the state of all graph menus
    :return: Enables the NEW button
    """
    # do not unlock NEW button if already unlocked
    if not disabled:
        raise PreventUpdate
    return False


# *************************************************TAB LAYOUT********************************************************

# manage tab saves
@app.callback(
    [Output('tab-storage', 'data'),
     Output('tab-content-wrapper', 'data-active-tab'),
     Output('tab-header', 'children'),
     Output('tab-content', 'children'),
     Output('num-tiles-3', 'data-num-tiles'),
     Output('dashboard-title-wrapper', 'children')],
    [Input({'type': 'dashboard-tab', 'index': ALL}, 'n_clicks'),
     Input({'type': 'dashboard-tab-close', 'index': ALL}, 'n_clicks'),
     Input('tab-add', 'n_clicks')],
    [State('tab-content', 'children'),
     State('tab-content-wrapper', 'data-active-tab'),
     State('tab-storage', 'data'),
     State('tab-header', 'children'),
     State('button-new', 'disabled'),
     State('dashboard-title', 'value')],
    prevent_initial_call=True
)
def _change_tab(tab_clicks, tab_close_clicks, _tab_add_nclicks,
                tab_content, active_tab, data, tab_toggle_children, new_disabled, dashboard_title):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    # if page loaded (changed_id == '.') or new button is disabled, prevent update
    if changed_id == '.' or new_disabled:
        raise PreventUpdate

    # if user requested to add a new tab
    if 'tab-add.n_clicks' in changed_id:
        if len(tab_toggle_children) >= 12:
            raise PreventUpdate
        tab_toggle_children = tab_toggle_children + [
            html.Div([
                html.Button(
                    get_label("LBL_Tab"),
                    id={'type': 'dashboard-tab', 'index': len(tab_toggle_children)},
                    className='dashboard-tab-button'),
                html.Button(
                    "x",
                    id={'type': 'dashboard-tab-close', 'index': len(tab_toggle_children)},
                    className='dashboard-tab-close')],
                className='dashboard-tab')]
        data.append({'content': get_default_tab_content(), 'title': ''})
        return data, active_tab, tab_toggle_children, no_update, no_update, no_update

    # if user requested to delete a tab
    if '"type":"dashboard-tab-close"}.n_clicks' in changed_id:
        deleted_tab_index = int(search(r'\d+', changed_id).group())
        # this is shifting logic to act like chrome or any other internet browser
        if deleted_tab_index == active_tab:
            if active_tab == len(data) - 1:
                new_tab = active_tab - 1
            else:
                new_tab = active_tab
            # if requesting to delete the only tab prevent it
            if new_tab < 0:
                raise PreventUpdate
        elif deleted_tab_index > active_tab:
            new_tab = active_tab
        else:
            new_tab = active_tab - 1
        # remove the tab and its x from the children
        del tab_toggle_children[deleted_tab_index]
        # remove the tabs data from the storage
        del data[deleted_tab_index]
        # shift all tab button indices down one following deleted tab
        for i in tab_toggle_children[deleted_tab_index:]:
            # decremement close button index
            i['props']['children'][0]['props']['id']['index'] -= 1
            # decrement tab button index
            i['props']['children'][1]['props']['id']['index'] -= 1
        # set active tab style as selected
        tab_toggle_children[new_tab]['props']['className'] = 'dashboard-tab-selected'
        # disable active tab button
        tab_toggle_children[new_tab]['props']['children'][0]['props']['disabled'] = True
        # set active tab close button style as selected
        tab_toggle_children[new_tab]['props']['children'][1]['props']['className'] = 'dashboard-tab-close-selected'
        # force a load if required else return new tab that's been shifted
        if deleted_tab_index == active_tab:
            title_wrapper = get_dashboard_title_input(data[new_tab]['title'])
            return data, new_tab, tab_toggle_children, data[new_tab]['content'], no_update, title_wrapper
        return data, new_tab, tab_toggle_children, no_update, no_update, no_update

    # else, user requested a tab change
    new_tab = int(search(r'\d+', changed_id).group())
    # if user requested the active tab, prevent update
    if new_tab == active_tab:
        raise PreventUpdate
    # else, user requested a different tab. Save the current tab content to the appropriate save location and swap tabs
    data[active_tab]['content'] = tab_content
    data[active_tab]['title'] = dashboard_title
    # set old active tab style as unselected
    tab_toggle_children[active_tab]['props']['className'] = 'dashboard-tab'
    # enable old active tab button
    tab_toggle_children[active_tab]['props']['children'][0]['props']['disabled'] = False
    # set old active tab close button style as unselected
    tab_toggle_children[active_tab]['props']['children'][1]['props']['className'] = 'dashboard-tab-close'
    # set new tab style as selected
    tab_toggle_children[new_tab]['props']['className'] = 'dashboard-tab-selected'
    # disable new tab button
    tab_toggle_children[new_tab]['props']['children'][0]['props']['disabled'] = True
    # set new tab close button style as selected
    tab_toggle_children[new_tab]['props']['children'][1]['props']['className'] = 'dashboard-tab-close-selected'
    # set the number of tiles to the number of tiles in the new tab
    num_tiles = data[new_tab]['content'][0]['props']['data-num-tiles']
    # create dashboard title wrapper
    title_wrapper = get_dashboard_title_input(data[new_tab]['title'])
    return data, new_tab, tab_toggle_children, data[new_tab]['content'], num_tiles, title_wrapper


# update num-tiles
@app.callback(
    Output('num-tiles', 'data-num-tiles'),
    [Input('num-tiles-2', 'data-num-tiles'),
     Input('num-tiles-3', 'data-num-tiles'),
     Input('num-tiles-4', 'data-num-tiles')],
    prevent_initial_call=True
)
def _update_num_tiles(input1, input2, input3):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if changed_id == '.':
        raise PreventUpdate

    if 'num-tiles-2' in changed_id:
        result = input1

    if 'num-tiles-3' in changed_id:
        result = input2

    if 'num-tiles-4' in changed_id:
        result = input3

    return result


# update tab name
@app.callback(
    Output({'type': 'dashboard-tab', 'index': ALL}, 'children'),
    [Input('dashboard-title', 'value')],
    [State('tab-content-wrapper', 'data-active-tab'),
     State({'type': 'dashboard-tab', 'index': ALL}, 'children')],
    prevent_initial_call=True
)
def _update_tab_title(title, active_tab, list_of_children):
    if title == '':
        list_of_children[active_tab] = get_label('LBL_Tab')
    else:
        if len(title) > 5:
            title = title[:3] + '...'
        list_of_children[active_tab] = title
    return list_of_children


# *************************************************TILE LAYOUT********************************************************

# manage VIEW <-> CUSTOMIZE <--> LAYOUTS for each tab
for x in range(4):
    @app.callback(
        [Output({'type': 'tile-view-content', 'index': x}, 'style'),
         Output({'type': 'tile-customize-content', 'index': x}, 'style'),
         Output({'type': 'tile-layouts-content', 'index': x}, 'style'),
         Output({'type': 'tile-view', 'index': x}, 'className'),
         Output({'type': 'tile-layouts', 'index': x}, 'className'),
         Output({'type': 'tile-customize', 'index': x}, 'className')],
        [Input({'type': 'tile-view', 'index': x}, 'n_clicks'),
         Input({'type': 'tile-customize', 'index': x}, 'n_clicks'),
         Input({'type': 'tile-layouts', 'index': x}, 'n_clicks')],
        [State({'type': 'tile-view-content', 'index': x}, 'style'),
         State({'type': 'tile-customize-content', 'index': x}, 'style'),
         State({'type': 'tile-layouts-content', 'index': x}, 'style'),
         State({'type': 'tile-view', 'index': x}, 'className'),
         State({'type': 'tile-customize', 'index': x}, 'className'),
         State({'type': 'tile-layouts', 'index': x}, 'className')],
        prevent_initial_call=True
    )
    def _switch_tile_tab(_view_clicks, _customize_clicks, _layouts_clicks, view_content_style_state,
                         customize_content_style_state, layouts_content_style_state, view_state, customize_state,
                         layouts_state):
        """
        :param _view_clicks: Detects the user clicking the VIEW button
        :param _customize_clicks: Detects the user clicking the CUSTOMIZE button
        :param view_content_style_state: Style of the VIEW tab, either VIEW_CONTENT_SHOW or
        VIEW_CONTENT_HIDE
        :param customize_content_style_state: Style of the CUSTOMIZE tab, either CUSTOMIZE_CONTENT_SHOW or
        CUSTOMIZE_CONTENT_HIDE
        :param view_state: ClassName of the VIEW button, either 'tile-nav-selected' or 'tile-nav'
        :param customize_state: ClassName of the CUSTOMIZE button, either 'tile-nav-selected' or 'tile-nav'
        :return: The styles of the CUSTOMIZE and VIEW tabs as being either hidden or shown, and the classNames of the
        VIEW and CUSTOMIZE buttons as being either selected or unselected
        """
        changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

        # if view button was pressed, display view content and set view button as selected
        if '"type":"tile-view"}.n_clicks' in changed_id:
            # protect against spam clicking
            if view_content_style_state == VIEW_CONTENT_SHOW:
                raise PreventUpdate
            view_content_style = VIEW_CONTENT_SHOW
            customize_content_style = CUSTOMIZE_CONTENT_HIDE
            layouts_content_style = LAYOUT_CONTENT_HIDE
            view_className = 'tile-nav tile-nav--view tile-nav--selected'
            customize_className = 'tile-nav tile-nav--customize'
            layouts_className = 'tile-nav tile-nav--layout'

        # if customize button was pressed, display customize content and set customize button as selected
        elif '"type":"tile-customize"}.n_clicks' in changed_id:
            # protect against spam clicking
            if customize_content_style_state == CUSTOMIZE_CONTENT_SHOW:
                raise PreventUpdate
            view_content_style = VIEW_CONTENT_HIDE
            customize_content_style = CUSTOMIZE_CONTENT_SHOW
            layouts_content_style = LAYOUT_CONTENT_HIDE
            view_className = 'tile-nav tile-nav--view'
            customize_className = 'tile-nav tile-nav--customize tile-nav--selected'
            # if the main layout was updated by DELETE or NEW or page loaded (meaning changed_id == '.'), prevent update
            layouts_className = 'tile-nav tile-nav--layout'
            # if layouts button was pressed, display layouts content and set layouts button as selected

        elif '"type":"tile-layouts"}.n_clicks' in changed_id:
            # protect against spam clicking
            if layouts_content_style_state == LAYOUT_CONTENT_SHOW:
                raise PreventUpdate
            view_content_style = VIEW_CONTENT_HIDE
            customize_content_style = CUSTOMIZE_CONTENT_HIDE
            layouts_content_style = LAYOUT_CONTENT_SHOW
            view_className = 'tile-nav tile-nav--view'
            customize_className = 'tile-nav tile-nav--customize'
            layouts_className = 'tile-nav tile-nav--layout tile-nav--selected'

        # if the main layout was updated by DELETE or NEW or page loaded (meaning changed_id == '.'), prevent update
        else:
            raise PreventUpdate

        return view_content_style, customize_content_style, layouts_content_style, view_className, layouts_className, \
               customize_className

for x in range(4):
    app.clientside_callback(
        ClientsideFunction(
            namespace='clientside',
            function_name='graphLoadScreen{}'.format(x)
        ),
        Output({'type': 'tile-menu-header', 'index': x}, 'n_clicks'),
        [Input({'type': 'tile-view', 'index': x}, 'n_clicks')],
        [State({'type': 'tile-view', 'index': x}, 'className')]
    )

    app.clientside_callback(
        ClientsideFunction(
            namespace='clientside',
            function_name='graphRemoveLoadScreen{}'.format(x)
        ),
        Output({'type': 'graph_display', 'index': x}, 'n_clicks'),
        [Input({'type': 'graph_display', 'index': x}, 'children')]
    )

# ************************************************CUSTOMIZE TAB*******************************************************

# update graph menu to match selected graph type
for x in range(4):
    @app.callback(
        [Output({'type': 'div-graph-options', 'index': x}, 'children'),
         Output({'type': 'update-graph-trigger', 'index': x}, 'data-graph_menu_trigger'),
         Output({'type': 'update-graph-trigger', 'index': x}, 'data-graph_menu_table_trigger')],
        [Input({'type': 'graph-menu-trigger', 'index': x}, 'data-'),
         Input({'type': 'graph-type-dropdown', 'index': x}, 'value'),
         Input({'type': 'tile-link', 'index': x}, 'className')],
        [State({'type': 'div-graph-options', 'index': x}, 'children'),
         State({'type': 'data-set', 'index': x}, 'value'),
         State({'type': 'data-set', 'index': 4}, 'value'),
         State('df-constants-storage', 'data')],
        prevent_initial_call=True
    )
    def _update_graph_menu(gm_trigger, selected_graph_type, link_state, graph_options_state, df_name, master_df_name,
                           df_const):
        """
        :param selected_graph_type: Selected graph type, ie. 'bar', 'line', etc.
        :param graph_options_state: State of the current graph options div
        :return: Graph menu corresponding to selected graph type
        """

        changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
        for item in dash.callback_context.triggered:
            if '"type":"tile-link"}.className' in item['prop_id']:
                changed_id = item['prop_id']

        if link_state == 'fa fa-link':
            df_name = master_df_name

        # if link state from unlinked --> linked and the data set has not changed, don't update menu, still update graph
        if ('"type":"tile-link"}.className' in changed_id and link_state == 'fa fa-link' and df_name == master_df_name)\
                or ('"type":"tile-link"}.className' in changed_id and link_state == 'fa fa-unlink'):
            return no_update, 1, no_update

        # if graph menu trigger has value 'tile closed' then a tile was closed, don't update menu, still update table
        if 'graph-menu-trigger"}.data-' in changed_id and gm_trigger == 'tile closed':
            return no_update, no_update, 1

        # if changed id == '.' and the graph menu already exists, prevent update
        if changed_id == '.' and graph_options_state or df_const is None or df_name not in df_const :
            raise PreventUpdate

        tile = int(dash.callback_context.inputs_list[0]['id']['index'])

        # apply graph selection and generate menu
        if selected_graph_type == 'Line':
            menu = get_line_graph_menu(tile=tile,
                                       x=X_AXIS_OPTIONS[0],
                                       y=df_const[df_name]['VARIABLE_OPTIONS'][0]['value'],
                                       measure_type=df_const[df_name]['MEASURE_TYPE_OPTIONS'][0],
                                       df_name=df_name,
                                       df_const=df_const)

        elif selected_graph_type == 'Bar':
            menu = get_bar_graph_menu(tile=tile,
                                      x=BAR_X_AXIS_OPTIONS[0],
                                      y=None if df_const is None else df_const[df_name]['VARIABLE_OPTIONS'][0]['value'],
                                      measure_type=None if df_const is None else
                                      df_const[df_name]['MEASURE_TYPE_OPTIONS'][0],
                                      df_name=df_name,
                                      df_const=df_const)

        elif selected_graph_type == 'Scatter':
            menu = get_scatter_graph_menu(tile=tile,
                                          x=X_AXIS_OPTIONS[0],
                                          y=None if df_const is None else
                                          df_const[df_name]['VARIABLE_OPTIONS'][0]['value'],
                                          measure_type=None if df_const is None else
                                          df_const[df_name]['MEASURE_TYPE_OPTIONS'][0],
                                          df_name=df_name,
                                          df_const=df_const)

        elif selected_graph_type == 'Bubble':
            menu = get_bubble_graph_menu(tile=tile,
                                         x=X_AXIS_OPTIONS[0],
                                         x_measure=None if df_const is None else
                                         df_const[df_name]['MEASURE_TYPE_OPTIONS'][0],
                                         y=X_AXIS_OPTIONS[0],
                                         y_measure=None if df_const is None else
                                         df_const[df_name]['MEASURE_TYPE_OPTIONS'][0],
                                         size=X_AXIS_OPTIONS[0],
                                         size_measure=None if df_const is None else
                                         df_const[df_name]['MEASURE_TYPE_OPTIONS'][0],
                                         df_name=df_name,
                                         df_const=df_const)

        elif selected_graph_type == 'Table':
            menu = get_table_graph_menu(tile=tile, number_of_columns=15)

        elif selected_graph_type == 'Box_Plot':
            menu = get_box_plot_menu(tile=tile,
                                     axis_measure=None if df_const is None else
                                     df_const[df_name]['MEASURE_TYPE_OPTIONS'][0],
                                     graphed_variables=None if df_const is None else
                                     df_const[df_name]['VARIABLE_OPTIONS'][0]['value'],
                                     graph_orientation='Horizontal',
                                     df_name=df_name,
                                     show_data_points=[],
                                     df_const=df_const)

        elif selected_graph_type == 'Sankey':
            menu = get_sankey_menu(tile=tile,
                                   graphed_options=None if df_const is None else
                                   df_const[df_name]['VARIABLE_OPTIONS'][0]['value'],
                                   df_name=df_name,
                                   df_const=df_const)

        else:
            raise PreventUpdate

        if '"type":"tile-link"}.className' in changed_id or 'graph-menu-trigger"}.data-' in changed_id:
            update_graph_trigger = 1
        else:
            update_graph_trigger = no_update

        return menu, update_graph_trigger, no_update


# ************************************************DATA SIDE-MENU******************************************************

# change link button appearance
@app.callback(
    Output({'type': 'tile-link', 'index': MATCH}, 'className'),
    [Input({'type': 'select-layout-dropdown', 'index': MATCH}, 'value'),
     Input({'type': 'tile-link', 'index': MATCH}, 'n_clicks')],
    [State({'type': 'tile-link', 'index': MATCH}, 'className')],
    prevent_initial_call=True
)
def _change_link(selected_layout, _link_clicks, link_state):
    """
    :param _link_clicks: Detects the user clicking the link/unlink icon
    :param link_state: State of the link/unlink icon
    :return: New state of the link/unlink icon
    """
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    # if link button was not pressed and layout was not selected, do not update
    if '.' == changed_id:
        raise PreventUpdate

    if '"type":"select-layout-dropdown"}.value' in changed_id:
        if link_state == 'fa fa-link':
            link_state = 'fa fa-unlink'
        else:
            raise PreventUpdate

    if '"type":"tile-link"}.n_clicks' in changed_id:
        # if link button was pressed, toggle the link icon linked <--> unlinked
        link_state = 'fa fa-unlink' if link_state == 'fa fa-link' else 'fa fa-link'

    return link_state


app.clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='datasetLoadScreen'
    ),
    Output('dataset-confirmation-symbols', 'n_clicks'),
    [Input({'type': 'confirm-load-data', 'index': ALL}, 'n_clicks'),
     Input({'type': 'confirm-data-set-refresh', 'index': ALL}, 'n_clicks')]
)

app.clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='datasetRemoveLoadScreen'
    ),
    Output('df-constants-storage', 'n_clicks'),
    [Input('df-constants-storage', 'data')]
)


# manage data sidemenu appearance and content
@app.callback(
    [Output({'type': 'data-tile', 'index': 0}, 'children'),
     Output({'type': 'data-tile', 'index': 1}, 'children'),
     Output({'type': 'data-tile', 'index': 2}, 'children'),
     Output({'type': 'data-tile', 'index': 3}, 'children'),
     Output({'type': 'data-tile', 'index': 4}, 'children'),
     Output({'type': 'data-tile', 'index': 0}, 'style'),
     Output({'type': 'data-tile', 'index': 1}, 'style'),
     Output({'type': 'data-tile', 'index': 2}, 'style'),
     Output({'type': 'data-tile', 'index': 3}, 'style'),
     Output({'type': 'data-tile', 'index': 4}, 'style'),
     Output({'type': 'graph-menu-trigger', 'index': 0}, 'data-'),
     Output({'type': 'graph-menu-trigger', 'index': 1}, 'data-'),
     Output({'type': 'graph-menu-trigger', 'index': 2}, 'data-'),
     Output({'type': 'graph-menu-trigger', 'index': 3}, 'data-'),
     Output('df-constants-storage', 'data'),
     Output({'type': 'confirm-load-data', 'index': 0}, 'style'),
     Output({'type': 'confirm-load-data', 'index': 1}, 'style'),
     Output({'type': 'confirm-load-data', 'index': 2}, 'style'),
     Output({'type': 'confirm-load-data', 'index': 3}, 'style'),
     Output({'type': 'confirm-load-data', 'index': 4}, 'style'),
     Output({'type': 'confirm-data-set-refresh', 'index': 0}, 'style'),
     Output({'type': 'confirm-data-set-refresh', 'index': 1}, 'style'),
     Output({'type': 'confirm-data-set-refresh', 'index': 2}, 'style'),
     Output({'type': 'confirm-data-set-refresh', 'index': 3}, 'style'),
     Output({'type': 'confirm-data-set-refresh', 'index': 4}, 'style'),
     Output({'type': 'data-set', 'index': 0}, 'data-'),
     Output({'type': 'data-set', 'index': 1}, 'data-'),
     Output({'type': 'data-set', 'index': 2}, 'data-'),
     Output({'type': 'data-set', 'index': 3}, 'data-'),
     Output({'type': 'data-set', 'index': 4}, 'data-')],
    [Input('dashboard-reset-trigger', 'data-'),
     Input('tile-closed-trigger', 'data-'),
     Input('select-dashboard-dropdown', 'value'),
     Input({'type': 'tile-link', 'index': ALL}, 'className'),
     Input({'type': 'select-layout-dropdown', 'index': ALL}, 'value'),
     Input({'type': 'tile-data', 'index': ALL}, 'n_clicks'),
     Input({'type': 'data-menu-close', 'index': ALL}, 'n_clicks'),
     Input({'type': 'data-set', 'index': 0}, 'value'),
     Input({'type': 'data-set', 'index': 1}, 'value'),
     Input({'type': 'data-set', 'index': 2}, 'value'),
     Input({'type': 'data-set', 'index': 3}, 'value'),
     Input({'type': 'data-set', 'index': 4}, 'value'),
     Input({'type': 'confirm-load-data', 'index': 0}, 'n_clicks'),
     Input({'type': 'confirm-load-data', 'index': 1}, 'n_clicks'),
     Input({'type': 'confirm-load-data', 'index': 2}, 'n_clicks'),
     Input({'type': 'confirm-load-data', 'index': 3}, 'n_clicks'),
     Input({'type': 'confirm-load-data', 'index': 4}, 'n_clicks'),
     Input({'type': 'confirm-data-set-refresh', 'index': 0}, 'n_clicks'),
     Input({'type': 'confirm-data-set-refresh', 'index': 1}, 'n_clicks'),
     Input({'type': 'confirm-data-set-refresh', 'index': 2}, 'n_clicks'),
     Input({'type': 'confirm-data-set-refresh', 'index': 3}, 'n_clicks'),
     Input({'type': 'confirm-data-set-refresh', 'index': 4}, 'n_clicks')],
    [State({'type': 'data-tile', 'index': ALL}, 'children'),
     State({'type': 'data-tile', 'index': ALL}, 'style'),
     State('df-constants-storage', 'data'),
     State({'type': 'data-set', 'index': ALL}, 'data-')],
    prevent_initial_call=True
)
def _manage_data_sidemenus(dashboard_reset, closed_tile, loaded_dashboard, links_style, selected_layout, data_clicks,
                           data_close_clicks, df_name_0, df_name_1, df_name_2, df_name_3, df_name_4, _confirm_clicks_0,
                           _confirm_clicks_1, _confirm_clicks_2, _confirm_clicks_3, _confirm_clicks_4,
                           _refresh_clicks_0, _refresh_clicks_1, _refresh_clicks_2, _refresh_clicks_3,
                           _refresh_clicks_4, data_states, sidemenu_style_states, df_const, prev_selection):
    """
    :param closed_tile: Detects when a tile has been deleted and encodes the index of the deleted tile
    param links_style: State of all link/unlink icons and detects user clicking a link icon
    :param data_states: State of all data side-menus
    :return: Data side-menus for all 5 side-menus
    """

    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    # if changed id == '.' due to NEW being requested, preserve data menu display.
    if changed_id == '.':
        raise PreventUpdate

    # if 'tile-data' in changed id but n_clicks == 0, meaning a tile was created from blank display, prevent update
    if '{"index":0,"type":"tile-data"}.n_clicks' == changed_id and not data_clicks[0]:
        raise PreventUpdate

    # initialize return variables, data is NONE and sidemenus are hidden by default
    data = [None] * 5
    sidemenu_styles = [DATA_CONTENT_HIDE] * 5
    graph_triggers = [no_update] * 5
    confirm_button = [no_update] * 5
    refresh_button = [no_update] * 5
    store = no_update

    # if 'data-menu-close' or 'select-dashboard-dropdown' requested, close all data menus
    if 'data-menu-close' in changed_id or 'select-dashboard-dropdown' in changed_id:
        pass

    # if 'tile-closed-trigger' requested
    elif 'tile-closed-trigger.data-' == changed_id:
        # trigger graph-menu-trigger
        graph_triggers[int(closed_tile)] = 'tile closed'
        # shuffle data tiles
        data_copy = copy.deepcopy(data_states)
        flag = False
        for i in range(4):
            if i == int(closed_tile):
                flag = True
            if flag and not i == 3:
                data[i] = change_index(data_copy[i + 1], i)
        # if a data menu is open and the only tile was not deleted, select the new open data menu
        if sidemenu_style_states.count(DATA_CONTENT_SHOW) > 0 and len(links_style) != 0:
            active_tile = sidemenu_style_states.index(DATA_CONTENT_SHOW)
            # if the master data menu is active and there are any linked tiles, the master data menu stays open
            if active_tile == 4 and links_style.count('fa fa-link') > 0:
                sidemenu_styles[4] = DATA_CONTENT_SHOW
            # else, the master data menu is not active while any linked tiles exist
            else:
                deleted_tile = int(closed_tile)
                # if the master data menu is active and there are no linked tiles, the linked tile was deleted
                if active_tile == 4:
                    active_tile = deleted_tile
                if deleted_tile == active_tile:
                    if active_tile == len(links_style):
                        new_active_tile = active_tile - 1
                    else:
                        new_active_tile = active_tile
                elif deleted_tile > active_tile:
                    new_active_tile = active_tile
                else:
                    new_active_tile = active_tile - 1
                if links_style[new_active_tile] == 'fa fa-link':
                    sidemenu_styles[4] = DATA_CONTENT_SHOW
                else:
                    sidemenu_styles[new_active_tile] = DATA_CONTENT_SHOW

    # elif 'data-set' in changed id keep shown and show confirmation button
    elif '"type":"data-set"}.value' in changed_id:
        changed_index = int(search(r'\d+', changed_id).group())
        df_names = [df_name_0, df_name_1, df_name_2, df_name_3, df_name_4]
        df_name = df_names[changed_index]
        sidemenu_styles[changed_index] = DATA_CONTENT_SHOW
        if df_name in session:
            confirm_button[changed_index] = DATA_CONTENT_HIDE
            refresh_button[changed_index] = {'padding': '10px 0', 'width': '15px', 'height': '15px',
                                             'position': 'relative',
                                             'margin-right': '10px', 'margin-left': '10px', 'vertical-align': 'top'}
            sidemenu_styles[changed_index] = DATA_CONTENT_SHOW
            # refresh data menu if not returning to last loaded
            if df_name is not prev_selection[changed_index]:
                data[changed_index] = get_data_menu(changed_index, df_name, df_const=df_const)
            # trigger update for all tiles that are linked to the active data menu
            if changed_index == 4:
                for i in range(len(links_style)):
                    if links_style[i] == 'fa fa-link':
                        graph_triggers[i] = df_name
                        confirm_button[i] = DATA_CONTENT_HIDE
                        refresh_button[i] = {'padding': '10px 0', 'width': '15px', 'height': '15px',
                                           'position': 'relative',
                                           'margin-right': '10px', 'margin-left': '10px', 'vertical-align': 'top'}
                        prev_selection[i] = df_name
            else:
                graph_triggers[changed_index] = df_name
                prev_selection[changed_index] = df_name
        else:
            if changed_index == 4:
                for i in range(len(links_style)):
                    if links_style[i] == 'fa fa-link':
                        confirm_button[i] = {'padding': '10px 0', 'width': '15px', 'height': '15px',
                                           'position': 'relative',
                                           'margin-right': '10px', 'margin-left': '10px', 'vertical-align': 'top'}
                        refresh_button[i] = DATA_CONTENT_HIDE
            confirm_button[changed_index] = {'padding': '10px 0', 'width': '15px', 'height': '15px',
                                             'position': 'relative',
                                             'margin-right': '10px', 'margin-left': '10px', 'vertical-align': 'top'}
            refresh_button[changed_index] = DATA_CONTENT_HIDE

    # elif 'data-set' in changed id, reset data tile with new df set as active, keep shown, and trigger graph update
    elif '"type":"confirm-load-data"}.n_clicks' in changed_id or '"type":"confirm-data-set-refresh"}.n_clicks' in changed_id:
        changed_index = int(search(r'\d+', changed_id).group())
        df_names = [df_name_0, df_name_1, df_name_2, df_name_3, df_name_4]
        df_name = df_names[changed_index]
        session[df_name] = dataset_to_df(df_name)
        if df_const is None:
            df_const = {}
        df_const[df_name] = generate_constants(df_name)
        store = df_const
        data[changed_index] = get_data_menu(changed_index, df_name, df_const=df_const)
        sidemenu_styles[changed_index] = DATA_CONTENT_SHOW
        # trigger update for all tiles that are linked to the active data menu
        if changed_index == 4:
            for i in range(len(links_style)):
                if links_style[i] == 'fa fa-link':
                    graph_triggers[i] = df_name
                    prev_selection[i] = df_name
        else:
            graph_triggers[changed_index] = df_name
        prev_selection[changed_index] = df_name
        confirm_button[changed_index] = DATA_CONTENT_HIDE
        refresh_button[changed_index] = {'padding': '10px 0', 'width': '15px', 'height': '15px', 'position': 'relative',
                                         'margin-right': '10px', 'margin-left': '10px', 'vertical-align': 'top'}

    # elif 'RESET' dashboard requested, hide and reset all data tiles
    elif 'dashboard-reset-trigger' in changed_id:
        for i in range(len(data)):
            data[i] = get_data_menu(i, df_const=df_const)

    # else, 'data', 'tile-link', or 'select-layout' requested
    else:
        changed_index = int(search(r'\d+', changed_id).group())
        # if 'tile-link' requested
        if '"type":"tile-link"}.className' in changed_id:
            # if linked --> unlinked: copy master tile data to unique tile data
            if links_style[changed_index] == 'fa fa-unlink':
                master_copy = copy.deepcopy(data_states[4])
                data[changed_index] = change_index(master_copy, changed_index)
        # if tile is slaved to master and a layout was not selected, display master data
        if links_style[changed_index] == 'fa fa-link' and '"type":"select-layout-dropdown"}.value' not in changed_id:
            # if 'data' requested or a data menu is already open, display master data
            if '"type":"tile-data"}.n_clicks' in changed_id or sidemenu_style_states.count(DATA_CONTENT_SHOW) > 0:
                sidemenu_styles[4] = DATA_CONTENT_SHOW
        # if tile is not linked to master or a layout was selected, display unique data side-menu
        else:
            # if 'data' requested or a data menu is already open, display tile data
            if '"type":"tile-data"}.n_clicks' in changed_id or sidemenu_style_states.count(DATA_CONTENT_SHOW) > 0:
                sidemenu_styles[changed_index] = DATA_CONTENT_SHOW

    # determine returns
    for i in range(5):
        # if the data was not changed, do not update
        if data[i] is None:
            data[i] = no_update
        # if the style of a data tile has not changed, do not update
        if sidemenu_styles[i] == sidemenu_style_states[i]:
            # for all tiles besides master data tile do not update if style has not changed
            if i != 4:
                sidemenu_styles[i] = no_update
            # if master data is SHOWN, do not prevent update to force trigger highlight tiles callback
            elif sidemenu_styles[4] != DATA_CONTENT_SHOW:
                sidemenu_styles[4] = no_update

    return (data[0], data[1], data[2], data[3], data[4],
            sidemenu_styles[0], sidemenu_styles[1], sidemenu_styles[2], sidemenu_styles[3], sidemenu_styles[4],
            graph_triggers[0], graph_triggers[1], graph_triggers[2], graph_triggers[3], store,
            confirm_button[0], confirm_button[1], confirm_button[2], confirm_button[3], confirm_button[4],
            refresh_button[0], refresh_button[1], refresh_button[2], refresh_button[3], refresh_button[4],
            prev_selection[0], prev_selection[1], prev_selection[2], prev_selection[3], prev_selection[4])


# highlight tiles slaved to displayed data sidebar
for x in range(4):
    @app.callback(
        Output({'type': 'tile', 'index': x}, 'className'),
        [Input({'type': 'data-tile', 'index': ALL}, 'style')],
        [State({'type': 'data-tile', 'index': x}, 'style'),
         State({'type': 'data-tile', 'index': 4}, 'style'),
         State({'type': 'tile-link', 'index': x}, 'className')]
    )
    def _highlight_child_tiles(sidebar_styles, sidebar_style, master_sidebar_style, link_state):
        """
        :param sidebar_styles: Detects hiding/showing of data side-menus
        :param sidebar_style: State of the style of the data side-menu
        :param master_sidebar_style: State of the style of the parent data side-menu
        :param link_state: State of the link/unlink icon
        :return: Highlights tiles child to the displayed date side-menu
        """

        if sidebar_style == DATA_CONTENT_SHOW or (
                master_sidebar_style == DATA_CONTENT_SHOW and link_state == 'fa fa-link'):
            tile_class = 'tile-highlight'
        else:
            tile_class = 'tile-container'

        return tile_class