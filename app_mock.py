# In[]:
# Import required libraries
import numpy as np
from textwrap import dedent

import plotly.graph_objs as go
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State

import dash_daq as daq

from dash_daq_drivers import keithley_instruments

# Instance of a Keithley2400
iv_generator = keithley_instruments.KT2400('COM3', mock_mode=True)

# # Add meta_tags for mobile responsiveness
# meta_tags = {
#     'name': 'viewport',
#     'content': 'width=device-width'
# }

# Define the app
app = dash.Dash(__name__)
server = app.server

app.config.suppress_callback_exceptions = True


class UsefulVariables:
    """Class to store information useful to callbacks"""

    def __init__(self):
        self.n_clicks = 0
        self.n_clicks_clear_graph = 0
        self.n_refresh = 0
        self.source = 'V'
        self.is_source_being_changed = False
        self.mode = 'single'
        self.sourced_values = []
        self.measured_values = []

    def change_n_clicks(self, nclicks):
        self.n_clicks = nclicks

    def change_n_clicks_clear_graph(self, nclicks):
        self.n_clicks_clear_graph = nclicks

    def reset_n_clicks(self):
        self.n_clicks = 0
        self.n_clicks_clear_graph = 0

    def change_n_refresh(self, nrefresh):
        self.n_refresh = nrefresh

    def reset_interval(self):
        self.n_refresh = 0

    def clear_graph(self):
        self.sourced_values = []
        self.measured_values = []

    def sorted_values(self):
        """ Sort the data so the are ascending according to the source """
        data_array = np.vstack(
            [
                local_vars.sourced_values,
                local_vars.measured_values
            ]
        )
        data_array = data_array[:, data_array[0, :].argsort()]

        return data_array


local_vars = UsefulVariables()


def get_source_labels(source='Voltage'):
    """labels for source/measure elements"""
    if source == 'Voltage':
        # we source voltage and measure current
        source_label = 'Voltage'
        measure_label = 'Current'
    elif source == 'Current':
        # we source current and measure voltage
        source_label = 'Current'
        measure_label = 'Voltage'

    return source_label, measure_label


def get_source_units(source='Voltage'):
    """units for source/measure elements"""
    if source == 'Voltage':
        # we source voltage and measure current
        source_unit = 'V'
        measure_unit = 'A'
    elif source == 'Current':
        # we source current and measure voltage
        source_unit = 'A'
        measure_unit = 'V'

    return source_unit, measure_unit


# Font and background colors associated with each themes
bkg_color = {'dark': '#23262e', 'light': '#f6f6f7'}
grid_color = {'dark': '#53555B', 'light': '#969696'}
text_color = {'dark': '#95969A', 'light': '#595959'}
card_color = {'dark': '#2D3038', 'light': '#FFFFFF'}
accent_color = {'dark': '#FFD15F', 'light': '#ff9827'}

single_div_toggle_style = {
    'width': '80%',
    'display': 'flex',
    'flexDirection': 'row',
    'margin': 'auto',
    'alignItems': 'center',
    'justifyContent': 'space-between'
}

sweep_div_toggle_style = {
    'display': 'flex',
    'flexDirection': 'column',
    'alignItems': 'center',
    'justifyContent': 'space-around'
}

label_style = {
    'display': 'flex',
    'flex-orientation': 'row',
    'justify-content': 'space-around',
    'font-size': '14px'
}


# Create controls using a function
def generate_main_layout(
        theme='light',
        src_type='Voltage',
        mode_val='single',
        fig=None,
):
    """generate the layout of the app"""

    source_label, measure_label = get_source_labels(src_type)
    source_unit, measure_unit = get_source_units(src_type)

    # As the trigger-measure btn will have its n_clicks reset by the reloading
    # of the layout we need to reset this one as well
    local_vars.reset_n_clicks()

    # Doesn't clear the data of the graph
    if fig is None:
        data = []
    else:
        data = fig['data']

    html_layout = [
        html.Div(
            className='row',
            children=[
                html.Div(
                    id='figure-card',
                    className='six columns',
                    style={'backgroundColor': card_color[theme]},
                    children=
                    [
                        html.P("IV Curve"),
                        dcc.Graph(
                            id='IV_graph',
                            style={'marginBottom': '10px'},
                            figure={
                                'data': data,
                                'layout': dict(
                                    paper_bgcolor=card_color[theme],
                                    plot_bgcolor=card_color[theme],
                                    margin={'l': 80, 'b': 80, 't': 80, 'r': 80, 'pad': 0},
                                    font=dict(
                                        color=text_color[theme],
                                        size=12,
                                    ),
                                    xaxis={
                                        'color': grid_color[theme],
                                        'gridcolor': grid_color[theme]
                                    },
                                    yaxis={
                                        'color': grid_color[theme],
                                        'gridcolor': grid_color[theme]
                                    }
                                )
                            }
                        )
                    ]
                ),
                html.Div(
                    id='control-container',
                    className='five columns',
                    children=[
                        html.Div(
                            # controls and options for the IV tracer
                            id="up-control-card",
                            style={'backgroundColor': card_color[theme],
                                   'color': text_color[theme]},
                            children=[
                                html.Div(
                                    className='IV-source-options',
                                    children=[
                                        html.Label("Sourcing", title='Choose whether you want to source voltage '
                                                                     'and measure current, or source current and measure voltage'),

                                        daq.ToggleSwitch(
                                            id='source-choice-toggle',
                                            label=['Voltage', 'Current'],
                                            style={'width': '200px', 'margin': 'auto'},
                                            value=False
                                        )

                                        # dcc.RadioItems(
                                        #     id='source-choice',
                                        #     options=[
                                        #         {'label': 'Voltage', 'value': 'V'},
                                        #         {'label': 'Current', 'value': 'I'}
                                        #     ],
                                        #     value=src_type,
                                        #     labelStyle=label_style
                                        # ),
                                    ],
                                ),
                                html.Div(
                                    className='measure-options',
                                    children=[
                                        html.Label('Measure mode', title='Choose if you want to do single measurement'
                                                                         ' or to start a sweep mode'),
                                        dcc.RadioItems(
                                            id='mode-choice',
                                            options=[
                                                {'label': 'Single measure', 'value': 'single'},
                                                {'label': 'Sweep', 'value': 'sweep'}
                                            ],
                                            value=mode_val,
                                            labelStyle=label_style
                                        )
                                    ]
                                ),
                                daq.StopButton(
                                    id='clear-graph_btn',
                                    buttonText='Clear Graph',
                                    className='daq-button',
                                    size=120
                                ),
                                daq.Indicator(
                                    id='clear-graph_ind',
                                    value=False,
                                    style={'display': 'none'}
                                )
                            ]
                        ),

                        html.Div(
                            id='mid-control-card',
                            style={'backgroundColor': card_color[theme],
                                   'color': text_color[theme],
                                   'marginTop': '10px'},
                            children=[
                                # Sourcing controls
                                html.Div(
                                    id='source-div',
                                    children=[
                                        # To perform single measures adjusting the source with a knob
                                        html.Div(
                                            id='single_div',
                                            style=single_div_toggle_style,
                                            children=[
                                                daq.Knob(
                                                    id='source-knob',
                                                    size=100,
                                                    value=0.00,
                                                    min=0,
                                                    max=10,
                                                    color=accent_color[theme],
                                                    label='%s (%s)' % (
                                                        source_label,
                                                        source_unit
                                                    )
                                                ),
                                                daq.LEDDisplay(
                                                    id="source-knob-display",
                                                    label='Knob readout',
                                                    value=0.00,
                                                    color=accent_color[theme]
                                                )
                                            ]
                                        ),
                                        # To perform automatic sweeps of the source
                                        html.Div(
                                            id='sweep_div',
                                            style=sweep_div_toggle_style,
                                            children=[
                                                html.Div(
                                                    className='sweep-div-row',
                                                    children=[
                                                        html.Div(
                                                            className='sweep-div-row',
                                                            style={'width': '98%'},
                                                            children=[
                                                                html.Div(
                                                                    id='sweep-title',
                                                                    children=html.P(
                                                                        "%s sweep" % source_label
                                                                    )),
                                                                html.Div(
                                                                    [
                                                                        daq.Indicator(
                                                                            id='sweep-status',
                                                                            label='Sweep active',
                                                                            color=accent_color[theme],
                                                                            value=False
                                                                        )
                                                                    ],
                                                                    title='Indicates if the sweep is running'
                                                                )
                                                            ]
                                                        )
                                                    ]
                                                ),
                                                html.Div(
                                                    className='sweep-div-row',
                                                    children=[
                                                        html.Div(
                                                            className='sweep-div-row-inner',
                                                            children=
                                                            [
                                                                'Start',
                                                                daq.PrecisionInput(
                                                                    id='sweep-start',
                                                                    precision=4,
                                                                    label=' %s' % source_unit,
                                                                    labelPosition='right',
                                                                    value=0,
                                                                ),
                                                            ],
                                                            title='The lowest value of the sweep'
                                                        ),
                                                        html.Div(
                                                            className='sweep-div-row-inner',
                                                            children=[
                                                                'Stop',
                                                                daq.PrecisionInput(
                                                                    id='sweep-stop',
                                                                    precision=4,
                                                                    label=' %s' % source_unit,
                                                                    labelPosition='right',
                                                                    value=10
                                                                )
                                                            ],
                                                            title='The highest value of the sweep'
                                                        )]),
                                                html.Div(
                                                    className='sweep-div-row',
                                                    children=[
                                                        html.Div(
                                                            className='sweep-div-row-inner',
                                                            children=[
                                                                'Step',
                                                                daq.PrecisionInput(
                                                                    id='sweep-step',
                                                                    precision=4,
                                                                    label=' %s' % source_unit,
                                                                    labelPosition='right',
                                                                    value=0.2
                                                                )
                                                            ],
                                                            title='The increment of the sweep'
                                                        ),
                                                        html.Div(
                                                            className='sweep-div-row-inner',
                                                            children=[
                                                                'Time of a step',
                                                                daq.NumericInput(
                                                                    id='sweep-dt',
                                                                    value=0.2,
                                                                    min=0.01,
                                                                    style={'color': text_color[theme]}
                                                                ),
                                                                's'
                                                            ],
                                                            title='The time spent on each increment'
                                                        )
                                                    ]
                                                )

                                            ]
                                        )]),

                                # Measure button and indicator
                                html.Div(
                                    id='trigger-div',
                                    children=[
                                        daq.StopButton(
                                            id='trigger-measure_btn',
                                            # buttonText=label_btn,
                                            buttonText='Single measure',
                                            className='daq-button',
                                            size=120,
                                        ),
                                        daq.Indicator(
                                            id='measure-triggered',
                                            color=accent_color[theme],
                                            value=False,
                                            label='Measure active'
                                        ),
                                    ]
                                )]),

                        html.Div(
                            id="bottom-card",
                            style={'backgroundColor': card_color[theme],
                                   'color': text_color[theme],
                                   'marginTop': '10px'},
                            children=[
                                # Display the sourced and measured values
                                html.Div(
                                    id='measure-div',
                                    children=[
                                        daq.LEDDisplay(
                                            id="source-display",
                                            label='Applied %s (%s)' % (
                                                source_label,
                                                source_unit
                                            ),
                                            value=0.0000,
                                            color=accent_color[theme]
                                        ),
                                        daq.LEDDisplay(
                                            id="measure-display",
                                            label='Measured %s (%s)' % (
                                                measure_label,
                                                measure_unit
                                            ),
                                            value=0.0000,
                                            color=accent_color[theme]
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    ]

    if theme == 'dark':
        return daq.DarkThemeProvider(children=html_layout)
    if theme == 'light':
        return html_layout


def generate_modal():
    return html.Div(
        id='markdown',
        className="modal",
        style={'display': 'none'},
        children=(
            html.Div(
                id="markdown-container",
                className="markdown-container",
                style={'color': text_color['light'], 'backgroundColor': card_color['light']},
                children=[
                    html.Div(
                        className='close-container',
                        children=html.Button(
                            "Close",
                            id="markdown_close",
                            n_clicks=0,
                            className="closeButton",
                            style={'color': text_color['dark']}
                        )
                    ),
                    html.Div(
                        className='markdown-text',
                        children=dcc.Markdown(
                            children=dedent('''
                            **What is this mock app about?**
    
                            This is an app to show the graphic elements of Dash DAQ used to create an
                            interface for an IV curve tracer using a Keithley 2400 SourceMeter. This mock
                            demo does not actually connect to a physical instrument the values displayed
                            are generated from an IV curve model for demonstration purposes.
    
                            **How to use the mock app**
    
                            First choose if you want to source (apply) current or voltage, using the radio
                            item located on the right of **Sourcing** label. Then choose if you want to operate
                            in a **single measurement mode** or in a **sweep mode**.
    
                            ***Single measurement mode***
    
                            Adjust the value of the source with the knob at the bottom of the graph area
                            and click on the `SINGLE MEASURE` button, the measured value will be displayed.
                            Repetition of this procedure for different source values will reveal the full
                            IV curve.
    
                            ***Sweep mode***
    
                            Set the sweep parameters `start`, `stop` and `step` as well as the time
                            spent on each step, then click on the button `START SWEEP`, the result of the
                            sweep will be displayed on the graph.
    
                            The data is never erased unless the button `CLEAR GRAPH` is pressed, or if the
                            source type is changed.
                            
                            ***Dark/light theme***
                            
                            Click on theme toggle on top of the page to view dark/light layout.
    
                            You can purchase the Dash DAQ components at [
                            dashdaq.io](https://www.dashdaq.io/)
                        ''')
                        )
                    )
                ]
            )
        )
    )


app.layout = html.Div(
    id='main-page',
    className='container',
    style={'backgroundColor': bkg_color['light'],
           'height': '100vh'
           },
    children=[
        dcc.Location(id='url', refresh=False),
        dcc.Interval(id='refresher', interval=1000000),
        html.Div(
            id='header',
            className='banner',
            style={'color': text_color['light']},
            children=[
                html.H6('Dash DAQ: IV Curve Tracer (mock app)'),
                daq.ToggleSwitch(
                    id='toggleTheme',
                    label={'label': 'Light/Dark theme', 'style': {'color': text_color['light']}},
                    size=35
                ),
                html.Img(
                    src='https://s3-us-west-1.amazonaws.com/plotly'
                        '-tutorials/excel/dash-daq/dash-daq-logo'
                        '-by-plotly-stripe.png',
                    className='logo')
            ]
        ),
        html.Div(
            id='intro-banner',
            className='intro-banner',
            style={'color': text_color['light'],
                   'backgroundColor': accent_color['light']},
            children=html.Div(
                className='intro-banner-content',
                children=[
                    html.P(children="This app uses graphic elements of Dash DAQ to create an"
                                    " interface for an IV curve tracer using a Keithley 2400 SourceMeter. Mock"
                                    " demo does not actually connect to a physical instrument, the values displayed"
                                    " are generated from an IV curve model for demonstration purposes.",
                           className='intro-banner-text'),
                    html.Button(
                        id="learn-more-button",
                        children="Learn More",
                        n_clicks=0,
                        style={
                            'borderColor': bkg_color['light'],
                            'color': text_color['light'],
                            'backgroundColor': accent_color['light']
                        }
                    )
                ]
            )
        ),
        html.Div(
            id='page-content',
            children=generate_main_layout(),
            style={'backgroundColor': bkg_color['light'],
                   'display': 'flex',
                   'padding': '2%'}
        ),
        generate_modal()
    ]
)


# In[]:
# Create callbacks
# ======= Dark/light themes callbacks =======
@app.callback(Output('page-content', 'children'),
              [
                  Input('toggleTheme', 'value')
              ],
              [
                  State('source-choice-toggle', 'value'),
                  State('mode-choice', 'value'),
                  State('IV_graph', 'figure'),
                  State('source-display', 'value'),  # Keep measure LED display while changing themes
                  State('measure-display', 'value')
              ]
              )
def page_layout(value, src_value, mode_val, fig, meas_src, meas_display):
    """update the theme of the daq components"""
    if src_value:
        src_type = 'Current'
    else:
        src_type = 'Voltage'

    if value:
        return generate_main_layout('dark', src_type, mode_val, fig)
    else:
        return generate_main_layout('light', src_type, mode_val, fig)


@app.callback(
    Output('page-content', 'style'),
    [Input('toggleTheme', 'value')],
    [State('page-content', 'style')]
)
def page_style(value, style_dict):
    """update the theme of the app"""
    if value:
        theme = 'dark'
    else:
        theme = 'light'

    style_dict['color'] = text_color[theme]
    style_dict['backgroundColor'] = bkg_color[theme]
    return style_dict


@app.callback(
    Output('header', 'style'),
    [Input('toggleTheme', 'value')],
    [State('header', 'style')]
)
def header_style(value, style_dict):
    """update the theme of header"""
    if value:
        theme = 'dark'
    else:
        theme = 'light'

    style_dict['color'] = text_color[theme]
    style_dict['backgroundColor'] = bkg_color[theme]
    return style_dict


@app.callback(
    Output('intro-banner', 'style'),
    [Input('toggleTheme', 'value')],
    [State('intro-banner', 'style')]
)
def banner_style(value, style_dict):
    """update the theme of banner"""
    if value:
        theme = 'dark'
    else:
        theme = 'light'

    style_dict['color'] = text_color[theme]
    return style_dict


@app.callback(
    Output('learn-more-button', 'style'),
    [Input('toggleTheme', 'value')],
    [State('learn-more-button', 'style')]
)
def banner_style(value, style_dict):
    """update the theme of button"""
    if value:
        theme = 'dark'
    else:
        theme = 'light'

    style_dict['color'] = text_color[theme]
    return style_dict


@app.callback(
    Output('markdown-container', 'style'),
    [Input('toggleTheme', 'value')],
    [State('markdown-container', 'style')]
)
def markdown_style(value, style_dict):
    """update the theme of markdown"""
    if value:
        theme = 'dark'
    else:
        theme = 'light'

    style_dict['color'] = text_color[theme]
    style_dict['backgroundColor'] = card_color[theme]
    return style_dict


@app.callback(
    Output('main-page', 'style'),
    [Input('toggleTheme', 'value')],
    [State('main-page', 'style')]
)
def markdown_style(value, style_dict):
    """update the theme of entire page"""
    if value:
        theme = 'dark'
    else:
        theme = 'light'

    style_dict['color'] = text_color[theme]
    style_dict['backgroundColor'] = bkg_color[theme]
    return style_dict


# ======= Callbacks for modal popup =======
@app.callback(Output("markdown", "style"),
              [Input("learn-more-button", "n_clicks"), Input("markdown_close", "n_clicks")])
def update_click_output(button_click, close_click):
    if button_click > close_click:
        return {"display": "block"}
    else:
        return {"display": "none"}


# ======= Callbacks for changing labels =======
# ======= Label for single measures =======
@app.callback(
    Output('source-knob', 'label'),
    [
        Input('source-choice-toggle', 'value'),
        Input('mode-choice', 'value')
    ],
)
def source_knob_label(src_value, _):
    """update label upon modification of Radio Items"""
    if src_value:
        src_type = 'Current'
    else:
        src_type = 'Voltage'
    source_label, measure_label = get_source_labels(src_type)
    return source_label


@app.callback(
    Output('source-knob-display', 'label'),
    [
        Input('source-choice-toggle', 'value'),
        Input('mode-choice', 'value')
    ],
)
def source_knob_display_label(src_value, _):
    """update label upon modification of Radio Items"""
    if src_value:
        src_type = 'Current'
    else:
        src_type = 'Voltage'
    source_label, measure_label = get_source_labels(src_type)
    source_unit, measure_unit = get_source_units(src_type)
    return 'Value : %s (%s)' % (source_label, source_unit)


# ======= Label for sweep mode =======
@app.callback(
    Output('sweep-start', 'label'),
    [
        Input('source-choice-toggle', 'value'),
        Input('mode-choice', 'value')
    ],
)
def sweep_start_label(src_value, _):
    """update label upon modification of Radio Items"""
    if src_value:
        src_type = 'Current'
    else:
        src_type = 'Voltage'
    source_unit, measure_unit = get_source_units(src_type)
    return '(%s)' % source_unit


@app.callback(
    Output('sweep-stop', 'label'),
    [
        Input('source-choice-toggle', 'value'),
        Input('mode-choice', 'value')
    ],
)
def sweep_stop_label(src_value, _):
    """update label upon modification of Radio Items"""
    if src_value:
        src_type = 'Current'
    else:
        src_type = 'Voltage'
    source_unit, measure_unit = get_source_units(src_type)
    return '(%s)' % source_unit


@app.callback(
    Output('sweep-step', 'label'),
    [
        Input('source-choice-toggle', 'value'),
        Input('mode-choice', 'value')
    ],
)
def sweep_step_label(src_value, _):
    """update label upon modification of Radio Items"""
    if src_value:
        src_type = 'Current'
    else:
        src_type = 'Voltage'
    source_unit, measure_unit = get_source_units(src_type)
    return '(%s)' % source_unit


@app.callback(
    Output('sweep-title', 'children'),
    [
        Input('source-choice-toggle', 'value'),
        Input('mode-choice', 'value')
    ],
)
def sweep_title_label(src_value, _):
    """update label upon modification of Radio Items"""
    if src_value:
        src_type = 'Current'
    else:
        src_type = 'Voltage'
    source_label, measure_label = get_source_labels(src_type)
    return html.P("%s sweep " % source_label)


# ======= Label for displays =======
@app.callback(
    Output('source-display', 'label'),
    [
        Input('source-choice-toggle', 'value'),
        Input('mode-choice', 'value')
    ],
)
def source_display_label(src_value, _):
    """update label upon modification of Radio Items"""
    if src_value:
        src_type = 'Current'
    else:
        src_type = 'Voltage'
    source_label, measure_label = get_source_labels(src_type)
    source_unit, measure_unit = get_source_units(src_type)
    return 'Applied %s (%s)' % (source_label, source_unit)


@app.callback(
    Output('measure-display', 'label'),
    [
        Input('source-choice-toggle', 'value'),
        Input('mode-choice', 'value')
    ],
)
def measure_display_label(src_value, _):
    """update label upon modification of Radio Items"""
    if src_value:
        src_type = 'Current'
    else:
        src_type = 'Voltage'
    source_label, measure_label = get_source_labels(src_type)
    source_unit, measure_unit = get_source_units(src_type)
    return 'Measured %s (%s)' % (measure_label, measure_unit)


@app.callback(
    Output('trigger-measure_btn', 'buttonText'),
    [
        Input('mode-choice', 'value')
    ],
)
def trigger_measure_label(mode_val):
    """update the measure button upon choosing single or sweep"""
    if mode_val == 'single':
        return 'Single measure'
    else:
        return 'Start sweep'


# ======= Callbacks to change elements in the layout =======
@app.callback(
    Output('single_div', 'style'),
    [
        Input('mode-choice', 'value')
    ],
)
def single_div_toggle(mode_val):
    """toggle the layout for single measure"""
    if mode_val == 'single':
        return single_div_toggle_style
    else:
        return {'display': 'none'}


@app.callback(
    Output('sweep_div', 'style'),
    [
        Input('mode-choice', 'value')
    ],
)
def sweep_div_toggle(mode_val):
    """toggle the layout for sweep"""
    if mode_val == 'single':
        return {'display': 'none'}
    else:
        return sweep_div_toggle_style


# ======= Applied/measured values display =======
@app.callback(
    Output('source-knob', 'value'),
    [
        Input('source-choice', 'value')
    ],
    [
        State('source-knob', 'value'),
    ]
)
def source_change(src_type, src_val):
    """modification upon source-change
    change the source type in local_vars
    reset the knob to zero
    reset the measured values on the graph
    """
    if src_type == local_vars.source:
        local_vars.is_source_being_changed = False
        return src_val
    else:
        local_vars.is_source_being_changed = True
        local_vars.source = src_type
        return 0.00


# ======= Interval callbacks =======
@app.callback(
    Output('refresher', 'interval'),
    [
        Input('sweep-status', 'value')
    ],
    [
        State('mode-choice', 'value'),
        State('sweep-dt', 'value')
    ]
)
def interval_toggle(swp_on, mode_val, dt):
    """change the interval to high frequency for sweep"""
    if dt <= 0:
        # Precaution against the user
        dt = 0.5
    if mode_val == 'single':
        return 1000000
    else:
        if swp_on:
            return dt * 1000
        else:
            return 1000000


@app.callback(
    Output('refresher', 'n_intervals'),
    [
        Input('trigger-measure_btn', 'n_clicks'),
        Input('mode-choice', 'value')
    ],
    [
        State('sweep-status', 'value'),
        State('refresher', 'n_intervals')
    ]
)
def reset_interval(_, mode_val, swp_on, n_interval):
    """reset the n_interval of the dcc.Interval once a sweep is done"""
    if mode_val == 'single':
        local_vars.reset_interval()
        return 0
    else:
        if swp_on:
            return n_interval
        else:
            local_vars.reset_interval()
            return 0


@app.callback(
    Output('sweep-status', 'value'),
    [
        Input('trigger-measure_btn', 'n_clicks'),
        Input('source-display', 'value')
    ],
    [
        State('measure-triggered', 'value'),
        State('sweep-status', 'value'),
        State('sweep-stop', 'value'),
        State('sweep-step', 'value'),
        State('mode-choice', 'value')
    ]
)
def sweep_activation_toggle(
        _,
        sourced_val,
        meas_triggered,
        swp_on,
        swp_stop,
        swp_step,
        mode_val
):
    """decide whether to turn on or off the sweep
    when single mode is selected, it is off by default
    when sweep mode is selected, it enables the sweep if is wasn't on
    otherwise it stops the sweep once the sourced value gets higher or equal
    than the sweep limit minus the sweep step
    """
    if mode_val == 'single':
        return False
    else:
        if swp_on:
            # The condition of continuation is to source lower than the sweep
            # limit minus one sweep step
            answer = float(sourced_val) <= float(swp_stop) - float(swp_step)
            return answer
        else:
            if not meas_triggered:
                # The 'trigger-measure_btn' wasn't pressed yet
                return False
            else:
                # Initiate a sweep
                return True


# ======= Measurements callbacks =======
@app.callback(
    Output('source-knob-display', 'value'),
    [
        Input('source-knob', 'value')
    ]
)
def set_source_knob_display(knob_val):
    """"set the value of the knob on a LED display"""
    return knob_val


@app.callback(
    Output('measure-triggered', 'value'),
    [
        Input('trigger-measure_btn', 'n_clicks'),
        Input('mode-choice', 'value')
    ]
)
def update_trigger_measure(nclick, _):
    """ Controls if a measure can be made or not
    The indicator 'measure-triggered' can be set to True only by a click
    on the 'trigger-measure_btn' button or by the 'refresher' interval
    """

    if nclick is None:
        nclick = 0

    if int(nclick) != local_vars.n_clicks:
        # It was triggered by a click on the trigger-measure_btn button
        local_vars.change_n_clicks(int(nclick))
        return True
    else:
        # It was triggered by a change of the mode
        return False


@app.callback(
    Output('source-display', 'value'),
    [
        Input('refresher', 'n_intervals'),
        Input('measure-triggered', 'value'),
    ],
    [
        State('source-knob', 'value'),
        State('source-display', 'value'),
        State('sweep-start', 'value'),
        State('sweep-stop', 'value'),
        State('sweep-step', 'value'),
        State('mode-choice', 'value'),
        State('sweep-status', 'value')
    ]
)
def set_source_display(
        n_interval,
        meas_triggered,
        knob_val,
        old_source_display_val,
        swp_start,
        swp_stop,
        swp_step,
        mode_val,
        swp_on
):
    """"set the source value to the instrument"""

    # Default answer
    answer = old_source_display_val

    if mode_val == 'single':
        answer = knob_val
    else:
        if meas_triggered:
            if swp_on:
                answer = float(swp_start) \
                         + (int(n_interval) - 1) * float(swp_step)
                if answer > float(swp_stop):
                    answer = old_source_display_val

    return float("%.4f" % answer)


@app.callback(
    Output('measure-display', 'value'),
    [
        Input('source-display', 'value')
    ],
    [
        State('measure-triggered', 'value'),
        State('measure-display', 'value'),
        State('source-choice', 'value'),
        State('mode-choice', 'value'),
        State('sweep-status', 'value')
    ]
)
def update_measure_display(
        src_val,
        meas_triggered,
        meas_old_val,
        src_type,
        mode_val,
        swp_on
):
    """"read the measured value from the instrument
    check if a measure should be made
    initiate a measure of the KT2400
    read the measure value and return it
    by default it simply return the value previously available
    """
    source_value = float(src_val)
    measured_value = meas_old_val

    if mode_val == 'single':
        if meas_triggered:
            # Save the sourced value
            local_vars.sourced_values.append(source_value)
            # Initiate a measurement
            measured_value = iv_generator.source_and_measure(src_type, src_val)
            # Save the measured value
            local_vars.measured_values.append(measured_value)
    else:
        if meas_triggered and swp_on:
            # Save the sourced value
            local_vars.sourced_values.append(source_value)
            # Initiate a measurement
            measured_value = iv_generator.source_and_measure(src_type, src_val)
            # Save the measured value
            local_vars.measured_values.append(measured_value)

    return measured_value


# ======= Graph related callbacks =======
@app.callback(
    Output('clear-graph_ind', 'value'),
    [
        Input('source-knob', 'value'),
        Input('clear-graph_btn', 'n_clicks'),
        Input('measure-triggered', 'value')
    ]
)
def clear_graph_click(src_val, nclick, meas_triggered):
    """clear the data on the graph
    Uses the callback of the knob value triggered by source-choice change
    or the click on the clear-graph_btn
    everytime a measure is initiated, this value is reset to False, this
    is why we need the input of measure_triggered
    """
    if nclick is None:
        nclick = 0

    if local_vars.is_source_being_changed:
        # The callback was triggered by a source change
        local_vars.is_source_being_changed = False
        local_vars.clear_graph()
        return True
    else:
        if int(nclick) != local_vars.n_clicks_clear_graph:
            # It was triggered by a click on the clear-graph_btn button
            local_vars.change_n_clicks_clear_graph(int(nclick))
            # Reset the data
            local_vars.clear_graph()
            return True
        else:
            return False


@app.callback(
    Output('IV_graph', 'figure'),
    [
        Input('measure-display', 'value'),
        Input('clear-graph_ind', 'value')
    ],
    [
        State('toggleTheme', 'value'),
        State('measure-triggered', 'value'),
        State('IV_graph', 'figure'),
        State('source-choice', 'value'),
        State('mode-choice', 'value'),
        State('sweep-status', 'value')
    ]
)
def update_graph(
        measured_val,
        clear_graph,  # Had to do this because of the lack of multiple Outputs
        theme,
        meas_triggered,
        graph_data,
        src_type,
        mode_val,
        swp_on
):
    """"update the IV graph"""
    if theme:
        theme = 'dark'
    else:
        theme = 'light'

    # Labels for sourced and measured quantities
    source_label, measure_label = get_source_labels(src_type)
    source_unit, measure_unit = get_source_units(src_type)

    if mode_val == 'single':
        if meas_triggered:
            # The change to the graph was triggered by a measure

            # Sort the stored data so the are ascending in x
            data_array = local_vars.sorted_values()

            xdata = data_array[0, :]
            ydata = data_array[1, :]

            data_for_graph = [
                go.Scatter(
                    x=xdata,
                    y=ydata,
                    mode='lines+markers',
                    name='IV curve',
                    line={
                        'color': accent_color[theme],
                        'width': 2
                    }
                )
            ]

            return {
                'data': data_for_graph,
                'layout': dict(
                    xaxis={
                        'title': 'Applied %s (%s)' % (
                            source_label, source_unit
                        ),
                        'color': text_color[theme],
                        'gridcolor': grid_color[theme]
                    },
                    yaxis={
                        'title': 'Measured %s (%s)' % (
                            measure_label,
                            measure_unit
                        ),
                        'gridcolor': grid_color[theme]
                    },
                    font=dict(
                        color=text_color[theme],
                        size=12,
                    ),
                    margin={'l': 80, 'b': 80, 't': 80, 'r': 80, 'pad': 0},
                    plot_bgcolor=card_color[theme],
                    paper_bgcolor=card_color[theme]
                )
            }
        else:
            if clear_graph:
                graph_data['data'] = local_vars.sorted_values()
            return graph_data
    else:
        if swp_on:
            # The change to the graph was triggered by a measure

            # Sort the stored data so the are ascending in x
            data_array = local_vars.sorted_values()

            xdata = data_array[0, :]
            ydata = data_array[1, :]

            data_for_graph = [
                go.Scatter(
                    x=xdata,
                    y=ydata,
                    mode='lines+markers',
                    name='IV curve',
                    line={
                        'color': accent_color[theme],
                        'width': 2
                    }
                )
            ]

            return {
                'data': data_for_graph,
                'layout': dict(
                    xaxis={
                        'title': 'Applied %s (%s)' % (
                            source_label, source_unit
                        ),
                        'color': text_color[theme],
                        'gridcolor': grid_color[theme]
                    },
                    yaxis={
                        'title': 'Measured %s (%s)' % (
                            measure_label,
                            measure_unit
                        ),
                        'gridcolor': grid_color[theme]
                    },
                    font=dict(
                        color=text_color[theme],
                        size=12,
                    ),
                    margin={'l': 80, 'b': 80, 't': 80, 'r': 80, 'pad': 0},
                    plot_bgcolor=card_color[theme],
                    paper_bgcolor=card_color[theme]
                )
            }
        else:
            if clear_graph:
                graph_data['data'] = local_vars.sorted_values()
            return graph_data


if __name__ == '__main__':
    app.run_server(debug=True, dev_tools_hot_reload=False, host='0.0.0.0')
