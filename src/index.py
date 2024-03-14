import json
import base64
import io, uuid
from os.path import basename
from datetime import datetime, timedelta

from flask_caching import Cache
import uuid
import flask
from flask_session import Session
import secrets

import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html, dash_table, callback_context, ctx
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

import pandas as pd
import xlsxwriter
import dash_cytoscape as cyto
cyto.load_extra_layouts()

from utils.common_functions import *
from utils.statistics_fisher import *
from utils.statistics_hypergeom import *
from utils.convert_batch import convert_table
from utils.graph_functions import get_elements, get_abbr
from utils.upset_chart import plotly_upset_plot_pivot, plotly_upset_figure
from utils.reverse_table_upset import table_for_upset
from pages.layout import header, footer, table_header, table_body
from pages.manual import manual_layout
from utils.phylo_tree import *
from utils.reporter import *
from utils.cleaning import clear_old_assets_and_cache

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, "https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"], title='LORA')
server = app.server
app.config.suppress_callback_exceptions = True

server.config.update(
    SESSION_COOKIE_SECURE=True,  # Controls if the cookie should be set with the secure flag
    SESSION_COOKIE_HTTPONLY=True,  # Controls if the cookie should be set with the httponly flag
    SESSION_COOKIE_SAMESITE='Lax',  # Restrict how cookies are sent with requests from external sites. Can be set to 'Lax' (recommended) or 'Strict'.

    SECRET_KEY=secrets.token_hex(32),
    SESSION_TYPE='filesystem',
    PERMANENT_SESSION_LIFETIME=timedelta(seconds=600),  # Session expire after 10 mins

    SESSION_FILE_THRESHOLD=100,  # The maximum number of items the session stores before it starts deleting some.
    SESSION_FILE_MODE=0o600,  # The file mode wanted for the session files
)

Session(server)

config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': './cache-dir',
    'CACHE_THRESHOLD': 100,
    'CACHE_DEFAULT_TIMEOUT': 600
}


cache = Cache(app.server, config=config)

@server.before_request
def set_session_id():
    if 'session_id' not in flask.session:
        session_id = str(uuid.uuid4())
        flask.session['session_id'] = session_id


app.index_string = '''<!DOCTYPE html>

<html lang='en'>
    <head>
    <meta name="author" content="Michaela Vondrackova">
  	<meta name="description" content="Metabolomics, lipidomics, Goslin, enrichment, lipid ontology, over-representation, standardization, LIPID MAPS" />
	<meta name="keywords" content="lipidomics, lipid structure, nomenclature, Goslin, normalized lipid name, lipid identification, UpSet plot, lipid network, pathway">

    <!-- Google tag (gtag.js) -->
    <script async="" src="https://www.googletagmanager.com/gtag/js?id=G-LQQRFEVR5E"></script>
    <script>
	  window.dataLayer = window.dataLayer || [];
	  function gtag(){dataLayer.push(arguments);}
	  gtag('js', new Date());
	
	  gtag('config', 'G-LQQRFEVR5E');
    </script>

    {%metas%}
    <title>{%title%}</title>

    {%favicon%}
    <link rel="apple-touch-icon" sizes="180x180" href="assets/favicons/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="assets/favicons/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="assets/favicons/favicon-16x16.png">
    <link rel="manifest" href="assets/favicons/site.webmanifest">
    <link rel="mask-icon" href="assets/favicons/safari-pinned-tab.svg" color="#5bbad5">
    <meta name="msapplication-TileColor" content="#da532c">
    <meta name="theme-color" content="#ffffff">

    {%css%}
    </head>

    <body>
    {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

app_layout = html.Div([

    header,

    html.Div([

        dcc.Tabs(id="tabs-styled-with-props", value='tab-1', children=[
            ### Upload data
            dcc.Tab(label='Upload Datasets', value='tab-1', className='custom-tab-1', selected_className='custom-tab-1--selected', id='tab-1',children=[
                html.Br(),
                html.H6('Select Grammar:'),
                html.Div([
                    dcc.Dropdown([
                        {'label':'Universal lipid parser', 'value':'LIPID'},
                        {'label':'Goslin parser', 'value':'GOSLIN'},
                        {'label':'Shorthand parser', 'value':'SHORTHAND2020'}, 
                        {'label':'LipidMaps parser', 'value':'LIPIDMAPS'},
                        {'label':'SwissLipids parser', 'value':'SWISSLIPIDS'},
                        {'label':'HMDB parser', 'value':'HMDB'}], 'LIPID', id='parser-dropdown',),
                ], style={'width':'25%'}),
                dbc.Tooltip('All parsers use jgoslin-cli.'
                            ' Universal lipid parser uses multiple grammars to parse lipid names, to use specific grammar use the remaining parsers.', target='parser-dropdown'),
                
                dbc.Row(children=[
                    ### upload query file
                    dbc.Col(children=[
                        html.Br(),
                        html.H6('Query'),
                        dcc.Upload(
                                id='upload-query-data',
                                children=html.Div([
                                    'Drag and Drop or ',
                                    html.A('Select File')
                                ]),
                                style={
                                    'width': '100%',
                                    'height': '60px',
                                    'lineHeight': '60px',
                                    'borderWidth': '1px',
                                    'borderStyle': 'dashed',
                                    'borderColor':'#0053b5',
                                    'borderRadius': '5px',
                                    'textAlign': 'center',
                                },
                                multiple=True
                        ),
                        html.Div(id='query-filename'),
                        html.Br(),
                        dcc.Loading(children=[
                            html.Div(id='datatable-query-container',),
                            dcc.Store(id='datatable-query-session'),
                            html.Br(),
                            html.Div(id='datatable-query-message', style={'margin-bottom':'5rem'}),
                        ], type="dot"),
                        
                    ],  width=5, style={'padding-right':'28px'}),

                    ### upload universe file
                    dbc.Col(children=[
                        html.Br(),
                        html.H6('Reference Lipidome'),
                        dcc.Upload(
                                id='upload-universe-data',
                                children=html.Div([
                                    'Drag and Drop or ',
                                    html.A('Select File')
                                ]),
                                style={
                                    'width': '100%',
                                    'height': '60px',
                                    'lineHeight': '60px',
                                    'borderWidth': '1px',
                                    'borderStyle': 'dashed',
                                    'borderColor':'#0053b5',
                                    'borderRadius': '5px',
                                    'textAlign': 'center',
                                },
                                multiple=True
                        ),
                        html.Div(id='universe-filename'),
                        html.Br(),
                        dcc.Loading(children=[
                            html.Div(id='datatable-universe-container'),
                            dcc.Store(id='datatable-universe-session'),
                            html.Br(),
                            html.Div(id='datatable-universe-message', style={'margin-bottom':'5rem'})
                        ], type="dot"),
                    ],  width=5, style={'padding':'0 40px 0 0'}),

                    dcc.Store(id='original-data-session'),

                    dbc.Col(children=[
                        ### upload DEMO FILES
                        html.Div([
                            html.H6('Example files', style={'display': 'inline-block'}),
                            html.Img(src='assets/icons/info-circle.svg', id='example-files-info', style={'display': 'inline-block', 'margin-left':'.5em'}),
                            dbc.Tooltip('After opening each demo (below), you will see example input files that you can try to run.', target='example-files-info', placement='right'),
                
                        ]),
                        dbc.Accordion([
                            dbc.AccordionItem([

                                html.P('Preview of Query and Reference Lipidome input files in .csv format'),

                                dbc.Row([
                                    dbc.Col([
                                        html.H6('Query'),
                                    ]),
                                    dbc.Col([
                                        html.A('Download', id='link-download-query-demo-1', href='./assets/data/demo_janovska_query.csv', style={'text-decoration':'none'}),
                                    ]),
                                ]),
                                html.Div(gen_table_demo('./data/demo_janovska_query.csv')),
                                
                                dbc.Row([
                                    dbc.Col([
                                        html.H6('Reference'),
                                    ]),
                                    dbc.Col([
                                        html.A('Download', id='link-download-universe-demo-1', href='./assets/data/demo_janovska_universe.csv', style={'text-decoration':'none'}),
                                    ]),
                                ], style={'margin-top':'10px'}),
                                html.Div(gen_table_demo('./data/demo_janovska_universe.csv')),

                                dbc.Button(id='demo-button-1', children='TRY DEMO', color='secondary', style={'margin':'1em 1em 1em 0', 'width':'auto'}),

                                dbc.Card([
                                    dbc.CardBody(
                                        [
                                            html.H6("References", className="card-title", style={'margin-bottom':'4px'}),
                                            html.Hr(style={'margin':'0 0 8px 0'}),

                                            html.P(children=[

                                                html.P('Janovska P, Melenovsky V, Svobodova M, Havlenova T, Kratochvilova H, Haluzik M, Hoskova E, Pelikanova T, Kautzner J, Monzo L, Jurcova I, Adamcova K, Lenkova L, Buresova J, Rossmeisl M, Kuda O, Cajka T, Kopecky J. (2020) Dysregulation of epicardial adipose tissue in cachexia due to heart failure: the role of natriuretic peptides and cardiolipin. ', style={'display':'contents'}),
                                                html.I('J Cachexia Sarcopenia Muscle, ', style={'display':'contents'}),
                                                html.P('11(6):1614-1627. ', style={'display':'contents'}),
                                                html.A('https://doi.org/10.1002/jcsm.12631', href='https://doi.org/10.1002/jcsm.12631', style={'display':'contents'}),

                                            ], style={'font-size': '.75rem'}),

                                            html.P("*see Figure 5D, Table S4, cluster A4 body weight-stable patients, lipid profiles of epicardial adipose tissue.", 
                                                    style={'margin':'8px 0 0 0', 'font-size': '.75rem', 'font-style': 'italic'})
                                        ]
                                    ),
                                ]),

                            ], title='DEMO 1'),

                            dbc.AccordionItem([

                                html.P('Preview of Query and Reference Lipidome input files in .csv format'),
                                dbc.Row([
                                    dbc.Col([
                                        html.H6('Query'),
                                    ]),
                                    dbc.Col([
                                        html.A('Download', id='link-download-query-demo-2', href='./assets/data/adipoatlas_query.csv', style={'text-decoration':'none'}),
                                    ]),
                                ]),
                                html.Div(gen_table_demo('./data/adipoatlas_query.csv')),
                                
                                dbc.Row([
                                    dbc.Col([
                                        html.H6('Reference'),
                                    ]),
                                    dbc.Col([
                                        html.A('Download', id='link-download-universe-demo-2', href='./assets/data/adipoatlas_universe.csv', style={'text-decoration':'none'}),
                                    ]),
                                ], style={'margin-top':'10px'}),
                                html.Div(gen_table_demo('./data/adipoatlas_universe.csv')),
                                
                                dbc.Button(id='demo-button-2', children='TRY DEMO', color='secondary', style={'margin':'1rem 0 2em 0', 'width':'auto'}),

                                dbc.Card([
                                    dbc.CardBody(
                                        [
                                            html.H6("References", className="card-title", style={'margin-bottom':'4px'}),
                                            html.Hr(style={'margin':'0 0 8px 0'}),

                                            html.P(children=[

                                                html.P('Lange, M., Angelidou, G., Ni, Z., Criscuolo, A., Schiller, J., Blüher, M., & Fedorova, M. (2021). AdipoAtlas: A reference lipidome for human white adipose tissue. ', style={'display':'contents'}),
                                                html.I('Cell Reports Medicine, ', style={'display':'contents'}),
                                                html.P('2(10), 100407. ', style={'display':'contents'}),
                                                html.A('https://doi.org/10.1016/j.xcrm.2021.100407', href='https://doi.org/10.1016/j.xcrm.2021.100407', style={'display':'contents'}),

                                            ], style={'font-size': '.75rem'}),

                                            html.P("*see Figure 4A: Statistically significantly upregulated lipid molecular species in white adipose tissue of obese versus lean patients.", 
                                                    style={'margin':'8px 0 0 0', 'font-size': '.75rem', 'font-style': 'italic'})
                                        ]
                                    ),
                                ]),

                            ], title='DEMO 2'),

                            dbc.AccordionItem([

                                html.P('Preview of Query and Reference Lipidome input files in .txt format'),

                                dbc.Row([
                                    dbc.Col([
                                        html.H6('Query'),
                                    ]),
                                    dbc.Col([
                                        html.A('Download', 
                                               id='link-download-query-demo-3', 
                                               href='./assets/data/Query_Human_Lung_Endothelial_Cells.txt', 
                                               style={'text-decoration':'none'},
                                               download='Query_Human_Lung_Endothelial_Cells.txt'),
                                    ]),
                                ]),
                                dbc.Textarea(className="mb-3", placeholder=gen_textarea_demo('./data/Query_Human_Lung_Endothelial_Cells.txt'), rows=10, readonly=True),
                                
                                dbc.Row([
                                    dbc.Col([
                                        html.H6('Reference'),
                                    ]),
                                    dbc.Col([
                                        html.A('Download', 
                                               id='link-download-universe-demo-3', 
                                               href='./assets/data/Universe_Human_Lung_Endothelial_Cells.txt', 
                                               style={'text-decoration':'none'},
                                               download='Universe_Human_Lung_Endothelial_Cells.txt'),
                                    ]),
                                ], style={'margin-top':'10px'}),
                                dbc.Textarea(className="mb-3", placeholder=gen_textarea_demo('./data/Universe_Human_Lung_Endothelial_Cells.txt'), rows=10, readonly=True),  

                                dbc.Button(id='demo-button-3', children='TRY DEMO', color='secondary', style={'margin':'0 0 2em 0', 'width':'auto'}),

                                dbc.Card([
                                    dbc.CardBody(
                                        [
                                            html.H6("References", className="card-title", style={'margin-bottom':'4px'}),
                                            html.Hr(style={'margin':'0 0 8px 0'}),

                                            html.P(children=[

                                                html.P('Clair, G., Reehl, S., Stratton, K. G., Monroe, M. E., Tfaily, M. M., Ansong, C., & Kyle, J. E. (2019). Lipid Mini-On: mining and ontology tool for enrichment analysis of lipidomic data. ', style={'display':'contents'}),
                                                html.I('Bioinformatics, ', style={'display':'contents'}),
                                                html.P('35(21), 4507–4508. ', style={'display':'contents'}),
                                                html.A('https://doi.org/10.1093/bioinformatics/btz250', href='https://doi.org/10.1093/bioinformatics/btz250', style={'display':'contents'}),

                                            ], style={'font-size': '.75rem'}),

                                            html.P(children=[

                                                html.P('Kyle, J. E., Clair, G., Bandyopadhyay, G., Misra, R. S., Zink, E. M., Bloodsworth, K. J., Shukla, A. K., Du, Y., Lillis, J., Myers, J. R., Ashton, J., Bushnell, T., Cochran, M., Deutsch, G., Baker, E. S., Carson, J. P., Mariani, T. J., Xu, Y., Whitsett, J. A., . . . Ansong, C. (2018). Cell type-resolved human lung lipidome reveals cellular cooperation in lung function. ', style={'display':'contents'}),
                                                html.I('Scientific Reports, ', style={'display':'contents'}),
                                                html.P('8(1). ', style={'display':'contents'}),
                                                html.A('https://doi.org/10.1038/s41598-018-31640-x', href='https://doi.org/10.1038/s41598-018-31640-x', style={'display':'contents'}),

                                            ], style={'font-size': '.75rem', 'margin':0}),
                                        ]
                                    ),
                                ]),

                            ], title='DEMO 3'),

                            dbc.AccordionItem([

                                html.P('Preview of Query and Reference Lipidome input files in .txt format'),
                                    
                                dbc.Row([
                                    dbc.Col([
                                        html.H6('Query'),
                                    ]),
                                    dbc.Col([
                                        html.A('Download', 
                                               id='link-download-query-demo-4', 
                                               href='./assets/data/Goslin_oxPEq.txt', 
                                               style={'text-decoration':'none'},
                                               download='Goslin_oxPEq.txt'),
                                    ]),
                                ]),
                                dbc.Textarea(className="mb-3", placeholder=gen_textarea_demo('./data/Goslin_oxPEq.txt'), rows=10, readonly=True),

                                dbc.Row([
                                    dbc.Col([
                                        html.H6('Reference'),
                                    ]),
                                    dbc.Col([
                                        html.A('Download', 
                                               id='link-download-universe-demo-4', 
                                               href='./assets/data/Goslin_oxPE.txt', 
                                               style={'text-decoration':'none'},
                                               download='Goslin_oxPE.txt'),
                                    ]),
                                ], style={'margin-top':'10px'}),
                                dbc.Textarea(className="mb-3", placeholder=gen_textarea_demo('./data/Goslin_oxPE.txt'), rows=10, readonly=True), 

                                dbc.Button(id='demo-button-4', children='TRY DEMO', color='secondary', style={'margin':'1em 1em 1em 0', 'width':'auto'}),

                                dbc.Card([
                                    dbc.CardBody(
                                        [
                                            html.H6("References", className="card-title", style={'margin-bottom':'4px'}),
                                            html.Hr(style={'margin':'0 0 8px 0'}),

                                            html.P(children=[

                                                html.P('Lauder, S. N., Allen-Redpath, K., Slatter, D. A., Aldrovandi, M., O’Connor, A., Farewell, D., Percy, C. L., Molhoek, J. E., Rannikko, S., Tyrrell, V. J., Ferla, S., Milne, G. L., Poole, A. W., Thomas, C. P., Obaji, S., Taylor, P. R., Jones, S. A., de Groot, P. G., Urbanus, R. T., . . . O’Donnell, V. B. (2017). Networks of enzymatically oxidized membrane lipids support calcium-dependent coagulation factor binding to maintain hemostasis. ', style={'display':'contents'}),
                                                html.I('Science Signaling, 10', style={'display':'contents'}),
                                                html.P('(507). ', style={'display':'contents'}),
                                                html.A('https://doi.org/10.1126/scisignal.aan2787', href='https://doi.org/10.1126/scisignal.aan2787', style={'display':'contents'}),

                                            ], style={'font-size': '.75rem', 'margin':0}),

                                            html.P("*see Figure 7, panel A: Red metabolites associated with platelet-type 12-LOX (p12-LOX).", 
                                                    style={'margin':'8px 0 16px 0', 'font-size': '.75rem', 'font-style': 'italic'}),

                                            html.P(children=[

                                                html.P('Ren, H., Triebl, A., Muralidharan, S., Wenk, M. R., Xia, Y., & Torta, F. (2021). Mapping the distribution of double bond location isomers in lipids across mouse tissues. ', style={'display':'contents'}),
                                                html.I('The Analyst, 146', style={'display':'contents'}),
                                                html.P('(12), 3899–3907. ', style={'display':'contents'}),
                                                html.A('https://doi.org/10.1039/d1an00449b', href='https://doi.org/10.1039/d1an00449b', style={'display':'contents'}),

                                            ], style={'font-size': '.75rem', 'margin':0}),

                                        ]
                                    ),
                                ]),

                            ], title='DEMO 4'),

                        ], id='accordion', start_collapsed=True, flush=True,),

                    ], width=2, style={'margin-top':'1.5rem', 'padding':'0 16px 0 0'}),
                ]),

                dbc.Row(children=[
                        dbc.Card([
                            dbc.CardBody(
                                [
                                    html.H4("Basics", className="card-title", style={'background-color':'#82c341', 
                                                                                     'padding':'12px',
                                                                                     'margin':0, 
                                                                                     'color':'#ffffff'}
                                    ),

                                    html.Div([
                                        html.P("Over-Representation Analysis (ORA) is a simple statistical method that determines whether a priori-defined set of variables is more present (over-represented) in a subset of variables than would be expected by chance. Lipid Over-Representation Analysis (LORA) is a tool that calculates ORA for lipidomics dataset and uses Goslin to incorporate the annotation level and known information about the structures of lipid species. Typical use in lipidomics: Which lipids are over-represented in my cluster of up-regulated lipid species in my experimental group?",
                                            className="card-text", style={'padding-bottom':'16px'}),
                                        html.Img(src='./assets/LORA-scheme-01.jpg', width='60%', style={'display': 'block',
                                                                                                        'margin-left': 'auto',
                                                                                                        'margin-right': 'auto',
                                                                                                        'margin-bottom':'16px'}),
                                    ],
                                    style={'padding':'12px'}),
            
                                ], 
                                style={'margin-bottom':'1rem',
                                       'padding':0, 
                                       'border':'1px solid #82c341',
                                       'border-radius':'5px',
                                       'background-color':'#ffffff'}
                            ),

                            dbc.CardBody(
                                [
                                    html.H4("How to use LORA", className="card-title", style={'background-color':'#82c341', 
                                                                                     'padding':'12px',
                                                                                     'margin':0, 
                                                                                     'color':'#ffffff'}
                                    ),

                                    html.Div([
                                        html.P(children=[
                                            html.A("Read the manual. ", href='/manual', style={'display':'contents'}),
                                            html.P("Prepare two text files: the 'reference' (full annotated lipidome) and the 'query' (a subset of the lipidome to test) in TXT or CSV format. Each file should contain a simple list (one lipid name per line). Select the Goslin grammar and upload the files (drag and drop or select file) into the application. If your lipid names are not parsed correctly, use the Goslin validator ", style={'display':'contents'}),
                                            html.A("https://apps.lifs-tools.org/goslin/", href='https://apps.lifs-tools.org/goslin/', style={'display':'contents'}),
                                            html.P(" to normalize your lipid nomenclature. Then follow the navigation.", style={'display':'contents'}),
                                        
                                        ], className="card-text", style={'padding-bottom':'16px'}),     
                                    ],
                                    style={'padding':'12px'}),

                                ],
                                style={'margin-bottom':'1rem', 
                                       'padding':0, 
                                       'border':'1px solid #82c341',
                                       'border-radius':'5px',
                                       'background-color':'#ffffff'}
                            ),

                            dbc.CardBody(
                                [
                                    html.H4("Goslin lipid structural hierarchy", className="card-title", style={'background-color':'#82c341', 
                                                                                     'padding':'12px',
                                                                                     'margin':0, 
                                                                                     'color':'#ffffff'}
                                    ),

                                    html.Div([
                                        html.P('Structural hierarchy representation of PE 16:1(6Z)/16:0;5OH[R],8OH;3oxo). LM: LIPID MAPS, HG: Head Group, FA: Fatty Acyl.', className="card-text", style={'padding-bottom':'16px'}),     
                                        
                                        dbc.Table(table_header + table_body, bordered=True, className='center', style={'width':'90%', 'margin-left': 'auto', 'margin-right': 'auto', 'margin-bottom':'2rem'}),

                                        html.H6('References'),

                                        html.A('Goslin webapplication documentation', href='https://apps.lifs-tools.org/goslin/documentation', style={'text-decoration': 'none', 'margin-bottom':'8px'}),

                                        html.P(children=[
                                        
                                            html.P('Kopczynski, D., Hoffmann, N., Peng, B., Liebisch, G., Spener, F., & Ahrends, R. (2022). Goslin 2.0 Implements the Recent Lipid Shorthand Nomenclature for MS-Derived Lipid Structures. ', style={'display':'contents'}),
                                            html.I('Analytical Chemistry, 94', style={'display':'contents'}),
                                            html.P('(16), 6097–6101. ', style={'display':'contents'}),
                                            html.A('https://doi.org/10.1021/acs.analchem.1c05430', href='https://doi.org/10.1021/acs.analchem.1c05430', style={'display':'contents'}),
                                        
                                        ]),
                                    
                                    ],
                                    style={'padding':'12px'}),

                                ],
                                style={'margin-bottom':'1rem', 
                                       'padding':0, 
                                       'border':'1px solid #82c341',
                                       'border-radius':'5px',
                                       'background-color':'#ffffff'}
                            ),

                            dbc.CardBody(
                                [
                                    html.H4("Statistics", className="card-title", style={'background-color':'#82c341', 
                                                                                        'padding':'12px',
                                                                                        'margin':0, 
                                                                                        'color':'#ffffff'}
                                    ),

                                    html.Div([
                                    
                                        html.P(children=[
                                            html.P("The enrichment ", style={'display':'contents'}),
                                            html.I("p", style={'display':'contents'}),
                                            html.P("-value is calculated using the Fisher exact test or Hypergeometric distribution, and multiple testing adjustment is applied to the results.", style={'display':'contents'})
                                        ], className="card-text"),
                                        
                                        html.Ul([
                                            html.Li(html.P("Benjamini-Hochberg (the classic False Discovery Rate)"), className="card-text", style={'margin':'0 0 4px 32px'}),
                                            html.Li(html.P("Bonferroni Correction (one-step correction)"), className="card-text", style={'margin':'0 0 4px 32px'}),
                                            html.Li(html.P("Holm Correction (using Bonferroni adjustments)"), className="card-text", style={'margin':'0 0 0 32px'}),
                                        ], style={'margin-bottom':'32px'}),

                                        html.H6("References", className="card-text"),
                                        html.P(children=[
                                            html.P('Chen, S. Y., Feng, Z., & Yi, X. (2017). A general introduction to adjustment for multiple comparisons. ', style={'display':'contents'}),
                                            html.I('Journal of Thoracic Disease, 9', style={'display':'contents'}),
                                            html.P('(6), 1725–1729. ', style={'display':'contents'}),
                                            html.A('https://doi.org/10.21037/jtd.2017.05.34', href='https://doi.org/10.21037/jtd.2017.05.34', style={'display':'contents'})
                                        ], className="card-text", style={'margin':'0 0 4px 0'}),
                                        
                                        html.P(children=[
                                            html.P('Huang, D. W., Sherman, B. T., & Lempicki, R. A. (2008). Bioinformatics enrichment tools: paths toward the comprehensive functional analysis of large gene lists. ', style={'display':'contents'}),
                                            html.I('Nucleic Acids Research, 37', style={'display':'contents'}),
                                            html.P('(1), 1–13. ', style={'display':'contents'}),
                                            html.A('https://doi.org/10.1093/nar/gkn923', href='https://doi.org/10.1093/nar/gkn923', style={'display':'contents'}),
                                        ], className="card-text", style={'padding-bottom':'16px'})

                                    ],
                                    style={'padding':'12px'}),
                                ],
                                style={'margin-bottom':'1rem',
                                       'padding':0,  
                                       'border':'1px solid #82c341',
                                       'border-radius':'5px',
                                       'background-color':'#ffffff'}
                            ),

                            dbc.CardBody(
                                [
                                    html.H4("Limitations", className="card-title", style={'background-color':'#b50800', 
                                                                                        'padding':'12px',
                                                                                        'margin':0, 
                                                                                        'color':'#ffffff'}
                                    ),

                                    html.Div([
                                    
                                        html.Ul([
                                            html.Li(html.P("We do not apply the ranking metric used in Gene Set Enrichment Analysis. Single lipids can not be members of two or more groups/categories/classes/subclasses or present multiple times in the same group. This feature will be included when this information is available in the databases (e.g., LIPID MAPS)."), className="card-text", style={'margin':'0 0 8px 0'}),
                                            html.Li(html.P("Short ‘query’ sets (e.g., n = 5) may yield unreliable results and could be evaluated as insignificant."), className="card-text", style={'margin':'0 0 8px 0'}),
                                            html.Li(html.P(children=[
                                                            html.P("Based on the ‘query’ and ‘reference’ size, the adjustment for multiple comparisons could impact the final ", style={'display':'contents'}),
                                                            html.I("p", style={'display':'contents'}),
                                                            html.P(" or ", style={'display':'contents'}),
                                                            html.I("q", style={'display':'contents'}),
                                                            html.P(" values.", style={'display':'contents'})
                                            ]), className="card-text", style={'margin':'0 0 8px 0'}),
                                            html.Li(html.P("Numerical values (lipid concentrations, fold changes, etc.) are not allowed. Use other bioinformatics tools (such as MetaboAnalyst) to select a subset of significantly altered lipids. Then use only the lipid names that changed in one direction only (either up or down) for the 'query'."), className="card-text", style={'margin':'0 0 8px 0'}),
                                            html.Li(html.P("Enrichment within ‘Acyls’ term is calculated at MOLECULAR SPECIES level only."), className="card-text", style={'margin':'0 0 8px 0'}),

                                        ]),
                                    ],
                                    style={'padding':'12px'}),
                                ],
                                style={'margin-bottom':'1rem',
                                       'padding':0,  
                                       'border':'1px solid #b50800',
                                       'border-radius':'5px',
                                       'background-color':'#ffffff'}
                            ),

                            dbc.CardBody(
                                [
                                    html.H4("Results", className="card-title", style={'background-color':'#82c341', 
                                                                                            'padding':'12px',
                                                                                            'margin':0, 
                                                                                            'color':'#ffffff'}
                                    ),

                                    html.Div([
                                        html.Ul([
                                            html.Li(html.P("The main output of LORA is a table of statistically significant terms describing the query subset."), className="card-text", style={'margin':'0 0 8px 0'}),
                                            html.Li(html.P("The UpSet plot can be used to identify the major structural features of the enriched lipids and to define the 'very important lipids' (VIL)."), className="card-text",  style={'margin':'0 0 8px 0'}),
                                            html.Li(html.P("The lipidome and its structural levels are visualized as an interactive lipidome network and hierarchical circular tree."), className="card-text",  style={'margin':'0 0 8px 0'}),
                                            html.Li(html.P("All files (reports, images, tables) are available for download. It is possible to download the drawn graphs (in JPEG, PNG and SVG) and the content (in JSON, XLSX and PhyloXML). "), className="card-text",  style={'margin':'0 0 8px 0'}),
                                            html.Li(html.P("User data is not stored and is deleted after 10 minutes. Download the ZIP report file."), className="card-text",  style={'margin':'0 0 8px 0'}),
                                        ]),
                                    ],
                                    style={'padding':'12px'}),
                                ],
                                style={'margin-bottom':'1rem',
                                       'padding':0, 
                                       'border':'1px solid #82c341',
                                       'border-radius':'5px',
                                       'background-color':'#ffffff'}
                            ),

                            dbc.CardBody(
                                [
                                    html.H4("Credits", className="card-title", style={'background-color':'#82c341', 
                                                                                            'padding':'12px',
                                                                                            'margin':0, 
                                                                                            'color':'#ffffff'}
                                    ),

                                    html.Div([
                                        html.Ul([
                                            html.Li(html.P("Michaela Vondrackova, Dominik Kopczynski, Nils Hoffmann, Ondrej Kuda."), className="card-text", style={'margin':'0 0 8px 0'}),
                                            html.Li(html.P("Supported by the project National Institute for Research of Metabolic and Cardiovascular Diseases (Programme EXCELES, ID Project No. LX22NPO5104) – Funded by the European Union – Next Generation EU."), className="card-text",  style={'margin':'0 0 8px 0'}),

                                        ]),
                                    ],
                                    style={'padding':'12px'}),
                                ],
                                style={'margin-bottom':'1rem',
                                       'padding':0, 
                                       'border':'1px solid #82c341',
                                       'border-radius':'5px',
                                       'background-color':'#ffffff'}
                            ),
                            dbc.CardBody(
                                [
                                    html.H4("Citing LORA", className="card-title", style={'background-color':'#82c341', 
                                                                                            'padding':'12px',
                                                                                            'margin':0, 
                                                                                            'color':'#ffffff'}
                                    ),

                                    html.Div([
                                        html.P(children=[
                                            html.P('Vondráčková, M., Kopczynski, D., Hoffmann, N., & Kuda, O. (2023). LORA, Lipid Over-Representation Analysis Based on Structural Information. ', style={'display':'contents'}),
                                            html.I('Analytical Chemistry, 95', style={'display':'contents'}),
                                            html.P('(34), 12600–12604. ', style={'display':'contents'}),
                                            html.A('https://doi.org/10.1021/acs.analchem.3c02039', href='https://doi.org/10.1021/acs.analchem.3c02039', style={'display':'contents'}),
                                        ]),
                                    ],
                                    style={'padding':'12px'}),
                                ],
                                style={'margin-bottom':'1rem',
                                       'padding':0, 
                                       'border':'1px solid #82c341',
                                       'border-radius':'5px',
                                       'background-color':'#ffffff'}
                            ),
                        ], style={'background-color':'#eeeeee', 'padding':'1rem'}),

                ], style={'margin-bottom':'3rem', 'padding':'12px'})
            ]),

            ### jgoslin tables
            dcc.Tab(label='Lipid Names Parsing', value='tab-2', className='custom-tab-2', selected_className='custom-tab-2--selected', disabled_className='custom-tab-2--disabled', id='tab-2', children=[
                html.Br(),
                html.H4('Lipid Nomenclature Parsing And Normalization'),

                dcc.Loading(children=[
                
                    html.Div([
                    
                        dbc.Row(children=[
    
                            html.H4('Query Table', id='query-jgoslin-table-header', style={'padding-bottom':'1em', 'display':'none'}),
                            dbc.Col(children=[
                                dcc.Checklist(id='checklist-query-jgoslin', className='dash-checklist', inputStyle={'margin-right': '5px'}, labelStyle={'display': 'flex', 'flex-wrap': 'nowrap'}),
                                html.Div(id='tooltips-query-container')
                            ], style={'width':'15%'}
                            ),

                            dbc.Col(children=[   
                                html.Div(id='query-process-container'),
                                dcc.Store(id='FA-options'),
                                dcc.Store(id='parameters-dynamic-checklist'),
                            ], style={'width':'85%'}
                            ),

                        ], id='query-jgoslin-row'),

                    ], id='div-query-process-container', style={'diplay':'none'}),

                    html.Div([
                        dbc.Row(children=[
                            html.H4('Reference Lipidome Table', id='universe-jgoslin-table-header', style={'padding-bottom':'1em', 'display':'none'}),
                            dbc.Col(children=[
                                dcc.Checklist(id='checklist-universe-jgoslin', className='dash-checklist', inputStyle={'margin-right': '5px'}, labelStyle={'display': 'flex', 'flex-wrap': 'nowrap'}),
                                html.Div(id='tooltips-universe-container')
                            ], style={'width':'15%'}
                            ),
                            dbc.Col(children=[
                                html.Div(id='universe-process-container'),
                            ], style={'width':'85%'}
                            ),
                        ], id='universe-jgoslin-row'),

                    ], id='div-universe-process-container', style={'diplay':'none'}),

                ], type="dot", fullscreen=True, style={'position':'fixed', 
                                           'top':'0px',
                                           'left':'0px',
                                           'width':'100%', 
                                           'z-index':'9999', 
                                           'background-color': 'rgba(255,255,255,0.8)'}),

                dbc.Card(
                    dbc.Row([
                        dbc.Col(
                            dbc.CardImg(
                                src="./assets/parsing_illustration.jpeg",
                                style={'padding':'1rem'}
                            ),
                            className="col-md-4"),
                        dbc.Col([
                            dbc.CardBody([
                            
                                html.H6(),
                                html.P(children=[
                                    html.B('Schematic illustration of ceramide Cer(d18:1(4E)/26:0(2OH)) parsing and normalization ', style={'display':'contents'}),
                                    html.P('(Kopczynski, D., 2022).', style={'display':'contents'})
                                ]),

                                html.P('To see more information about processing visit reference below:'),

                                html.P(children=[
                                
                                    html.P('Kopczynski, D., Hoffmann, N., Peng, B., Liebisch, G., Spener, F., & Ahrends, R. (2022). Goslin 2.0 Implements the Recent Lipid Shorthand Nomenclature for MS-Derived Lipid Structures. ', style={'display':'contents'}),
                                    html.I('Analytical Chemistry, 94', style={'display':'contents'}),
                                    html.P('(16), 6097–6101. ', style={'display':'contents'}),
                                    html.A('https://doi.org/10.1021/acs.analchem.1c05430', href='https://doi.org/10.1021/acs.analchem.1c05430', style={'display':'contents'}),
                                
                                ]),

                            ], style={'background-color':'#eeeeee', 'width': '100%', 'height': '100%'}),

                        ], 
                        className="col-md-8"),
                    ]),
                    style={'margin':'1rem 0 3rem 0', 
                           'border': '2px solid #eeeeee'}
                ),
                html.Div([
                    dbc.Card([
                        dbc.Row([

                            dbc.Col([
                                dbc.CardImg(
                                    src='assets/icons/exclamation-circle.svg', 
                                    style={
                                            'width':'50%',
                                            'filter': 'drop-shadow(0px 4px 4px rgba(0, 0, 0, 0.4))'
                                    }
                                ),
                            ], className="col-md-2 d-flex justify-content-center align-items-center"),
                            dbc.Col([
                                dbc.CardBody([
                                    html.Div([
                                        html.H4("Info!", 
                                                className="card-title", 
                                                style={
                                                        'display': 'inline-block', 
                                                        'margin-bottom':0, 
                                                        'font-weight': 'bold'
                                                }),
                                        html.Hr(style={
                                                    'color':'#dddddd', 
                                                    'height':'2px', 
                                                    'margin':'4px 0 8px 0', 
                                                    'opacity':1
                                                }),
                                    ]),
                                    html.Div(children=[], id="alert-process-button"),
                                    html.Div(children=[
                                        dbc.Button(
                                                id="process-button", 
                                                children="Process", 
                                                style={'width':'auto'}, 
                                                outline=True, 
                                                color="light"),
                                    ], style={'display':'flex', 'justify-content': 'center', 'align-items':'center'}),
                                ]),
                            ], className="col-md-10")

                        ], className="g-0 d-flex align-items-center",
                        )
                    ],
                    className="mb-3 shadow",
                    style={"width": "40rem"}, color="#0053b5", inverse=True

                )], id='div-process-button', style={'display':'flex', 'justify-content': 'center', 'align-items':'center'})
                

            ], disabled=True),

            ### Enrichment Analysis
            dcc.Tab(label='Enrichment Analysis', value='tab-3', className='custom-tab-3', selected_className='custom-tab-3--selected', disabled_className='custom-tab-3--disabled', id='tab-3', children=[
                dbc.Row([
                    dbc.Col([
                            html.Div([
                                html.Br(),
                                html.H4('Enrichment Analysis'),
                                html.Div([
                                    html.H6('Enrichment test:'),
                                    dcc.Dropdown(['Fisher exact test', 'Hypergeometric'], 'Fisher exact test', id='statistical-test-dropdown')
                                ], style={'margin':'5px 0 5px 0'}),

                                html.Div([    
                                    dcc.RadioItems([{'label':html.Div(['greater'], id='target-greater', style={'display':'inline-block'}), 'value':'greater'},
                                                    {'label':html.Div(['less'], id='target-less', style={'display':'inline-block'}), 'value':'less',},
                                                    {'label':html.Div(['two-sided'], id='target-two-sided', style={'display':'inline-block'}),'value':'two-sided'}
                                                    ], 'greater', id='radioitems-alternative', 
                                                    inline = True, labelStyle={'display': 'flex', 'flex-direction': 'row', "margin-right": "1rem"}, 
                                                    inputStyle={"margin-right": "5px"},
                                                    ),
                                    
                                    dbc.Tooltip('The odds ratio of the underlying population is greater than one.', target='target-greater'),
                                    dbc.Tooltip('The odds ratio of the underlying population is less than one.', target='target-less'),
                                    dbc.Tooltip('The odds ratio of the underlying population is not one.', target='target-two-sided'),
                                ], style={'margin':'5px 0 20px 0', 'display': 'flex'}),

                                html.Hr(style={'color':'#0053b5', 'height':'2px'}),
                                
                                html.Div([
                                    html.H6('Parameters to test:'),
                                    dcc.Checklist([
                                                {'label':'Lipid Maps Category', 'value': 'Lipid Maps Category'}, 
                                                {'label':'Lipid Maps Main Class or Sub Class', 'value': 'Lipid Maps Main Class'}, 
                                                {'label':'Fatty Acyls', 'value': 'Acyls'}
                                        ], ['Lipid Maps Category', 'Lipid Maps Main Class', 'Acyls'], id='enrichment-checklist', labelStyle={"margin-right": "1rem", 'display':'block'}, inputStyle={"margin-right": "5px"}),
                                ], style={'margin':'5px 0 20px 0'}),

                                html.Hr(style={'color':'#0053b5', 'height':'2px'}),

                                html.H6('Parameters to test within subset:'),
                            
                                html.P('Select subset:', style={'font-style': 'italic', 'margin':'8px 0 0 0'}),
                                dcc.Checklist([
                                                {'label':'Lipid Maps Category', 'value': 'Lipid Maps Category'}, 
                                                {'label':'Lipid Maps Main Class or Sub Class', 'value': 'Lipid Maps Main Class'}, 
                                        ], ['Lipid Maps Category', 'Lipid Maps Main Class'], id='enrichment-checklist-subset', labelStyle={"margin-right": "1rem", 'display':'block'}, inputStyle={"margin-right": "5px"}),
                                
                                html.P('Select parameters:', style={'font-style': 'italic', 'margin':'8px 0 0 2rem'}),
                                
                                dcc.Checklist(id='parameters-checklist', labelStyle={"margin-right": "1rem", 'display':'block'}, inputStyle={"margin-right": "5px"}, style={'margin-left':'2rem'}),
                                
                                html.Hr(style={'color':'#0053b5', 'height':'2px'}),

                                dbc.Row(children=[

                                    dbc.Col(children=[
                                        html.H6('Multiple hypothesis testing:'),
                                        dcc.Dropdown([
                                                {
                                                    'label': 'FDR (Benjamini/Hochberg)',
                                                    'value': 'fdr_bh',
                                                    'title': 'False Discovery Rate (FDR; Benjamini/Hochberg)'
                                                },
                                                {
                                                    'label': 'Bonferroni (one-step)',
                                                    'value': 'bonferroni',
                                                    'title': 'Bonferroni Correction (one-step correction)'
                                                },
                                                {
                                                    'label': 'Holm (Bonferroni adj.)',
                                                    'value': 'holm',
                                                    'title': 'Holm Correction (using Bonferroni adjustments)'
                                                }
                                            ],
                                            'fdr_bh', id='statistical-method-dropdown'),
                                    ], style={'padding':'0'}),

                                ], style={'margin':'20px 0'}),

                                dbc.Row(children=[

                                    dbc.Col(children=[
                                        html.H6('Alpha level:'),
                                        dbc.Input(value=0.1, id='alpha-level-input', type='number', size='sm'),
                                    ], style={'padding-left':'0'}),  

                                ], style={'margin':'20px 0'}),

                                html.Hr(style={'color':'#0053b5', 'height':'2px'}),

                                html.Div([
                                    html.H6('Filter count:'),
                                    dbc.Input(value=1, id='filter-count', type='number', size='sm'),
                                ]),

                                html.Hr(style={'color':'#0053b5', 'height':'2px'}),

                                dcc.Checklist(options=[{'label': 'Show only statistically significant results', 'value':'Filter statistically significant results'}], 
                                              value=['Filter statistically significant results'], id='filter-enrichment', inputStyle={"margin-right": "5px"}),
                                
                                dbc.Button(id='enrichment-button', children="Process", style={'margin':'10px auto 10px auto', 'width':'auto'}, color="secondary", disabled=True),

                                html.Div(id='output-select-message'),

                            ], style={'background-color':'#eeeeee', 'border': '1px solid rgba(0,0,0,.125)', 'border-radius': '.25rem', 'margin-left':'14px', 'margin-top':'10px', 'padding-right':'8px', 'padding-left':'8px'}),

                    ], width='auto', style={'width':'20%', 'padding':0, 'margin-bottom':'5em'}),

                    dbc.Col([
                        dcc.Loading(children=[
    
                            html.Div(children=[

                                html.H4('Over-represented terms', style={'margin-top':'1.625rem'}),
                                html.Div(id='enrichment-container'),
                                dcc.Store(id='enrichment-container-session'),

                                html.H4('Very Important Lipid (VIL)', style={'margin-top':'4rem'}),
                                html.Div(id='vil-table-container'),

                                html.H4('UpSet plot for term intersection visualization', style={'margin-top':'4rem'}),
                                dcc.Graph(id='basic-interactions'),
                                dcc.Store(id='basic-interactions-session'),
                                dcc.Store(id='VIL_table_session'),
                                dcc.Store(id='all_results_session'),
                                html.Div(id='upset_table', style={'width':'100%', 'margin-bottom':'2rem'}),
                                
                            ], id='enrichment-analysis-column-container', style={'display':'none'})
                             
                        ], type="dot", fullscreen=True, style={'position':'fixed', 
                                                               'top':'0px',
                                                               'left':'0px',
                                                               'width':'100%', 
                                                               'z-index':'9999', 
                                                               'background-color': 'rgba(255,255,255,0.8)'}),

                        dbc.Card([
                            dbc.CardBody(
                                [
                                    html.H4("Results", className="card-title", style={'background-color':'#82c341', 
                                                                                        'padding':'12px',
                                                                                        'margin':0, 
                                                                                        'color':'#ffffff'}
                                    ),

                                    html.Div([
                                        html.Ul([
                                            html.Li(html.P(children=[
                                                html.P("The primary output of LORA is a table of statistically significant terms describing the ‘query’ subset. The over-represented terms are calculated at specific levels (indicated in the table) and corrected for multiple hypothesis testing according to the parameters. The 'FDR' column contains corrected ", style={'display':'contents'}),
                                                html.I("p", style={'display':'contents'}),
                                                html.P("-values according to the selected method (FDR, Bonferroni Correction, or Holm-Bonferroni).", style={'display':'contents'})
                                            ]), className="card-text", style={'margin':'0 0 8px 0'}),
                                            html.Li(html.P("The default setting represents the most widely used scenario in lipidomics – all available parameters tested, False discovery rate set at 0.1, Fisher exact test performed as 'greater than' (over-represented), filter count set at 1. Filter count removes over-represented terms where only n values in query set are present (e.g., when only one molecule in the set fulfills a specific condition, the result is unreliable). Select fewer parameters to speed up the calculations."), className="card-text",  style={'margin':'0 0 8px 0'}),
                                            html.Li(html.P("Columns 'Missing Query' and 'Missing Reference' show how many lipids were tested. Beware that short QUERY sets (e.g., n ~ 5) may yield unreliable results and could be evaluated as insignificant. Also, if you have similar lipids reported at different levels [e.g., PC 36:1 and PC(18:1(9Z)/18:1(9Z)) ], calculation at SPECIES level is correct, but only the second one will be calculated at FULL STRUCTURE level. Thus, interpret the results carefully."), className="card-text",  style={'margin':'0 0 8px 0'}),
                                            html.Li(children=[
                                                html.P("Secondary results are:", style={'margin-bottom':'4px'}),
                                                html.Ul([
                                                    html.Li("VIL table (Tab 3, Enrichment analysis)"),
                                                    html.Li("UpSet plot (Tab 3, Enrichment analysis)"),
                                                    html.Li("Lipidome hierarchical circular tree (Tab 4, Graphical Representation)"),
                                                    html.Li("Lipidome network (Tab 4, Graphical Representation)"),
                                                ], className="card-text",  style={'margin':'0 0 8px 0'}),
                                            html.Li(html.P("All results and a PDF report will be available for download as a ZIP file. The download link will be available at the top right of the screen once the calculation is complete."), className="card-text",  style={'margin':'0 0 8px 0'})
                                            ])


                                        ]),
                                    ],
                                    style={'padding':'12px'}),

                                ],
                                style={'margin-bottom':'1rem', 
                                        'padding':0, 
                                        'border':'1px solid #82c341',
                                        'border-radius':'5px',
                                        'background-color':'#ffffff'}
                            ),

                            dbc.CardBody(
                                [
                                    html.H4("Very Important Lipid (VIL)", className="card-title", style={'background-color':'#82c341', 
                                                                                        'padding':'12px',
                                                                                        'margin':0, 
                                                                                        'color':'#ffffff'}
                                    ),

                                    html.Div([
                                        html.Ul([
                                            html.Li(html.P("VIL defines the most representative lipid(s) of the ‘query’."), className="card-text", style={'margin':'0 0 8px 0'}),
                                            html.Li([
                                                html.P("The over-represented terms describing the structural patterns of lipids may overlap. For instance, the term ", style={'display':'contents'}),
                                                html.B("Acyls [MOLECULAR_SPECIES]: 18:3 ", style={'display':'contents'}),
                                                html.P("and term ", style={'display':'contents'}),
                                                html.B("Acyls [MOLECULAR_SPECIES]: 12:0 ", style={'display':'contents'}),
                                                html.P("(both significantly enriched) overlap at lipid TG 12:0_18:2_18:3.", style={'display':'contents'})], className="card-text", style={'margin':'0 0 8px 0'}),
                                            html.Li(html.P("Lipid(s) that are present in most over-represented terms are defined as VIL(s). Corrected p-values of the specific lipid(s) are reported for each over-represented term in the VIL table."), className="card-text", style={'margin':'0 0 8px 0'}),
                                            html.Li(html.P("Calculation costs of all possible term intersections grow exponentially. Therefore, the upper limit is 13 terms. If more than 13 terms resulted from the analysis, tighten the statistical parameters to get only highly significant terms and the VIL report."), className="card-text", style={'margin':'0 0 8px 0'}),
                                        ]),
                                    ],
                                    style={'padding':'12px'}),

                                ],
                                style={'margin-bottom':'1rem', 
                                        'padding':0, 
                                        'border':'1px solid #82c341',
                                        'border-radius':'5px',
                                        'background-color':'#ffffff'}
                            ),

                            dbc.CardBody(
                                [
                                    html.H4("UpSet plot for Term Intersection Visualization", className="card-title", style={'background-color':'#82c341', 
                                                                                        'padding':'12px',
                                                                                        'margin':0, 
                                                                                        'color':'#ffffff'}
                                    ),

                                    html.Div([
                                        html.Ul([
                                            html.Li(html.P("The UpSet plot can be used to identify the major structural features of the enriched lipids and define the VILs in a graphical representation."), className="card-text", style={'margin':'0 0 8px 0'}),
                                            html.Li(html.P([
                                                html.P("Connected black dots represent the intersection of the terms labeled above. The size of the term intersection (cardinality bar plot) represents the number of lipids that share this specific set of structural features. The ", style={'display':'contents'}),
                                                html.I("p", style={'display':'contents'}),
                                                html.P("-value(s) belong to the particular lipids within each term (", style={'display':'contents'}),
                                                html.I("n", style={'display':'contents'}),
                                                html.P(" lipids × ", style={'display':'contents'}),
                                                html.I("m", style={'display':'contents'}),
                                                html.P(" terms). The bar graph at the bottom shows how many lipids fit within the specified term.", style={'display':'contents'})
                                            ]), className="card-text", style={'margin':'0 0 8px 0'}),
                                            html.Li(html.P("The UpSet plot is sorted by the number of overlaps and the size of the term overlap. Empty groups are omitted to reduce the size of the plot."), className="card-text", style={'margin':'0 0 8px 0'}),
                                            html.Li(html.P("The plot is interactive. Click on the bar in the Cardinality Bar Plot to generate a table of lipids belonging to that particular term intersection."), className="card-text", style={'margin':'0 0 8px 0'}),
                                            html.Li(html.P("The computation limit is set to 13 terms as above for the VIL table."), className="card-text", style={'margin':'0 0 8px 0'}),
                                        ]),
                                    ],
                                    style={'padding':'12px'}),

                                ],
                                style={'margin-bottom':'1rem', 
                                        'padding':0, 
                                        'border':'1px solid #82c341',
                                        'border-radius':'5px',
                                        'background-color':'#ffffff'}
                            ),

                        ], style={'background-color':'#eeeeee', 'padding':'1rem'}),


                    ], width='auto', style={'width':'79%', 'margin-top':'10px'}),

                ], style={'margin-bottom':'32px'}),

            ], disabled=True),

            ### Net Graph
            dcc.Tab(label='Graphical Representation', value='tab-4', className='custom-tab-4', selected_className='custom-tab-4--selected', disabled_className='custom-tab-4--disabled',id='tab-4', children=[
                html.Div(children=[
                        dbc.Row([
                                dbc.Col([
                                    dbc.Card([
                                        dbc.CardBody(
                                            [
                                                html.H4("Lipidome hierarchical circular tree", className="card-title", style={'background-color':'#82c341', 'padding':'12px','margin':0,'color':'#ffffff'}),
                                                html.Div([
                                                        html.Ul([
                                                            html.Li(html.P("Lipidome is organized according to Goslin levels and SHORTHAND2020 classification system. Lipidome node is the root."), className="card-text", style={'margin':'0 0 8px 0'}),
                                                            html.Li(html.P("Each lipid is annotated as specific level based on provided information. The last available level is marked with a bold dot."), className="card-text", style={'margin':'0 0 8px 0'}),
                                                            html.Li(html.P("Only CATEGORY and CLASS levels are explicitely labeled to preserve plot clarity."), className="card-text", style={'margin':'0 0 8px 0'}),
                                                            html.Li(html.P("The plot is responsive and interactive (zoom, hover). Image file and phyloXML file is available in report zip package."), className="card-text", style={'margin':'0 0 8px 0'}),
                                                            html.Li(html.P("Legend:"), className="card-text", style={'margin':'0 0 8px 0'}),
                                                                                                                                                                                  
                                                            html.Img(src='./assets/circular_tree-legend.jpg', width='100%', style={'display': 'block',
                                                                                                            'margin-left': 'auto',
                                                                                                            'margin-right': 'auto',
                                                                                                            'margin-bottom':'16px'}),                                                            
                                                        ]),
                                                    ], style={'padding':'12px'}),
                                            ], style={'margin-bottom':'1rem', 'padding':0}
                                        ),
                                    ]),                                
                                ], style={'width':'50%', 'align':'center', 'margin-left':0, 'margin-top':'10px', 'margin-bottom':'1em'}
                                ),
                                dbc.Col([                                        
                                    dcc.Graph(id='phylo_tree_figure'),
                                        
                                ], style={'width':'50%', 'align':'start', 'margin-left':0, 'margin-top':'10px', 'margin-bottom':'1em'}),
                                                
                        ]),
                        dbc.Row([html.Hr(style={'margin':'0 0 8px 0'}),]),
                        dbc.Row([
                                dbc.Col([
                                    dbc.Card(
                                    [
                                        dbc.CardBody(
                                            [
                                                html.H4("Lipidome network", className="card-title", style={'background-color':'#82c341', 'padding':'12px','margin':0,'color':'#ffffff'}),
                                                html.Div([
                                                        html.Ul([
                                                            html.Li(html.P("Lipidome is organized according to LipidMaps classification system"), className="card-text", style={'margin':'0 0 8px 0'}),
                                                            html.Li(html.P("Node size represents the number of lipids within the hierarchcival level."), className="card-text", style={'margin':'0 0 8px 0'}),
                                                            html.Li(html.P("Blue section of the circle represents the query lipids."), className="card-text", style={'margin':'0 0 8px 0'}),
                                                            html.Li(html.P("Red section of the circle marks statistically significant result at the hierarchical level."), className="card-text", style={'margin':'0 0 8px 0'}),
                                                            html.Li(html.P("Green border marks statistically significant result within a tested subset."), className="card-text", style={'margin':'0 0 8px 0'}),
                                                            html.Li(html.P("Click the node to get more information in a table below."), className="card-text", style={'margin':'0 0 8px 0'}),                                                            
                                                            html.Li(html.P("The plot is responsive and interactive (zoom, move nodes, click). Image file is available in report zip package."), className="card-text", style={'margin':'0 0 8px 0'}),
                                                            html.Li(html.P("Legend:"), className="card-text", style={'margin':'0 0 8px 0'}),
                                                                                                                                                                                  
                                                            html.Img(src='./assets/cytoscape-legend.jpg', width='60%', style={'display': 'block',
                                                                                                            'margin-left': 'auto',
                                                                                                            'margin-right': 'auto',
                                                                                                            'margin-bottom':'16px'}), 
                                                            html.Li(html.P("The legend (nodes with predefined size) is generated within the map as an independent network to keep the correct scale."), className="card-text", style={'margin':'0 0 8px 0'}),                                                                                                            
                                                        ]),
                                                    ], style={'padding':'12px'}),
                                            ], style={'margin-bottom':'1rem', 'padding':0}
                                        ),
                                    ]),
                                    html.Hr(style={'margin':'0 0 8px 0'}),
                                    html.Div(id='cytoscape-tapNodeData-output', style={} ),
                                    
                                ], style={'width':'50%', 'margin-left':0, 'margin-top':'10px', 'margin-bottom':'1em'}),

                                dbc.Col([
                                ## Cytoscape                       
                                    html.Div(children=[
                                        cyto.Cytoscape (
                                            id='cytoscape',
                                            layout={
                                                'name': 'fcose',
                                                'padding': 1
                                            },
                                            zoomingEnabled=True,
                                            zoom=0.5,
                                            minZoom=0.2,
                                            maxZoom= 3,
                                            responsive=True,
                                            stylesheet=[{
                                                'selector': 'node',
                                                'style': {
                                                    'shape' : 'data(shape)',
                                                    'width': "mapData(size, 10, 200, 20, 100)",
                                                    'height': "mapData(size, 10, 200, 20, 100)",
                                                    'content': 'data(id)',
                                                    'text-halign': 'data(halign)',
                                                    'text-valign': 'data(valign)',
                                                    'font-size': 'data(font_size)',
                                                    'pie-size': '99%',
                                                    'pie-1-background-color': '#00bfff',
                                                    'pie-1-background-size': 'mapData(sector1, 0, 100, 0, 100)',
                                                    'pie-2-background-color': '#87ceeb',
                                                    'pie-2-background-size': 'mapData(sector2, 0, 100, 0, 100)',
                                                    'pie-3-background-color': 'red',
                                                    'pie-3-background-size': 'mapData(sector3, 0, 100, 0, 100)',
                                                    'border-width' : 'data(border_width)',
                                                    'border-color': 'data(highlight)'
                                                }
                                            }, {
                                                'selector': 'edge',
                                                'style': {
                                                    'curve-style': 'bezier',
                                                    'width': 2,
                                                    'target-arrow-shape': 'triangle',
                                                    'opacity': 0.5
                                                }
                                            }, {
                                                'selector': ':selected',
                                                'style': {
                                                    'background-color': 'black',
                                                    'line-color': 'black',
                                                    'target-arrow-color': 'black',
                                                    'source-arrow-color': 'black',
                                                    'opacity': 1
                                                }
                                            },
                                            {
                                                'selector':'pink',
                                                'style': {
                                                    'background-color': 'black',
                                                    'border': '1px #ff0000 solid',
                                        
                                                    'animation': 'blink 1s',
                                                    'animation-iteration-count': '3'            
                                                },                           
                                            },
                                                {
                                                'selector': '.faded',
                                                'style': {
                                                    'opacity': 0.25,
                                                    'text-opacity': 0
                                                }
                                            }],
                                            style={
                                                'padding':'.5rem 0 .5rem 0',
                                                'margin-top':'10px',
                                                'width': '880px',
                                                'height': '880px',
                                                'background-color' : 'rgb(245, 245, 245)'           
                                            }
                                        ),
                                    ]),
                                ], style={'width':'50%'}),                  
                        ]),
                ]),
            ], disabled=True)
        
        ], colors={
                "border": "white",
                "primary": "#82c341",
                "background": "#eeeeee",
        }),

    ], style={'margin': '0 2rem'}),

    footer,
])


# change url path
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/manual':
        return manual_layout
    else:
        return app_layout



def parse_contents(contents, filename):

    session_id = flask.session['session_id']
    filename = ' '.join(map(str, filename))

    for e in contents:
        content_type, content_string = e.split(',')

    decoded = base64.b64decode(content_string)

    cache.set(session_id, decoded)
    data_input = cache.get(session_id)

    header = has_header(data_input)

    try:
        if filename.endswith(('csv', 'txt')):
            return pd.read_csv(io.StringIO(data_input.decode('utf-8')), sep='\t', header=0 if header else None)
        elif filename.endswith(('xls', 'xlsx')):
            return pd.read_excel(io.BytesIO(data_input), sep='\t', header=0 if header else None)
    except Exception as e:
        return print('There was an error processing this file.')

    

### tab-2 callback
@app.callback(Output('tab-2', 'disabled'),
              Input('datatable-query-container', 'children')
)
def tabs_disable(query_container):
    btn = dash.callback_context.triggered[0]["prop_id"].split(".")
    triggered_id = ctx.triggered_id
    if triggered_id == 'datatable-query-container':
        return False



### tab-3 callback
@app.callback(Output('tab-3', 'disabled'),
              Input('query-process-container', 'children'),
              Input('datatable-query-session', 'data'),)
def tabs_disable(query_container, dt_query_session):
    triggered_id = ctx.triggered_id

    if triggered_id == 'query-process-container':
        return False
    if triggered_id == 'datatable-query-session':
        return True



### tab-4 callback
@app.callback(Output('tab-4', 'disabled'),
              Input('enrichment-container', 'children'),
              Input('datatable-query-session', 'data'))
def tabs_disable(enrichment_container, dt_query_session):
    triggered_id = ctx.triggered_id

    if triggered_id == 'enrichment-container':
        return False
    if triggered_id == 'datatable-query-session':
        return True



### query lipid names - filename
@app.callback(Output('query-filename', 'children'),
              Input('demo-button-1', 'n_clicks'),
              Input('demo-button-2', 'n_clicks'),
              Input('demo-button-3', 'n_clicks'),
              Input('demo-button-4', 'n_clicks'),
              Input('upload-query-data', 'contents'),
              State('upload-query-data', 'filename'))
def update_query_output_filename(demo_1, demo_2, demo_3, demo_4, contents, filename):
    triggered_id = ctx.triggered_id

    if triggered_id == None:
        raise PreventUpdate
    if triggered_id == 'upload-query-data':
        return [
            html.Img(src='assets/icons/file-earmark-check.svg', style={'display': 'inline-block', 'margin-right':'.5em'}),
            html.P(''.join(filename), style={'display': 'inline-block'})
        ]
        
    if triggered_id == 'demo-button-1':
        return [
            html.Img(src='assets/icons/file-earmark-check.svg', style={'display': 'inline-block', 'margin-right':'.5em'}),
            html.P('demo_janovska_query.csv', style={'display': 'inline-block'})
        ]
        
    if triggered_id == 'demo-button-2':
        return [
            html.Img(src='assets/icons/file-earmark-check.svg', style={'display': 'inline-block', 'margin-right':'.5em'}),
            html.P('adipoatlas_query.csv', style={'display': 'inline-block'})
        ]

    if triggered_id == 'demo-button-3':
        return [
            html.Img(src='assets/icons/file-earmark-check.svg', style={'display': 'inline-block', 'margin-right':'.5em'}),
            html.P('Query_Human_Lung_Endothelial_Cells.txt', style={'display': 'inline-block'})
        ]

    if triggered_id == 'demo-button-4':
        return [
            html.Img(src='assets/icons/file-earmark-check.svg', style={'display': 'inline-block', 'margin-right':'.5em'}),
            html.P('Goslin_oxPEq.txt', style={'display': 'inline-block'})
        ]



### universe lipid names - filename
@app.callback(Output('universe-filename', 'children'),
              Input('demo-button-1', 'n_clicks'),
              Input('demo-button-2', 'n_clicks'),
              Input('demo-button-3', 'n_clicks'),
              Input('demo-button-4', 'n_clicks'),
              Input('upload-universe-data', 'contents'),
              State('upload-universe-data', 'filename'))
def update_query_output_filename(demo_1, demo_2, demo_3, demo_4, contents, filename):
    triggered_id = ctx.triggered_id

    if triggered_id == None:
        raise PreventUpdate
    if triggered_id == 'upload-universe-data':
        return [
            html.Img(src='assets/icons/file-earmark-check.svg', style={'display': 'inline-block', 'margin-right':'.5em'}),
            html.P(''.join(filename), style={'display': 'inline-block'})
        ]

    if triggered_id == 'demo-button-1':
        return [
            html.Img(src='assets/icons/file-earmark-check.svg', style={'display': 'inline-block', 'margin-right':'.5em'}),
            html.P('demo_janovska_universe.csv', style={'display': 'inline-block'})
        ]

    if triggered_id == 'demo-button-2':
        return [
            html.Img(src='assets/icons/file-earmark-check.svg', style={'display': 'inline-block', 'margin-right':'.5em'}),
            html.P('adipoatlas_universe.csv', style={'display': 'inline-block'})
        ]

    if triggered_id == 'demo-button-3':
        return [
            html.Img(src='assets/icons/file-earmark-check.svg', style={'display': 'inline-block', 'margin-right':'.5em'}),
            html.P('Universe_Human_Lung_Endothelial_Cells.txt', style={'display': 'inline-block'})
        ]

    if triggered_id == 'demo-button-4':
        return [
            html.Img(src='assets/icons/file-earmark-check.svg', style={'display': 'inline-block', 'margin-right':'.5em'}),
            html.P('Goslin_oxPE.txt', style={'display': 'inline-block'})
        ]



### query and universe lipid names - content
@app.callback(Output('datatable-query-container', 'children'),
              Output('datatable-universe-container', 'children'),
              Output('datatable-query-message', 'children'),
              Output('datatable-universe-message', 'children'),
              Output('datatable-query-session', 'data'),
              Output('datatable-universe-session', 'data'),
              Output('original-data-session', 'data'),
              Input('demo-button-1', 'n_clicks'),
              Input('demo-button-2', 'n_clicks'),
              Input('demo-button-3', 'n_clicks'),
              Input('demo-button-4', 'n_clicks'),
              Input('parser-dropdown', 'value'),
              Input('upload-query-data', 'contents'),
              Input('upload-universe-data', 'contents'),
              State('upload-query-data', 'filename'),
              State('upload-universe-data', 'filename'))
def update_query_and_universe_output(demo_button_1, demo_button_2, demo_button_3, demo_button_4, parser_dropdown, contents_query, contents_universe, filename_query, filename_universe):
    
    triggered_id = ctx.triggered_id

    session_id = flask.session['session_id']
    clear_old_assets_and_cache(os.getcwd(), session_id)

    report_path = create_dir(session_id)
    cache.set('report_path'+session_id, report_path)

    if (triggered_id == 'demo-button-1' or 
        triggered_id == 'demo-button-2' or 
        triggered_id == 'demo-button-3' or 
        triggered_id == 'demo-button-4') and contents_query is None and contents_universe is None and parser_dropdown == 'LIPID':
        
        if triggered_id == 'demo-button-1':
            filename_query = 'demo_janovska_query.csv'
            filename_universe = 'demo_janovska_universe.csv'

            content_query = pd.read_csv('./data/demo_janovska_query.csv', sep='\t')
            content_universe = pd.read_csv('./data/demo_janovska_universe.csv', sep='\t')

        if triggered_id == 'demo-button-2':
            filename_query = 'adipoatlas_query.csv'
            filename_universe = 'adipoatlas_universe.csv'

            content_query = pd.read_csv('./data/adipoatlas_query.csv', sep='\t', header=None)
            content_universe = pd.read_csv('./data/adipoatlas_universe.csv', sep='\t', header=None)

        if triggered_id == 'demo-button-3':
            filename_query = 'Query_Human_Lung_Endothelial_Cells.txt'
            filename_universe = 'Universe_Human_Lung_Endothelial_Cells.txt'

            content_query = pd.read_csv('./data/Query_Human_Lung_Endothelial_Cells.txt', sep='\t')
            content_universe = pd.read_csv('./data/Universe_Human_Lung_Endothelial_Cells.txt', sep='\t')
        
        if triggered_id == 'demo-button-4':
            filename_query = 'Goslin_oxPEq.txt'
            filename_universe = 'Goslin_oxPE.txt'

            content_query = pd.read_csv('./data/Goslin_oxPEq.txt', sep='\t', header=None)
            content_universe = pd.read_csv('./data/Goslin_oxPE.txt', sep='\t', header=None)


        content_query_dict = content_query.to_dict(orient='list')
        content_universe_dict = content_universe.to_dict(orient='list')
        original_data = {'query': content_query_dict, 'universe': content_universe_dict}

        content_query_prepared = prepare_for_parsing(content_query)
        content_query_exchanged = character_exchange_df(content_query_prepared)
        content_universe_exchanged = character_exchange_df(content_universe)

        content_query_exchanged = content_query_exchanged.iloc[:, 0].str.rstrip(' ')
        content_universe_exchanged = content_universe_exchanged.iloc[:, 0].str.rstrip(' ')

        parsed_names_query = convert_table(content_query_exchanged, parser_dropdown, report_path)
        parsed_names_universe = convert_table(content_universe_exchanged, parser_dropdown, report_path)

        df_lipid_parsed_query = parsed_names_query[['Original Name', 'Normalized Name']].fillna('').astype('str')
        df_lipid_parsed_universe = parsed_names_universe[['Original Name', 'Normalized Name']].fillna('').astype('str')


        ### matching
        df_lipid_matched_query, df_lipid_matched_universe = find_matches(df_lipid_parsed_query, df_lipid_parsed_universe)
        
        # query - preparation
        df_lipid_prepared_query = get_prepared_table_data(df_lipid_matched_query)

        # universe - preparation
        df_lipid_prepared_universe = get_prepared_table_data(df_lipid_matched_universe)


        ### messages
        message_query = get_message(df_lipid_prepared_query)
        message_universe = get_message(df_lipid_prepared_universe)
        

        ### tables
        table_query = table_update_query_and_universe_output(df_lipid_prepared_query)
        table_universe = table_update_query_and_universe_output(df_lipid_prepared_universe)

        ###  data storage
        df_lipid_parsed_query_data = prepare_for_storing(parsed_names_query)
        df_lipid_parsed_universe_data = prepare_for_storing(parsed_names_universe)
        
        ### alerts
        alert_query = dbc.Alert(
            [
                html.H6(message_query, style={'color':'#b50800'}),
                html.P('Total number of rows is: ' + str(len(df_lipid_prepared_query.index)), style={'margin':0})
            ], style={'borderColor':'rgba(0,0,0,.125)',}, color='#EEEEEE')
        
        alert_universe = dbc.Alert(
            [
                html.H6(message_universe, style={'color':'#b50800'}),
                html.P('Total number of rows is: ' + str(len(df_lipid_prepared_universe.index)), style={'margin':0})
            ], style={'borderColor':'rgba(0,0,0,.125)',}, color='#EEEEEE')

        return table_query, table_universe, alert_query, alert_universe, df_lipid_parsed_query_data.to_dict('records'), df_lipid_parsed_universe_data.to_dict('records'), original_data

    if contents_query is not None and contents_universe is not None and parser_dropdown == 'LIPID':        
        
        content_query = parse_contents(contents_query, filename_query)
        content_universe = parse_contents(contents_universe, filename_universe)

        content_query_dict = content_query.to_dict(orient='list')
        content_universe_dict = content_universe.to_dict(orient='list')
        original_data = {'query': content_query_dict, 'universe': content_universe_dict}

        content_query_prepared = prepare_for_parsing(content_query)
        content_query_exchanged = character_exchange_df(content_query_prepared)
        content_universe_exchanged = character_exchange_df(content_universe)

        content_query_exchanged = content_query_exchanged.iloc[:, 0].str.rstrip(' ') 
        content_universe_exchanged = content_universe_exchanged.iloc[:, 0].str.rstrip(' ')

        parsed_names_query = convert_table(content_query_exchanged, parser_dropdown, report_path)
        parsed_names_universe = convert_table(content_universe_exchanged, parser_dropdown, report_path)

        df_lipid_parsed_query = parsed_names_query[['Original Name', 'Normalized Name']].fillna('').astype('str')
        df_lipid_parsed_universe = parsed_names_universe[['Original Name', 'Normalized Name']].fillna('').astype('str')


        ### matching
        df_lipid_matched_query, df_lipid_matched_universe = find_matches(df_lipid_parsed_query, df_lipid_parsed_universe)
        
        # query - preparation
        df_lipid_prepared_query = get_prepared_table_data(df_lipid_matched_query)

        # universe - preparation
        df_lipid_prepared_universe = get_prepared_table_data(df_lipid_matched_universe)


        ### messages
        message_query = get_message(df_lipid_prepared_query)
        message_universe = get_message(df_lipid_prepared_universe)
        

        ### tables
        table_query = table_update_query_and_universe_output(df_lipid_prepared_query)
        table_universe = table_update_query_and_universe_output(df_lipid_prepared_universe)


        ###  data storage
        df_lipid_parsed_query_data = prepare_for_storing(parsed_names_query)
        df_lipid_parsed_universe_data = prepare_for_storing(parsed_names_universe)

        
        ### alerts
        alert_query = dbc.Alert(
            [
                html.H6(message_query, style={'color':'#b50800'}),
                html.P('Total number of rows is: ' + str(len(df_lipid_prepared_query.index)), style={'margin':0})
            ], style={'borderColor':'rgba(0,0,0,.125)',}, color='#EEEEEE')
        
        alert_universe = dbc.Alert(
            [
                html.H6(message_universe, style={'color':'#b50800'}),
                html.P('Total number of rows is: ' + str(len(df_lipid_prepared_universe.index)), style={'margin':0})
            ], style={'borderColor':'rgba(0,0,0,.125)',}, color='#EEEEEE')

        return table_query, table_universe, alert_query, alert_universe, df_lipid_parsed_query_data.to_dict('records'), df_lipid_parsed_universe_data.to_dict('records'), original_data

    if (triggered_id == 'demo-button-1' or 
        triggered_id == 'demo-button-2' or 
        triggered_id == 'demo-button-3' or 
        triggered_id == 'demo-button-4') and contents_query is None and contents_universe is None and (parser_dropdown == 'GOSLIN' or 
                                                                                                       parser_dropdown == 'SHORTHAND2020' or
                                                                                                       parser_dropdown == 'LIPIDMAPS' or
                                                                                                       parser_dropdown == 'SWISSLIPIDS' or
                                                                                                       parser_dropdown == 'HMDB'):
        if triggered_id == 'demo-button-1':
            filename_query = 'demo_janovska_query.csv'
            filename_universe = 'demo_janovska_universe.csv'

            content_query = pd.read_csv('./data/demo_janovska_query.csv', sep='\t')
            content_universe = pd.read_csv('./data/demo_janovska_universe.csv', sep='\t')

        if triggered_id == 'demo-button-2':
            filename_query = 'adipoatlas_query.csv'
            filename_universe = 'adipoatlas_universe.csv'

            content_query = pd.read_csv('./data/adipoatlas_query.csv', sep='\t', header=None)
            content_universe = pd.read_csv('./data/adipoatlas_universe.csv', sep='\t', header=None)

        if triggered_id == 'demo-button-3':
            filename_query = 'Query_Human_Lung_Endothelial_Cells.txt'
            filename_universe = 'Universe_Human_Lung_Endothelial_Cells.txt'

            content_query = pd.read_csv('./data/Query_Human_Lung_Endothelial_Cells.txt', sep='\t')
            content_universe = pd.read_csv('./data/Universe_Human_Lung_Endothelial_Cells.txt', sep='\t')
        
        if triggered_id == 'demo-button-4':
            filename_query = 'Goslin_oxPEq.txt'
            filename_universe = 'Goslin_oxPE.txt'

            content_query = pd.read_csv('./data/Goslin_oxPEq.txt', sep='\t', header=None)
            content_universe = pd.read_csv('./data/Goslin_oxPE.txt', sep='\t', header=None)


        content_query_dict = content_query.to_dict(orient='list')
        content_universe_dict = content_universe.to_dict(orient='list')
        original_data = {'query': content_query_dict, 'universe': content_universe_dict}

        content_query_prepared = prepare_for_parsing(content_query)
        content_query_exchanged = character_exchange_df(content_query_prepared)
        content_universe_exchanged = character_exchange_df(content_universe)

        content_query_exchanged = content_query_exchanged.iloc[:, 0].str.rstrip(' ')
        content_universe_exchanged = content_universe_exchanged.iloc[:, 0].str.rstrip(' ')

        parsed_names_query = convert_table(content_query_exchanged, parser_dropdown, report_path)
        parsed_names_universe = convert_table(content_universe_exchanged, parser_dropdown, report_path)


        df_lipid_parsed_query = parsed_names_query[['Original Name', 'Normalized Name']].fillna('').astype('str')
        df_lipid_parsed_universe = parsed_names_universe[['Original Name', 'Normalized Name']].fillna('').astype('str')


        ### matching
        df_lipid_matched_query, df_lipid_matched_universe = find_matches(df_lipid_parsed_query, df_lipid_parsed_universe)
        
        # query - preparation
        df_lipid_prepared_query = get_prepared_table_data(df_lipid_matched_query)

        # universe - preparation
        df_lipid_prepared_universe = get_prepared_table_data(df_lipid_matched_universe)


        ### messages
        message_query = get_message(df_lipid_prepared_query)
        message_universe = get_message(df_lipid_prepared_universe)
        

        ### tables
        table_query = table_update_query_and_universe_output(df_lipid_prepared_query)
        table_universe = table_update_query_and_universe_output(df_lipid_prepared_universe)


        ###  data storage
        df_lipid_parsed_query_data = prepare_for_storing(parsed_names_query)
        df_lipid_parsed_universe_data = prepare_for_storing(parsed_names_universe)

        
        ### alerts
        alert_query = dbc.Alert(
            [
                html.H6(message_query, style={'color':'#b50800'}),
                html.P('Total number of rows is: ' + str(len(df_lipid_prepared_query.index)), style={'margin':0})
            ], style={'borderColor':'rgba(0,0,0,.125)',}, color='#EEEEEE')
        
        alert_universe = dbc.Alert(
            [
                html.H6(message_universe, style={'color':'#b50800'}),
                html.P('Total number of rows is: ' + str(len(df_lipid_prepared_universe.index)), style={'margin':0})
            ], style={'borderColor':'rgba(0,0,0,.125)',}, color='#EEEEEE')

        return table_query, table_universe, alert_query, alert_universe, df_lipid_parsed_query_data.to_dict('records'), df_lipid_parsed_universe_data.to_dict('records'), original_data

    if contents_query is not None and contents_universe is not None and (parser_dropdown == 'GOSLIN' or 
                                                                         parser_dropdown == 'SHORTHAND2020' or
                                                                         parser_dropdown == 'LIPIDMAPS' or
                                                                         parser_dropdown == 'SWISSLIPIDS' or
                                                                         parser_dropdown == 'HMDB'):        
        
        content_query = parse_contents(contents_query, filename_query)
        content_universe = parse_contents(contents_universe, filename_universe)

        content_query_dict = content_query.to_dict(orient='list')
        content_universe_dict = content_universe.to_dict(orient='list')
        original_data = {'query': content_query_dict, 'universe': content_universe_dict}

        content_query_prepared = prepare_for_parsing(content_query)
        content_query_exchanged = character_exchange_df(content_query_prepared)
        content_universe_exchanged = character_exchange_df(content_universe)

        content_query_exchanged = content_query_exchanged.iloc[:, 0].str.rstrip(' ') 
        content_universe_exchanged = content_universe_exchanged.iloc[:, 0].str.rstrip(' ')

        parsed_names_query = convert_table(content_query_exchanged, parser_dropdown, report_path)
        parsed_names_universe = convert_table(content_universe_exchanged, parser_dropdown, report_path)

        df_lipid_parsed_query = parsed_names_query[['Original Name', 'Normalized Name']].fillna('').astype('str')
        df_lipid_parsed_universe = parsed_names_universe[['Original Name', 'Normalized Name']].fillna('').astype('str')


        ### matching
        df_lipid_matched_query, df_lipid_matched_universe = find_matches(df_lipid_parsed_query, df_lipid_parsed_universe)
        
        # query - preparation
        df_lipid_prepared_query = get_prepared_table_data(df_lipid_matched_query)

        # universe - preparation
        df_lipid_prepared_universe = get_prepared_table_data(df_lipid_matched_universe)


        ### messages
        message_query = get_message(df_lipid_prepared_query)
        message_universe = get_message(df_lipid_prepared_universe)
        

        ### tables
        table_query = table_update_query_and_universe_output(df_lipid_prepared_query)
        table_universe = table_update_query_and_universe_output(df_lipid_prepared_universe)


        ###  data storage
        df_lipid_parsed_query_data = prepare_for_storing(parsed_names_query)
        df_lipid_parsed_universe_data = prepare_for_storing(parsed_names_universe)

        
        ### alerts
        alert_query = dbc.Alert(
            [
                html.H6(message_query, style={'color':'#b50800'}),
                html.P('Total number of rows is: ' + str(len(df_lipid_prepared_query.index)), style={'margin':0})
            ], style={'borderColor':'rgba(0,0,0,.125)',}, color='#EEEEEE')
        
        alert_universe = dbc.Alert(
            [
                html.H6(message_universe, style={'color':'#b50800'}),
                html.P('Total number of rows is: ' + str(len(df_lipid_prepared_universe.index)), style={'margin':0})
            ], style={'borderColor':'rgba(0,0,0,.125)',}, color='#EEEEEE')

        return table_query, table_universe, alert_query, alert_universe, df_lipid_parsed_query_data.to_dict('records'), df_lipid_parsed_universe_data.to_dict('records'), original_data

    else:
        raise PreventUpdate



## query jgoslin table checklist without synchronisation
@app.callback(Output('checklist-query-jgoslin', 'options'),
              Input('datatable-query-session', 'data'),
              Input('process-button', 'n_clicks'),
)
def create_jgoslin_checklist(data, n_clicks):
    ctx = callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if n_clicks is None:
        raise PreventUpdate
    
    if input_id == 'datatable-query-session':
        return []
    
    if input_id == 'process-button':

        df = pd.DataFrame(data)
        df = separate_db_position_geometry(df)

        df_columns = df.columns
        columns_to_drop = [x for x in df_columns if x.startswith('Lipid Shorthand')]
        df = df.drop(columns=columns_to_drop)
    
        options = []
        for column in df.columns:
            new_option = {'label': column, 'value': column, 'disabled': True}
            options = options + [new_option]

        return options
    


## query jgoslin table checklist without synchronisation
@app.callback(Output('checklist-universe-jgoslin', 'options'),
              Input('datatable-universe-session', 'data'),
              Input('process-button', 'n_clicks'),
)
def create_jgoslin_checklist(data, n_clicks):
    ctx = callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if n_clicks is None:
        raise PreventUpdate
    
    if input_id == 'datatable-universe-session':
        return []
    
    if input_id == 'process-button':

        df = pd.DataFrame(data)
        df = separate_db_position_geometry(df)

        df_columns = df.columns
        columns_to_drop = [x for x in df_columns if x.startswith('Lipid Shorthand')]
        df = df.drop(columns=columns_to_drop)
    
        options = []
        for column in df.columns:
            new_option = {'label': column, 'value': column, 'disabled': True}
            options = options + [new_option]

        return options



### tab-2 message
@app.callback(Output('alert-process-button', 'children'),
              Input('datatable-query-session', 'data'),
              Input('datatable-universe-session', 'data'),
              Input('tab-2', 'value'),
)
def display_message(data_query, data_universe, value):
    if value == 'tab-2':
        df_query = pd.DataFrame(data_query)
        df_universe = pd.DataFrame(data_universe)

        message = [
            html.B('The number of lipids to parse is ' + str(len(df_query.index)) + ' for query and ' + str(len(df_universe.index)) + ' for reference lipidome. ', style={'margin-bottom':0}),
            html.P([
                html.P('For further processing, please click on the ', style={'display':'contents'}),
                html.B('Process', style={'display':'contents'}),
                html.P(' button.', style={'display':'contents'}),
            ], style={'margin-bottom':'1rem'}),
            ]

        return message
    else:
        raise PreventUpdate



### tab-2 message visibility
@app.callback(Output('div-process-button', 'style'),
              Input('process-button', 'n_clicks'),
              Input('datatable-query-session', 'data'),
)
def display_message_vis(n_clicks, dt_query_session):

    ctx = callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if input_id == 'datatable-query-session':
         return {'display':'flex', 'justify-content': 'center', 'align-items':'center'}
    if input_id == 'process-button':
        return {'display':'none'}
    else: 
        raise PreventUpdate



### query row style
@app.callback(Output('query-jgoslin-row', 'style'),
              Output('div-query-process-container', 'style'),
              Output('query-jgoslin-table-header', 'style'),
              Input('query-process-container', 'children'),
              Input('datatable-query-session', 'data'),
)
def row_style(query_process_container, dt_query_session):

    ctx = callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if input_id == 'datatable-query-session':
        return {}, {'display':'none'}, {'display':'none'}
    if query_process_container is not None:
        return {'margin':'1em 0 2em 0', 'padding':'1em 0 1em 0'}, {'background-color':'#eeeeee', 'border': '1px solid rgba(0,0,0,.125)', 'border-radius': '.25rem', 'margin-bottom': '1rem'}, {'display':'block'}
    else:
        raise PreventUpdate



### universe row style
@app.callback(Output('universe-jgoslin-row', 'style'),
              Output('div-universe-process-container', 'style'),
              Output('universe-jgoslin-table-header', 'style'),
              Input('universe-process-container', 'children'),
              Input('datatable-universe-session', 'data'),
)
def row_style(universe_process_container, dt_universe_session):

    ctx = callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if input_id == 'datatable-universe-session':
        return {}, {'display':'none'}, {'display':'none'}
    if universe_process_container is not None:
        return {'margin':'1em 0 2em 0', 'padding':'1em 0 1em 0'}, {'background-color':'#eeeeee', 'border': '1px solid rgba(0,0,0,.125)', 'border-radius': '.25rem'}, {'display':'block'}
    else:
        raise PreventUpdate



### query parsed jgoslin table 
@app.callback(Output('query-process-container', 'children'),
              Output('FA-options', 'data'),
              Output('parameters-dynamic-checklist', 'data'),
              Input('process-button', 'n_clicks'),
              Input('datatable-query-session', 'data'),
              #Input('checklist-query-jgoslin', 'value'),
)
def create_jgoslin_table(n_clicks, data_query):

    #print(checklist_value_query)
    
    if n_clicks is None:
        raise PreventUpdate 

    else:
        df_final_query = pd.DataFrame(data_query)
        df_final_query = separate_db_position_geometry(df_final_query)

        df_columns = df_final_query.columns
        columns_to_drop = [x for x in df_columns if x.startswith('Lipid Shorthand')]
        df_final_query = df_final_query.drop(columns=columns_to_drop)
        
        parameters = df_final_query.columns

        #df_final_query = df_final_query.loc[:, df_final_query.columns.isin(checklist_value_query)]

        FA_otpions = get_FA_options(df_final_query)


        # custom width for each column query
        long_column_names = [{"if": {"column_id": column}, "min-width": "350px"} for column in df_final_query.columns if len(column) >= 30]
        med_column_names = [{"if": {"column_id": column}, "min-width": "250px"} for column in df_final_query.columns if (len(column) > 15 and len(column)) < 30]
        small_column_names = [{"if": {"column_id": column}, "min-width": "150px"} for column in df_final_query.columns if len(column) <= 15]

        adjusted_columns = long_column_names + med_column_names + small_column_names


        table_query = dash_table.DataTable(
                    df_final_query.to_dict('records'), 
                    [{"name": i, "id": i} for i in df_final_query.columns],
                    style_data={
                        'whiteSpace': 'normal',
                        'lineHeight': '20px',
                        'border': 'none'
                    },
                    style_cell={
                        'font_family': 'sans-serif',
                        'font_size': '12px',
                    },
                    style_as_list_view=True,
                    style_header={'backgroundColor': '#0053b5', 'color': 'white', 'fontWeight': 'bold', 'border-bottom': '2px solid #0053b5'},
                    style_table={'height': '740px', 'maxHeight': '740px'},
                    fixed_rows={'headers': True},
                    style_cell_conditional=adjusted_columns,
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': '#EEEEEE',
                        }],
                    sort_action='native',
                    sort_mode='multi',
                    sort_as_null=['', 'No'],
                    sort_by=[{'column_id': 'Normalized name', 'direction': 'asc'}],
                    editable=True,
                    css=[{'selector': 'p', 'rule': 'margin: 0; text-align: right; font-family: monospace'}]
                    )

        return table_query, FA_otpions, parameters


### universe parsed jgoslin table 
@app.callback(Output('universe-process-container', 'children'),
              Input('process-button', 'n_clicks'),
              Input('datatable-universe-session', 'data'),
              #Input('checklist-universe-jgoslin', 'value')
)
def create_jgoslin_table(n_clicks, data_universe):
    
    if n_clicks is None:
        raise PreventUpdate 

    else:
        df_final_universe = pd.DataFrame(data_universe)
        df_final_universe = separate_db_position_geometry(df_final_universe)

        #df_final_universe = df_final_universe.loc[:, df_final_universe.columns.isin(checklist_value_universe)]

        df_columns = df_final_universe.columns
        columns_to_drop = [x for x in df_columns if x.startswith('Lipid Shorthand')]
        df_final_universe = df_final_universe.drop(columns=columns_to_drop)
    
        # custom width for each column query
        long_column_names = [{"if": {"column_id": column}, "min-width": "350px"} for column in df_final_universe.columns if len(column) >= 30]
        med_column_names = [{"if": {"column_id": column}, "min-width": "250px"} for column in df_final_universe.columns if (len(column) > 15 and len(column)) < 30]
        small_column_names = [{"if": {"column_id": column}, "min-width": "150px"} for column in df_final_universe.columns if len(column) <= 15]

        adjusted_columns = long_column_names + med_column_names + small_column_names

        table_universe = dash_table.DataTable(
                    df_final_universe.to_dict('records'), 
                    [{"name": i, "id": i} for i in df_final_universe.columns],
                    style_data={
                        'whiteSpace': 'normal',
                        'lineHeight': '20px',
                        'border': 'none'
                    },
                    style_cell={
                        'font_family': 'sans-serif',
                        'font_size': '12px',
                    },
                    style_as_list_view=True,
                    style_header={'backgroundColor': '#0053b5', 'color': 'white', 'fontWeight': 'bold', 'border-bottom': '2px solid #0053b5'},
                    style_table={'height': '800px', 'maxHeight': '800px'},
                    fixed_rows={'headers': True},
                    style_cell_conditional=adjusted_columns,
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': '#EEEEEE',
                        }],
                    sort_action='native',
                    sort_mode='multi',
                    sort_as_null=['', 'No'],
                    sort_by=[{'column_id': 'Normalized name', 'direction': 'asc'}],
                    editable=True,
                    css=[{'selector': 'p', 'rule': 'margin: 0; text-align: right; font-family: monospace'}]
                    )

        return table_universe
          


### RadioItems disable/enable while performing action
@app.callback(
    Output('radioitems-alternative', 'style'),
    Input('statistical-test-dropdown', 'value'),
)
def disabled_radioitems(value):
    if value == 'Fisher exact test':
        return {'display':'block'}
    if value == 'Hypergeometric':
        return {'display':'none'}



### process button callback
@app.callback(
    Output('output-select-message', 'children'),
    Input('enrichment-button', 'n_clicks'),
)
def display_select_message(n_clicks):
    if n_clicks is None:
        return html.P('Select the required parameters and submit', style={'color':'#b3b3b3', 'padding-bottom':'1rem'})
    if n_clicks is not None:
        return []



### process button callback - disabled
@app.callback(
    Output('enrichment-button', 'disabled'),
    Input('alpha-level-input', 'value'),
)
def process_button_disabled(alpha_level):
    if alpha_level is not None:
        return False
    else:
        raise PreventUpdate



### generate dynamicaly checklist for paramters selection
@app.callback(
    Output('parameters-checklist', 'value'),
    Output('parameters-checklist', 'options'),
    Input('parameters-dynamic-checklist', 'data')
)
def generate_param_checklist(data):
    data_sliced = data[10:]
    data_final = data_sliced + ['Acyls']
    return data_final, data_final



### statistics - Fisher exact test + Hypergeometric - Checklist
@app.callback(
    Output('enrichment-container', 'children'),
    Output('enrichment-container-session', 'data'),
    Output('basic-interactions', 'figure'),
    Output('enrichment-analysis-column-container', 'style'),
    Output('vil-table-container', 'children'),
    Output('basic-interactions-session', 'data'),
    Output('enrichment-button', 'n_clicks'),
    Output('VIL_table_session', 'data'),
    Output('all_results_session', 'data'),
    State('enrichment-checklist', 'value'),
    State('enrichment-checklist-subset', 'value'),
    Input('datatable-query-session', 'data'),
    Input('datatable-universe-session', 'data'),
    Input('enrichment-button', 'n_clicks'),
    State('radioitems-alternative', 'value'),
    State('parameters-checklist', 'value'),
    State('statistical-method-dropdown', 'value'),
    State('alpha-level-input', 'value'),
    State('statistical-test-dropdown', 'value'),
    State('filter-enrichment', 'value'),
    State('filter-count', 'value'),
)
def create_table_statistics(checklist, checklist_subset, data_query, data_universe, n_clicks, radio_item, param_checklist, statistical_method, alpha_level, statistical_test, filter, filter_count):

    ctx = callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]

    session_id = flask.session['session_id']

    carbon_options = ['acyls containing less than 16 carbon atoms', 'acyls containing 16-18 carbon atoms', 'acyls containing more than 18 carbon atoms']
    double_bond_options = ['acyls containing 0 double bonds (saturated)', 'acyls containing 1 double bonds (monounsaturated)', 'acyls containing 2 or more double bonds (polyunsaturated)']

    if n_clicks is None:
        raise PreventUpdate
    
    elif input_id == 'datatable-query-session':
        return [], {}, {}, {'display':'none'}, [], {}, None, {}

    elif input_id == 'enrichment-button' and len(checklist) != 0 and len(checklist_subset) == 0 and len(param_checklist) == 0 and statistical_test == 'Fisher exact test':

        df_query_final = separate_db_position_geometry(pd.DataFrame(data_query))
        df_universe_final = separate_db_position_geometry(pd.DataFrame(data_universe))

        # Calculate enrichment using Fisher's exact test
        if checklist == ['Acyls']:
            df = calculate_enrichment_fisher(checklist, get_FA_df(df_query_final), get_FA_df(df_universe_final), radio_item, statistical_method, alpha_level, filter_count)

        elif 'Acyls' in checklist:
            excluded_list = [item for item in checklist if item != 'Acyls']
            dfs_to_concat = []
            dfs_to_concat.append(calculate_enrichment_fisher(excluded_list, df_query_final, df_universe_final, radio_item, statistical_method, alpha_level, filter_count))
            dfs_to_concat.append(calculate_enrichment_fisher(['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), radio_item, statistical_method, alpha_level, filter_count))
            df = pd.concat(dfs_to_concat)

        elif 'Acyls' not in checklist:    
            df = calculate_enrichment_fisher(checklist, df_query_final, df_universe_final, radio_item, statistical_method, alpha_level, filter_count)

        # Clean up data and apply filters
        df['p-value'] = df['p-value'].apply(lambda x: edit_pval(x))
        df['Term (Classifier)'] = df['Term (Classifier)'].apply(lambda x: int(x) if isinstance(x, float) else x)
        df['Term (Classifier)'] = df['Term (Classifier)'].astype(str)

        df_all_results = df

        if filter == ['Filter statistically significant results']:
            try:
                df = df[df['Hypothesis Correction Result'] == True]
            except Exception as e:
                print(f'Error when filtering statically significant values: {e}')

        # Select statistically significant results
        df_get_sig = df[df['Hypothesis Correction Result'] == True].copy()
        df_get_sig['p-value'] = pd.to_numeric(df_get_sig['p-value'], errors='ignore', downcast='float')

        LIM_MAX = df_get_sig['p-value'].max()

        # Create upset plot
        upset_df = table_for_upset(df_get_sig, df_query_final)

        if len(df.index) < 2:
            fig = go.Figure()
            fig.add_annotation(
                text="Not enough data to plot a figure, the condition needs to be loosen.",
                font={"size": 16},
                showarrow=False
            )
            fig_dict = {}
            VIL = pd.DataFrame()

        if len(df.index) >= 2 and len(df.index) < 13:
            original_df, df_to_plot, subsets, fig_dict, VIL = plotly_upset_plot_pivot(upset_df, LIM_MAX)
            fig = plotly_upset_figure(df_to_plot, original_df, subsets, LIM_MAX) 
            fig.update_layout(clickmode='event+select')

        if len(df.index) >= 13:    
            original_df, df_to_plot, subsets, fig_dict, VIL = plotly_upset_plot_pivot(upset_df, LIM_MAX)
            fig = plotly_upset_figure(df_to_plot, original_df, subsets, LIM_MAX) 
            fig.update_layout(clickmode='event+select')
        
        cache.set('upset_fig_'+session_id, fig)

        table = table_create_table_statistics(df)

        VIL_table = vil_table(VIL)

        return table, df.to_dict('records'), fig, {'visibility':'visible', 'display':'block'}, VIL_table, fig_dict, n_clicks, VIL, df_all_results.to_dict('records')

    elif input_id == 'enrichment-button' and len(checklist) == 0 and len(checklist_subset) != 0 and len(param_checklist) != 0 and statistical_test == 'Fisher exact test':

        df_query_final = separate_db_position_geometry(pd.DataFrame(data_query))
        df_universe_final = separate_db_position_geometry(pd.DataFrame(data_universe))

        if param_checklist == ['Acyls']:
            df = calculate_enrichment_within_subset_fisher(checklist_subset, ['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), radio_item, statistical_method, alpha_level, filter_count)

        elif 'Acyls' in param_checklist:
            excluded_list = [item for item in param_checklist if item != 'Acyls']
            dfs_to_concat = []

            if 'Total #C' not in excluded_list and 'Total #DB' not in excluded_list:
                dfs_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, excluded_list, df_query_final, df_universe_final, radio_item, statistical_method, alpha_level, filter_count))
                dfs_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, ['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), radio_item, statistical_method, alpha_level, filter_count))

            if 'Total #C' not in excluded_list and 'Total #DB' in excluded_list:
                dfs_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, excluded_list, df_query_final, df_universe_final, radio_item, statistical_method, alpha_level, filter_count))
                dfs_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, ['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), radio_item, statistical_method, alpha_level, filter_count))
                df_list = [calculate_enrichment_fisher_advanced(checklist_subset, df_query_final, df_universe_final, radio_item, 'DOUBLE BONDS', double_bond_option, statistical_method, alpha_level, filter_count) for double_bond_option in double_bond_options]
                dfs_to_concat.extend(df_list)

            if 'Total #DB' not in excluded_list and 'Total #C' in excluded_list:
                dfs_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, excluded_list, df_query_final, df_universe_final, radio_item, statistical_method, alpha_level, filter_count))
                dfs_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, ['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), radio_item, statistical_method, alpha_level, filter_count))
                df_list = [calculate_enrichment_fisher_advanced(checklist_subset, df_query_final, df_universe_final, radio_item, 'CARBONS', carbon_option, statistical_method, alpha_level, filter_count) for carbon_option in carbon_options]
                dfs_to_concat.extend(df_list)
            
            if 'Total #C' in excluded_list and 'Total #DB' in excluded_list:
                dfs_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, excluded_list, df_query_final, df_universe_final, radio_item, statistical_method, alpha_level, filter_count))
                dfs_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, ['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), radio_item, statistical_method, alpha_level, filter_count))
                df_list_carbons = [calculate_enrichment_fisher_advanced(checklist_subset, df_query_final, df_universe_final, radio_item, 'CARBONS', carbon_option, statistical_method, alpha_level, filter_count) for carbon_option in carbon_options]
                dfs_to_concat.extend(df_list_carbons)
                df_list_db = [calculate_enrichment_fisher_advanced(checklist_subset, df_query_final, df_universe_final, radio_item, 'DOUBLE BONDS', double_bond_option, statistical_method, alpha_level, filter_count) for double_bond_option in double_bond_options]
                dfs_to_concat.extend(df_list_db)
            
            df = pd.concat(dfs_to_concat)

        else:
            dfs_to_concat = []

            if 'Total #C' not in param_checklist and 'Total #DB' not in param_checklist:
                df = calculate_enrichment_within_subset_fisher(checklist_subset, param_checklist, df_query_final, df_universe_final, radio_item, statistical_method, alpha_level, filter_count)

            if 'Total #C' not in param_checklist and 'Total #DB' in param_checklist:
                dfs_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, param_checklist, df_query_final, df_universe_final, radio_item, statistical_method, alpha_level, filter_count))
                df_list = [calculate_enrichment_fisher_advanced(checklist_subset, df_query_final, df_universe_final, radio_item, 'DOUBLE BONDS', double_bond_option, statistical_method, alpha_level, filter_count) for double_bond_option in double_bond_options]
                dfs_to_concat.extend(df_list)

            if 'Total #DB' not in param_checklist and 'Total #C' in param_checklist:
                dfs_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, param_checklist, df_query_final, df_universe_final, radio_item, statistical_method, alpha_level, filter_count))            
                df_list = [calculate_enrichment_fisher_advanced(checklist_subset, df_query_final, df_universe_final, radio_item, 'CARBONS', carbon_option, statistical_method, alpha_level, filter_count) for carbon_option in carbon_options]
                dfs_to_concat.extend(df_list)
            
            if 'Total #C' in param_checklist and 'Total #DB' in param_checklist:
                dfs_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, param_checklist, df_query_final, df_universe_final, radio_item, statistical_method, alpha_level, filter_count))
                df_list_carbons = [calculate_enrichment_fisher_advanced(checklist_subset, df_query_final, df_universe_final, radio_item, 'CARBONS', carbon_option, statistical_method, alpha_level, filter_count) for carbon_option in carbon_options]
                dfs_to_concat.extend(df_list_carbons)
                df_list_db = [calculate_enrichment_fisher_advanced(checklist_subset, df_query_final, df_universe_final, radio_item, 'DOUBLE BONDS', double_bond_option, statistical_method, alpha_level, filter_count) for double_bond_option in double_bond_options]
                dfs_to_concat.extend(df_list_db)

            df = pd.concat(dfs_to_concat)

        df['p-value'] = df['p-value'].apply(lambda x: edit_pval(x))
        df['Term (Classifier)'] = df['Term (Classifier)'].apply(lambda x: int(x) if isinstance(x, float) else x)
        df['Term (Classifier)'] = df['Term (Classifier)'].astype(str)

        df_all_results = df

        if filter == ['Filter statistically significant results']:
            try:
                df = df[df['Hypothesis Correction Result'] == True]
            except Exception as e:
                print(f'Error when filtering statically significant values: {e}')

        df_get_sig = df[df['Hypothesis Correction Result'] == True].copy()
        df_get_sig['p-value'] = pd.to_numeric(df_get_sig['p-value'], errors='ignore', downcast='float')

        LIM_MAX = df_get_sig['p-value'].max()

        upset_df = table_for_upset(df_get_sig, df_query_final)

        if len(df.index) < 2:
            fig = go.Figure()
            fig.add_annotation(
                text="Not enough data to plot a figure, the condition needs to be loosen.",
                font={"size": 16},
                showarrow=False
            )
            fig_dict = {}
            VIL = pd.DataFrame()
        
        if len(df.index) >= 2 and len(df.index) < 13:
            original_df, df_to_plot, subsets, fig_dict, VIL = plotly_upset_plot_pivot(upset_df, LIM_MAX)
            fig = plotly_upset_figure(df_to_plot, original_df, subsets, LIM_MAX) 
            fig.update_layout(clickmode='event+select')

        if len(df.index) >= 13:    
            original_df, df_to_plot, subsets, fig_dict, VIL = plotly_upset_plot_pivot(upset_df, LIM_MAX)
            fig = plotly_upset_figure(df_to_plot, original_df, subsets, LIM_MAX) 
            fig.update_layout(clickmode='event+select')

        cache.set('upset_fig_'+session_id, fig)    

        table = table_create_table_statistics(df)

        VIL_table = vil_table(VIL)

        return table, df.to_dict('records'), fig, {'visibility':'visible', 'display':'block'}, VIL_table, fig_dict, n_clicks, VIL, df_all_results.to_dict('records')

    elif input_id == 'enrichment-button' and len(checklist) != 0 and len(checklist_subset) != 0 and len(param_checklist) != 0 and statistical_test == 'Fisher exact test':

        df_query_final = separate_db_position_geometry(pd.DataFrame(data_query))
        df_universe_final = separate_db_position_geometry(pd.DataFrame(data_universe))

        if checklist == ['Acyls']:
            df_general = calculate_enrichment_fisher(checklist, get_FA_df(df_query_final), get_FA_df(df_universe_final), radio_item, statistical_method, alpha_level, filter_count)
        
        elif 'Acyls' in checklist:
            excluded_list = [item for item in checklist if item != 'Acyls']
            dfs_general_to_concat = []
            dfs_general_to_concat.append(calculate_enrichment_fisher(excluded_list, df_query_final, df_universe_final, radio_item, statistical_method, alpha_level, filter_count))
            dfs_general_to_concat.append(calculate_enrichment_fisher(['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), radio_item, statistical_method, alpha_level, filter_count))
            df_general = pd.concat(dfs_general_to_concat)

        else:
            df_general = calculate_enrichment_fisher(checklist, df_query_final, df_universe_final, radio_item, statistical_method, alpha_level, filter_count)


        if param_checklist == ['Acyls']:
            df_subset = calculate_enrichment_within_subset_fisher(checklist_subset, ['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), radio_item, statistical_method, alpha_level, filter_count)

        elif 'Acyls' in param_checklist:
            excluded_list = [item for item in param_checklist if item != 'Acyls']
            dfs_subset_to_concat = []

            if 'Total #C' not in excluded_list and 'Total #DB' not in excluded_list:
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, excluded_list, df_query_final, df_universe_final, radio_item, statistical_method, alpha_level, filter_count))
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, ['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), radio_item, statistical_method, alpha_level, filter_count))

            elif 'Total #C' not in excluded_list and 'Total #DB' in excluded_list:
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, excluded_list, df_query_final, df_universe_final, radio_item, statistical_method, alpha_level, filter_count))
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, ['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), radio_item, statistical_method, alpha_level, filter_count))
                df_list = [calculate_enrichment_fisher_advanced(checklist_subset, df_query_final, df_universe_final, radio_item, 'DOUBLE BONDS', double_bond_option, statistical_method, alpha_level, filter_count) for double_bond_option in double_bond_options]
                dfs_subset_to_concat.extend(df_list)

            elif 'Total #DB' not in excluded_list and 'Total #C' in excluded_list:
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, excluded_list, df_query_final, df_universe_final, radio_item, statistical_method, alpha_level, filter_count))
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, ['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), radio_item, statistical_method, alpha_level, filter_count))
                df_list = [calculate_enrichment_fisher_advanced(checklist_subset, df_query_final, df_universe_final, radio_item, 'CARBONS', carbon_option, statistical_method, alpha_level, filter_count) for carbon_option in carbon_options]
                dfs_subset_to_concat.extend(df_list)
            
            elif 'Total #C' in excluded_list and 'Total #DB' in excluded_list:
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, excluded_list, df_query_final, df_universe_final, radio_item, statistical_method, alpha_level, filter_count))
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, ['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), radio_item, statistical_method, alpha_level, filter_count))
                df_list_carbons = [calculate_enrichment_fisher_advanced(checklist_subset, df_query_final, df_universe_final, radio_item, 'CARBONS', carbon_option, statistical_method, alpha_level, filter_count) for carbon_option in carbon_options]
                dfs_subset_to_concat.extend(df_list_carbons)
                df_list_db = [calculate_enrichment_fisher_advanced(checklist_subset, df_query_final, df_universe_final, radio_item, 'DOUBLE BONDS', double_bond_option, statistical_method, alpha_level, filter_count) for double_bond_option in double_bond_options]
                dfs_subset_to_concat.extend(df_list_db)
            
            df_subset = pd.concat(dfs_subset_to_concat)

        else:
            dfs_subset_to_concat = []

            if 'Total #C' not in param_checklist and 'Total #DB' not in param_checklist:
                df_subset = calculate_enrichment_within_subset_fisher(checklist_subset, param_checklist, df_query_final, df_universe_final, radio_item, statistical_method, alpha_level, filter_count)

            elif 'Total #C' not in param_checklist and 'Total #DB' in param_checklist:
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, param_checklist, df_query_final, df_universe_final, radio_item, statistical_method, alpha_level, filter_count))
                df_list = [calculate_enrichment_fisher_advanced(checklist_subset, df_query_final, df_universe_final, radio_item, 'DOUBLE BONDS', double_bond_option, statistical_method, alpha_level, filter_count) for double_bond_option in double_bond_options]
                dfs_subset_to_concat.extend(df_list)

            elif 'Total #DB' not in param_checklist and 'Total #C' in param_checklist:
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, param_checklist, df_query_final, df_universe_final, radio_item, statistical_method, alpha_level, filter_count))
                df_list = [calculate_enrichment_fisher_advanced(checklist_subset, df_query_final, df_universe_final, radio_item, 'CARBONS', carbon_option, statistical_method, alpha_level, filter_count) for carbon_option in carbon_options]
                dfs_subset_to_concat.extend(df_list)
            
            elif 'Total #C' in param_checklist and 'Total #DB' in param_checklist:
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_fisher(checklist_subset, param_checklist, df_query_final, df_universe_final, radio_item, statistical_method, alpha_level, filter_count))
                df_list_carbons = [calculate_enrichment_fisher_advanced(checklist_subset, df_query_final, df_universe_final, radio_item, 'CARBONS', carbon_option, statistical_method, alpha_level, filter_count) for carbon_option in carbon_options]
                dfs_subset_to_concat.extend(df_list_carbons)
                df_list_db = [calculate_enrichment_fisher_advanced(checklist_subset, df_query_final, df_universe_final, radio_item, 'DOUBLE BONDS', double_bond_option, statistical_method, alpha_level, filter_count) for double_bond_option in double_bond_options]
                dfs_subset_to_concat.extend(df_list_db)
                
            df_subset = pd.concat(dfs_subset_to_concat)

        df = pd.concat([df_general, df_subset])

        df['p-value'] = df['p-value'].apply(lambda x: edit_pval(x))
        df['Term (Classifier)'] = df['Term (Classifier)'].apply(lambda x: int(x) if isinstance(x, float) else x)
        df['Term (Classifier)'] = df['Term (Classifier)'].astype(str)

        df_all_results = df
            
        if filter == ['Filter statistically significant results']:
            try:
                df = df[df['Hypothesis Correction Result'] == True]
            except Exception as e:
                print(f'Error when filtering statically significant values: {e}')

        df_get_sig = df[df['Hypothesis Correction Result'] == True].copy()
        df_get_sig['p-value'] = pd.to_numeric(df_get_sig['p-value'], errors='ignore', downcast='float')

        LIM_MAX = df_get_sig['p-value'].max()

        upset_df = table_for_upset(df_get_sig, df_query_final)

        if len(df.index) < 2:
            fig = go.Figure()
            fig.add_annotation(
                text="Not enough data to plot a figure, the condition needs to be loosen.",
                font={"size": 16},
                showarrow=False
            )
            fig_dict = {}
            VIL = pd.DataFrame()

        if len(df.index) >= 2 and len(df.index) < 13:
            original_df, df_to_plot, subsets, fig_dict, VIL = plotly_upset_plot_pivot(upset_df, LIM_MAX)
            fig = plotly_upset_figure(df_to_plot, original_df, subsets, LIM_MAX) 
            fig.update_layout(clickmode='event+select')

        if len(df.index) >= 13:    
            original_df, df_to_plot, subsets, fig_dict, VIL = plotly_upset_plot_pivot(upset_df, LIM_MAX)
            fig = plotly_upset_figure(df_to_plot, original_df, subsets, LIM_MAX) 
            fig.update_layout(clickmode='event+select')

        cache.set('upset_fig_'+session_id, fig)

        table = table_create_table_statistics(df)

        VIL_table = vil_table(VIL)

        return table, df.to_dict('records'), fig, {'visibility':'visible', 'display':'block'}, VIL_table, fig_dict, n_clicks, VIL, df_all_results.to_dict('records')
    
    elif input_id == 'enrichment-button' and len(checklist) !=0 and len(checklist_subset) == 0 and len(param_checklist) == 0 and statistical_test == 'Hypergeometric':
        
        df_query_final = separate_db_position_geometry(pd.DataFrame(data_query))
        df_universe_final = separate_db_position_geometry(pd.DataFrame(data_universe))

        if checklist == ['Acyls']:
            df = calculate_enrichment_hypergeom(checklist, get_FA_df(df_query_final), get_FA_df(df_universe_final), statistical_method, alpha_level, filter_count)

        elif 'Acyls' in checklist:
            excluded_list = [item for item in checklist if item != 'Acyls']
            dfs_to_concat = []
            dfs_to_concat.append(calculate_enrichment_hypergeom(excluded_list, df_query_final, df_universe_final, statistical_method, alpha_level, filter_count))
            dfs_to_concat.append(calculate_enrichment_hypergeom(['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), statistical_method, alpha_level, filter_count))
            df = pd.concat(dfs_to_concat)

        elif 'Acyls' not in checklist:    
            df = calculate_enrichment_hypergeom(checklist, df_query_final, df_universe_final, statistical_method, alpha_level, filter_count)

        df['p-value'] = df['p-value'].apply(lambda x: edit_pval(x))
        df['Term (Classifier)'] = df['Term (Classifier)'].apply(lambda x: int(x) if isinstance(x, float) else x)
        df['Term (Classifier)'] = df['Term (Classifier)'].astype(str)
        
        df_all_results = df

        if filter == ['Filter statistically significant results']:
            try:
                df = df[df['Hypothesis Correction Result'] == True]
            except Exception as e:
                print(f'Error when filtering statically significant values: {e}')

        df_get_sig = df[df['Hypothesis Correction Result'] == True].copy()
        df_get_sig['p-value'] = pd.to_numeric(df_get_sig['p-value'], errors='ignore', downcast='float')

        LIM_MAX = df_get_sig['p-value'].max()

        upset_df = table_for_upset(df_get_sig, df_query_final)

        if len(df.index) < 2:
            fig = go.Figure()
            fig.add_annotation(
                text="Not enough data to plot a figure, the condition needs to be loosen.",
                font={"size": 16},
                showarrow=False
            )
            fig_dict = {}
            VIL = pd.DataFrame()

        if len(df.index) >= 2 and len(df.index) < 13:
            original_df, df_to_plot, subsets, fig_dict, VIL = plotly_upset_plot_pivot(upset_df, LIM_MAX)
            fig = plotly_upset_figure(df_to_plot, original_df, subsets, LIM_MAX) 
            fig.update_layout(clickmode='event+select')

        if len(df.index) >= 13:    
            original_df, df_to_plot, subsets, fig_dict, VIL = plotly_upset_plot_pivot(upset_df, LIM_MAX)
            fig = plotly_upset_figure(df_to_plot, original_df, subsets, LIM_MAX) 
            fig.update_layout(clickmode='event+select')
        
        cache.set('upset_fig_'+session_id, fig)

        table = table_create_table_statistics(df)

        VIL_table = vil_table(VIL)

        return table, df.to_dict('records'), fig, {'visibility':'visible', 'display':'block'}, VIL_table, fig_dict, n_clicks, VIL, df_all_results.to_dict('records')

    elif input_id == 'enrichment-button' and len(checklist) == 0 and len(checklist_subset) != 0 and len(param_checklist) != 0 and statistical_test=='Hypergeometric':
        
        df_query_final = separate_db_position_geometry(pd.DataFrame(data_query))
        df_universe_final = separate_db_position_geometry(pd.DataFrame(data_universe))


        if param_checklist == ['Acyls']:
            df = calculate_enrichment_within_subset_hypergeom(checklist_subset, ['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), statistical_method, alpha_level, filter_count)

        elif 'Acyls' in param_checklist:
            excluded_list = [item for item in param_checklist if item != 'Acyls']
            dfs_to_concat = []

            if 'Total #C' not in excluded_list and 'Total #DB' not in excluded_list:

                dfs_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, excluded_list, df_query_final, df_universe_final, statistical_method, alpha_level, filter_count))
                dfs_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, ['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), statistical_method, alpha_level, filter_count))
            
            if 'Total #C' not in excluded_list and 'Total #DB' in excluded_list:
                dfs_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, excluded_list, df_query_final, df_universe_final, statistical_method, alpha_level, filter_count))
                dfs_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, ['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), statistical_method, alpha_level, filter_count))
                df_list = [calculate_enrichment_hypergeom_advanced(checklist_subset, df_query_final, df_universe_final, 'DOUBLE BONDS', double_bond_option, statistical_method, alpha_level, filter_count) for double_bond_option in double_bond_options]
                dfs_to_concat.extend(df_list)

            if 'Total #DB' not in excluded_list and 'Total #C' in excluded_list:
                dfs_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, excluded_list, df_query_final, df_universe_final, statistical_method, alpha_level, filter_count))
                dfs_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, ['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), statistical_method, alpha_level, filter_count))
                df_list = [calculate_enrichment_hypergeom_advanced(checklist_subset, df_query_final, df_universe_final, 'CARBONS', carbon_option, statistical_method, alpha_level, filter_count) for carbon_option in carbon_options]
                dfs_to_concat.extend(df_list)
            
            if 'Total #C' in excluded_list and 'Total #DB' in excluded_list:
                dfs_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, excluded_list, df_query_final, df_universe_final, statistical_method, alpha_level, filter_count))
                dfs_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, ['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), statistical_method, alpha_level, filter_count))
                df_list_carbons = [calculate_enrichment_hypergeom_advanced(checklist_subset, df_query_final, df_universe_final, 'CARBONS', carbon_option, statistical_method, alpha_level, filter_count) for carbon_option in carbon_options]
                dfs_to_concat.extend(df_list_carbons)
                df_list_db = [calculate_enrichment_hypergeom_advanced(checklist_subset, df_query_final, df_universe_final, 'DOUBLE BONDS', double_bond_option, statistical_method, alpha_level, filter_count) for double_bond_option in double_bond_options]
                dfs_to_concat.extend(df_list_db)

            df = pd.concat(dfs_to_concat)

        else:
            dfs_to_concat = []

            if 'Total #C' not in param_checklist and 'Total #DB' not in param_checklist:
                df = calculate_enrichment_within_subset_hypergeom(checklist_subset, param_checklist, df_query_final, df_universe_final, statistical_method, alpha_level, filter_count)

            if 'Total #C' not in param_checklist and 'Total #DB' in param_checklist:
                dfs_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, param_checklist, df_query_final, df_universe_final, statistical_method, alpha_level, filter_count))
                df_list = [calculate_enrichment_hypergeom_advanced(checklist_subset, df_query_final, df_universe_final, 'DOUBLE BONDS', double_bond_option, statistical_method, alpha_level, filter_count) for double_bond_option in double_bond_options]
                dfs_to_concat.extend(df_list)
            
            if 'Total #DB' not in param_checklist and 'Total #C' in param_checklist:
                dfs_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, param_checklist, df_query_final, df_universe_final, statistical_method, alpha_level, filter_count))
                df_list = [calculate_enrichment_hypergeom_advanced(checklist_subset, df_query_final, df_universe_final, 'CARBONS', carbon_option, statistical_method, alpha_level, filter_count) for carbon_option in carbon_options]
                dfs_to_concat.extend(df_list)
            
            if 'Total #C' in param_checklist and 'Total #DB' in param_checklist:
                dfs_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, param_checklist, df_query_final, df_universe_final, statistical_method, alpha_level, filter_count))
                df_list_carbons = [calculate_enrichment_hypergeom_advanced(checklist_subset, df_query_final, df_universe_final, 'CARBONS', carbon_option, statistical_method, alpha_level, filter_count) for carbon_option in carbon_options]
                dfs_to_concat.extend(df_list_carbons)
                df_list_db = [calculate_enrichment_hypergeom_advanced(checklist_subset, df_query_final, df_universe_final, 'DOUBLE BONDS', double_bond_option, statistical_method, alpha_level, filter_count) for double_bond_option in double_bond_options]
                dfs_to_concat.extend(df_list_db)

            df = pd.concat(dfs_to_concat)

        df['p-value'] = df['p-value'].apply(lambda x: edit_pval(x))
        df['Term (Classifier)'] = df['Term (Classifier)'].apply(lambda x: int(x) if isinstance(x, float) else x)
        df['Term (Classifier)'] = df['Term (Classifier)'].astype(str)

        df_all_results = df
            
        if filter == ['Filter statistically significant results']:
            try:
                df = df[df['Hypothesis Correction Result'] == True]
            except Exception as e:
                print(f'Error when filtering statically significant values: {e}')

        df_get_sig = df[df['Hypothesis Correction Result'] == True].copy()
        df_get_sig['p-value'] = pd.to_numeric(df_get_sig['p-value'], errors='ignore', downcast='float')

        LIM_MAX = df_get_sig['p-value'].max()

        upset_df = table_for_upset(df_get_sig, df_query_final)

        if len(df.index) < 2:
            fig = go.Figure()
            fig.add_annotation(
                text="Not enough data to plot a figure, the condition needs to be loosen.",
                font={"size": 16},
                showarrow=False
            )
            fig_dict = {}
            VIL = pd.DataFrame()

        if len(df.index) >= 2 and len(df.index) < 13:
            original_df, df_to_plot, subsets, fig_dict, VIL = plotly_upset_plot_pivot(upset_df, LIM_MAX)
            fig = plotly_upset_figure(df_to_plot, original_df, subsets, LIM_MAX) 
            fig.update_layout(clickmode='event+select')

        if len(df.index) >= 13:    
            original_df, df_to_plot, subsets, fig_dict, VIL = plotly_upset_plot_pivot(upset_df, LIM_MAX)
            fig = plotly_upset_figure(df_to_plot, original_df, subsets, LIM_MAX) 
            fig.update_layout(clickmode='event+select')
        
        cache.set('upset_fig_'+session_id, fig)

        table = table_create_table_statistics(df)

        VIL_table = vil_table(VIL)

        return table, df.to_dict('records'), fig, {'visibility':'visible', 'display':'block'}, VIL_table, fig_dict, n_clicks, VIL, df_all_results.to_dict('records')
    
    elif input_id == 'enrichment-button' and len(checklist) != 0 and len(checklist_subset) != 0 and len(param_checklist) != 0 and statistical_test == 'Hypergeometric':
        
        df_query_final = separate_db_position_geometry(pd.DataFrame(data_query))
        df_universe_final = separate_db_position_geometry(pd.DataFrame(data_universe))

        if checklist == ['Acyls']:
                df_general = calculate_enrichment_hypergeom(checklist, get_FA_df(df_query_final), get_FA_df(df_universe_final), statistical_method, alpha_level, filter_count)

        elif 'Acyls' in checklist:
            excluded_list = [item for item in checklist if item != 'Acyls']
            dfs_general_to_concat = []
            dfs_general_to_concat.append(calculate_enrichment_hypergeom(excluded_list, df_query_final, df_universe_final, statistical_method, alpha_level, filter_count))
            dfs_general_to_concat.append(calculate_enrichment_hypergeom(['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), statistical_method, alpha_level, filter_count))
            df_general = pd.concat(dfs_general_to_concat)

        else:    
            df_general = calculate_enrichment_hypergeom(checklist, df_query_final, df_universe_final, statistical_method, alpha_level, filter_count)


        if param_checklist == ['Acyls']:
            df_subset = calculate_enrichment_within_subset_hypergeom(checklist_subset, ['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), statistical_method, alpha_level, filter_count)

        elif 'Acyls' in param_checklist:
            excluded_list = [item for item in param_checklist if item != 'Acyls']
            dfs_subset_to_concat = []

            if 'Total #C' not in excluded_list and 'Total #DB' not in excluded_list:
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, excluded_list, df_query_final, df_universe_final, statistical_method, alpha_level, filter_count))
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, ['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), statistical_method, alpha_level, filter_count))

            if 'Total #C' not in excluded_list and 'Total #DB' in excluded_list:
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, param_checklist, df_query_final, df_universe_final, statistical_method, alpha_level, filter_count))
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, ['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), statistical_method, alpha_level, filter_count))
                df_list = [calculate_enrichment_hypergeom_advanced(checklist_subset, df_query_final, df_universe_final, 'DOUBLE BONDS', double_bond_option, statistical_method, alpha_level, filter_count) for double_bond_option in double_bond_options]
                dfs_subset_to_concat.extend(df_list)

            if 'Total #DB' not in excluded_list and 'Total #C' in excluded_list:
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, excluded_list, df_query_final, df_universe_final, statistical_method, alpha_level, filter_count))
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, ['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), statistical_method, alpha_level, filter_count))
                df_list = [calculate_enrichment_hypergeom_advanced(checklist_subset, df_query_final, df_universe_final, 'CARBONS', carbon_option, statistical_method, alpha_level, filter_count) for carbon_option in carbon_options]
                dfs_subset_to_concat.extend(df_list)

            if 'Total #C' in excluded_list and 'Total #DB' in excluded_list:

                dfs_subset_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, excluded_list, df_query_final, df_universe_final, statistical_method, alpha_level, filter_count))
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, ['Acyls'], get_FA_df(df_query_final), get_FA_df(df_universe_final), statistical_method, alpha_level, filter_count))
                df_list_carbons = [calculate_enrichment_hypergeom_advanced(checklist_subset, df_query_final, df_universe_final, 'CARBONS', carbon_option, statistical_method, alpha_level, filter_count) for carbon_option in carbon_options]
                dfs_subset_to_concat.extend(df_list_carbons)
                df_list_db = [calculate_enrichment_hypergeom_advanced(checklist_subset, df_query_final, df_universe_final, 'DOUBLE BONDS', double_bond_option, statistical_method, alpha_level, filter_count) for double_bond_option in double_bond_options]
                dfs_subset_to_concat.extend(df_list_db)

            df_subset = pd.concat(dfs_subset_to_concat)

        else:

            if 'Total #C' not in param_checklist and 'Total #DB' not in param_checklist:
                df_subset = calculate_enrichment_within_subset_hypergeom(checklist_subset, param_checklist, df_query_final, df_universe_final, statistical_method, alpha_level, filter_count)

            if 'Total #C' not in param_checklist and 'Total #DB' in param_checklist:
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, param_checklist, df_query_final, df_universe_final, statistical_method, alpha_level, filter_count))
                df_list = [calculate_enrichment_hypergeom_advanced(checklist_subset, df_query_final, df_universe_final, 'DOUBLE BONDS', double_bond_option, statistical_method, alpha_level, filter_count) for double_bond_option in double_bond_options]
                dfs_subset_to_concat.extend(df_list)

            if 'Total #DB' not in param_checklist and 'Total #C' in param_checklist:
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, param_checklist, df_query_final, df_universe_final, statistical_method, alpha_level, filter_count))
                df_list = [calculate_enrichment_hypergeom_advanced(checklist_subset, df_query_final, df_universe_final, 'CARBONS', carbon_option, statistical_method, alpha_level, filter_count) for carbon_option in carbon_options]
                dfs_subset_to_concat.extend(df_list)
            
            if 'Total #C' in param_checklist and 'Total #DB' in param_checklist:
                dfs_subset_to_concat.append(calculate_enrichment_within_subset_hypergeom(checklist_subset, param_checklist, df_query_final, df_universe_final, statistical_method, alpha_level, filter_count))
                df_list_carbons = [calculate_enrichment_hypergeom_advanced(checklist_subset, df_query_final, df_universe_final, 'CARBONS', carbon_option, statistical_method, alpha_level, filter_count) for carbon_option in carbon_options]
                dfs_subset_to_concat.extend(df_list_carbons)
                df_list_db = [calculate_enrichment_hypergeom_advanced(checklist_subset, df_query_final, df_universe_final, 'DOUBLE BONDS', double_bond_option, statistical_method, alpha_level, filter_count) for double_bond_option in double_bond_options]
                dfs_subset_to_concat.extend(df_list_db)
            
            df_subset = pd.concat(dfs_subset_to_concat)

        df = pd.concat([df_general, df_subset])
        
        df['p-value'] = df['p-value'].apply(lambda x: edit_pval(x))
        df['Term (Classifier)'] = df['Term (Classifier)'].apply(lambda x: int(x) if isinstance(x, float) else x)
        df['Term (Classifier)'] = df['Term (Classifier)'].astype(str)

        df_all_results = df
            
        if filter == ['Filter statistically significant results']:
            try:
                df = df[df['Hypothesis Correction Result'] == True]
            except Exception as e:
                print(f'Error when filtering statically significant values: {e}')

        df_get_sig = df[df['Hypothesis Correction Result'] == True].copy()
        df_get_sig['p-value'] = pd.to_numeric(df_get_sig['p-value'], errors='ignore', downcast='float')

        LIM_MAX = df_get_sig['p-value'].max()

        upset_df = table_for_upset(df_get_sig, df_query_final)

        if len(df.index) < 2:
            fig = go.Figure()
            fig.add_annotation(
                text="Not enough data to plot a figure, the condition needs to be loosen.",
                font={"size": 16},
                showarrow=False
            )
            fig_dict = {}
            VIL = pd.DataFrame()

        if len(df.index) >= 2 and len(df.index) < 13:
            original_df, df_to_plot, subsets, fig_dict, VIL = plotly_upset_plot_pivot(upset_df, LIM_MAX)
            fig = plotly_upset_figure(df_to_plot, original_df, subsets, LIM_MAX) 
            fig.update_layout(clickmode='event+select')

        if len(df.index) >= 13:    
            original_df, df_to_plot, subsets, fig_dict, VIL = plotly_upset_plot_pivot(upset_df, LIM_MAX)
            fig = plotly_upset_figure(df_to_plot, original_df, subsets, LIM_MAX) 
            fig.update_layout(clickmode='event+select')
        
        cache.set('upset_fig_'+session_id, fig)

        table = table_create_table_statistics(df)
        VIL_table = vil_table(VIL)

        return table, df.to_dict('records'), fig, {'visibility':'visible', 'display':'block'}, VIL_table, fig_dict, n_clicks, VIL, df_all_results.to_dict('records')

    else:
        pass


### Tab-3 Param Callback
@app.callback(
    Output('radioitems-alternative', 'value'),
    Output('enrichment-checklist', 'value'),
    Output('enrichment-checklist-subset', 'value'),
    Output('statistical-method-dropdown', 'value'),
    Output('alpha-level-input', 'value'),
    Output('filter-enrichment', 'value'),
    Output('filter-count', 'value'),
    Input('datatable-query-session', 'data'),
)
def reset_params(dt_query_session):

    ctx = callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if input_id == 'datatable-query-session':
        radioitems_alternative = 'greater'
        enrichment_checklist = ['Lipid Maps Category', 'Lipid Maps Main Class', 'Acyls']
        enrichment_checklist_subset = ['Lipid Maps Category', 'Lipid Maps Main Class']
        statistical_method_dropdown = 'fdr_bh'
        alpha_level_input = 0.1
        filter_enrichment = ['Filter statistically significant results']
        filter_count = 1
        return radioitems_alternative, enrichment_checklist, enrichment_checklist_subset, statistical_method_dropdown, alpha_level_input, filter_enrichment, filter_count
    else:
        raise PreventUpdate
    


### Graphical Representation - Net graph
@app.callback(
    Output('phylo_tree_figure', 'figure'),
    Output('cytoscape', 'elements'),
    Input('enrichment-container', 'children'),
    Input('datatable-query-session', 'data'),
    Input('datatable-universe-session', 'data'),
    Input('enrichment-container-session', 'data'),
)
def generate_cytoscape(value, query_data, universe_data, statistics_data):
    session_id = flask.session['session_id']
    triggered_id = ctx.triggered_id

    if triggered_id == None and statistics_data is None:
        raise PreventUpdate

    if triggered_id == 'enrichment-container' and statistics_data is not None:

        df_query = pd.DataFrame(query_data)
        df_universe = pd.DataFrame(universe_data)
        df_statistics = pd.DataFrame(statistics_data)
        
        elements, _, cy_nodes, cy_edges = get_elements(df_universe, df_query, df_statistics)

        cytoscape_object = {
        "format_version" : "1.0",
        "generated_by" : "cytoscape-3.8.0",
        "target_cytoscapejs_version" : "~2.1",
        "data" : {
            "shared_name" : "LORA Lipid network",
            "name" : "LORA Lipid network",        
            "__Annotations" : [ ],
            },
        "elements" : {
            "nodes" : {},
            "edges" : {}
            }          
        }
        cytoscape_object["elements"]["nodes"] = cy_nodes
        cytoscape_object["elements"]["edges"] = cy_edges
        
        json_object = json.dumps(cytoscape_object, indent=4)
        with open("assets/"+session_id+"/cytoscape_network_json.cyjs", "w") as outfile:
            outfile.write(json_object)

        columns_to_select = ['Normalized Name','Lipid Shorthand CATEGORY','Lipid Shorthand CLASS','Lipid Shorthand SPECIES','Lipid Shorthand MOLECULAR_SPECIES','Lipid Shorthand SN_POSITION','Lipid Shorthand STRUCTURE_DEFINED','Lipid Shorthand FULL_STRUCTURE','Lipid Shorthand COMPLETE_STRUCTURE']
        existing_columns = [col for col in columns_to_select if col in df_universe.columns]
        phylo_df = df_universe[existing_columns]
  
        phylo_df = phylo_df.fillna(value=np.nan)     
        phylo_xml = phylo_create_phyloXML(phylo_df, session_id)

        phylo_fig = phylo_create_circular_phylogram("assets/"+session_id+"/phylo_lipids.xml")
                
        return phylo_fig, elements

    raise PreventUpdate



### Graphical Representation - tables
@app.callback(Output('cytoscape-tapNodeData-output', 'children'),
              Input('cytoscape', 'tapNodeData'),
              Input('datatable-query-session', 'data'),
              Input('datatable-universe-session', 'data'),
              Input('enrichment-container-session', 'data'),
)
def displayTapNodeData(data, query_data, universe_data, statistics_data):
    session_id = flask.session['session_id']
    triggered_id = ctx.triggered_id

    if triggered_id is None:
        raise PreventUpdate

    if triggered_id == 'cytoscape':

        LM_abbreviations=get_abbr()

        df_query = pd.DataFrame(query_data)
        df_universe = pd.DataFrame(universe_data)
        df_statistics = pd.DataFrame(statistics_data)
        
        this_session = cache.get(session_id)
        _, sig_stat_all_df, _, _ = get_elements(df_universe, df_query, df_statistics)

        if data:
            full_name = LM_abbreviations[LM_abbreviations['Abbreviation'] == data['label']]
            if(len(full_name)>0):
                long_name = full_name['Long name'].iloc[0]
            else:
                long_name = data['label']
                    
            key2 = '\['+data['label']+'\]'
            stats_df = sig_stat_all_df[sig_stat_all_df['Term (Classifier)'].str.contains(pat=key2)]
            if(len(stats_df)>0):
                stats_df = stats_df.dropna(axis=1, how='all')
                return html.Div(html.P(['Node ', data['label'], ' = ', long_name, 
                                html.Br(), 
                                dash_table.DataTable(
                                            stats_df.to_dict('records'),
                                            [{"name": i, "id": i} for i in stats_df.columns],
                                            fill_width=False, 
                                            style_table={
                                                    'margin':'0 0 5rem 0', 
                                                    'border-collapse': 'separate', 
                                                    'border-spacing': '0 0.5rem'
                                            },
                                            style_data={
                                                    'lineHeight': '20px', 
                                                    'padding': '0.5rem', 
                                                    'border': '1px solid #e9ecef', 
                                                    'white-space': 'normal', 
                                                    'word-break': 'break-word', 
                                                    'max-width': '50%'},
                                            style_data_conditional=[
                                                {
                                                    'if': {'column_id': 'Names',},
                                                    'font-weight': 'bold',
                                                },
                                            ],
                                            style_cell={
                                                    'font_family': 'sans-serif',
                                                    'font_size': '10px',
                                            },
                                            style_header={
                                                    'backgroundColor': '#0053b5', 
                                                    'color': 'white', 
                                                    'fontWeight': 'bold',
                                                    'font-size': '10', 
                                                    'border-bottom': '2px solid #0053b5', 
                                                    'whiteSpace': 'normal',
                                                    'word-break': 'break-word', 
                                                    'height': 'auto', 
                                                    'padding': '0.5rem', 
                                                    'border-radius': '0.25rem', 
                                                    'max-width': '50%'
                                            })
                                ]))
            else:
                return html.Div(html.P(['Node ', data['label'], ' = ', long_name, html.Br(), 'Hint: Tap node with green border to get additional statistics.']))



@app.callback(
    Output('hover-data', 'children'),
    Input('basic-interactions', 'hoverData'))
def display_hover_data(hoverData):
    return json.dumps(hoverData, indent=2)



@app.callback(
    Output('upset_table', 'children'),
    Input('basic-interactions', 'clickData'),
    Input('basic-interactions-session', 'data'),)
def display_click_data(clickData, atlas):

    if clickData is None:
        raise PreventUpdate
        
    else:             
        try:
            klic = clickData['points'][0]['customdata']
            data_df = pd.DataFrame.from_dict(atlas[klic]) 

            for column in data_df.iloc[:, 1:]:
                data_df[column] = data_df[column].apply(lambda x: edit_pval(float(x))) 
        
            return html.Div(
            [
                dash_table.DataTable(
                    data=data_df.to_dict('records'),
                    columns=[{"id": x, "name": x} for x in data_df.columns],
                    style_data={
                        'lineHeight': '20px'
                    },
                    style_data_conditional=[
                        {
                            'if': {
                                'column_id': 'Names',
                            },
                            'font-weight': 'bold',
                        },
                    ],
                    style_cell={
                        'font_family': 'sans-serif',
                        'font_size': '12px',
                    },
                    style_header={'backgroundColor': '#0053b5', 'color': 'white', 'fontWeight': 'bold', 'border-bottom': '2px solid #0053b5', 'whiteSpace': 'normal', 'height': 'auto',},
                    )
            ]
            )
        except:
            return html.Div()



@app.callback(
    Output('selected-data', 'children'),
    Input('basic-interactions', 'selectedData'))
def display_selected_data(selectedData):
    return json.dumps(selectedData, indent=2)



@app.callback(
    Output('relayout-data', 'children'),
    Input('basic-interactions', 'relayoutData'))
def display_relayout_data(relayoutData):
    return json.dumps(relayoutData, indent=2)



@app.callback(
        Output('btn_report', 'disabled'),
        Input('enrichment-container', 'children'),
        Input('phylo_tree_figure', 'figure'),
        Input('VIL_table_session', 'data'),
        Input('basic-interactions-session', 'data'),
        Input('enrichment-checklist', 'value'),
        Input('enrichment-checklist-subset', 'value'),
        Input('radioitems-alternative', 'value'),
        Input('parameters-checklist', 'value'),
        Input('statistical-method-dropdown', 'value'),
        Input('alpha-level-input', 'value'),
        Input('statistical-test-dropdown', 'value'),
        Input('filter-count', 'value'),
        Input('all_results_session', 'data'),
        Input('original-data-session', 'data'),
        Input('datatable-query-session', 'data'),
        Input('datatable-universe-session', 'data'),
)
def create_report(
        enrichment_container, 
        phylo_tree_figure, 
        VIL_data, 
        basic_interactions_data,
        enrichment_checklist,
        enrichment_checklist_subset,
        alternative,
        parameters_checklist,
        statistical_method,
        alpha_level,
        statistical_test,
        filter_count,
        all_results_data,
        original_data,
        query_data,
        universe_data
        ):
    session_id = flask.session['session_id']
    
    print(f"Starting report creation for session {session_id}")

    triggered_id = ctx.triggered_id

    if triggered_id == 'enrichment-container':

        print("Enrichment container triggered")
        
        fig_interactions = cache.get('upset_fig_'+session_id)
        fig_tree = go.Figure(phylo_tree_figure)

        report_path = cache.get('report_path'+session_id)

        ## VIL table
        print("Creating VIL table xlsx started")
        pd.DataFrame(VIL_data).to_excel(report_path+'/VIL_table.xlsx', sheet_name='VIL_table')
        reporter_image_from_df(pd.DataFrame(VIL_data), session_id)
        print("Creating VIL table xlsx finished")

        ## Original data
        print("Creating original data xlsx started")
        original_query = pd.DataFrame(original_data['query'])
        original_universe = pd.DataFrame(original_data['universe'])
        with pd.ExcelWriter(report_path+'/original_data.xlsx', engine='xlsxwriter') as writer:
            original_query.to_excel(writer, sheet_name='original_query', index=False, header=None)
            original_universe.to_excel(writer, sheet_name='original_reference', index=False, header=None)
        print("Creating original data xlsx finished")

        ## Query and Universe tables
        print("Creating Query and Universe tables (parsed data) xlsx started")
        query_goslin_table = pd.DataFrame(query_data)
        universe_goslin_table = pd.DataFrame(universe_data)
        with pd.ExcelWriter(report_path+'/parsed_data.xlsx', engine='xlsxwriter') as writer:
            query_goslin_table.to_excel(writer, sheet_name='parsed_query', index=False)
            universe_goslin_table.to_excel(writer, sheet_name='parsed_reference', index=False)
        print("Creating Query and Universe tables (parsed data) xlsx finished")

        ## Results Fisher/Hypergeom
        print("Creating Results Fisher/Hypergeom xlsx started")
        all_results_df = pd.DataFrame(all_results_data)
        all_results_df_modified =  all_results_df.iloc[:, :-2]
        significant_results_df_modified = all_results_df_modified[all_results_df_modified['Hypothesis Correction Result'] == True]

        with pd.ExcelWriter(report_path+'/results.xlsx', engine='xlsxwriter') as writer:
            all_results_df_modified.to_excel(writer, sheet_name='all_results', index=False)
            significant_results_df_modified.to_excel(writer, sheet_name='significant_results', index=False)
        print("Creating Results Fisher/Hypergeom xlsx finished")

        ## UpSet
        print("Creating UpSet intersection tables xlsx started")
        with pd.ExcelWriter(report_path+'/UpSet_intersection_tables.xlsx', engine='xlsxwriter') as writer:
            dod = dict(reversed(list(basic_interactions_data.items())))
            for sheetname, value in dod.items():
                df_temp = pd.DataFrame(value)
                df_temp.to_excel(writer, sheet_name=sheetname, index=False)
                worksheet = writer.sheets[sheetname]
                workbook = writer.book
                for idx, col in enumerate(df_temp):
                    series = df_temp[col]
                    max_len = max((
                        series.astype(str).map(len).max(),
                        len(str(series.name))
                        )) + 1
                    worksheet.set_column(idx, idx, max_len)
                border_fmt = workbook.add_format({'bottom':1, 'top':1, 'left':1, 'right':1})
                worksheet.conditional_format(xlsxwriter.utility.xl_range(0, 0, len(df_temp), len(df_temp.columns)), {'type': 'no_errors', 'format': border_fmt})
        print("Creating UpSet intersection tables xlsx finished")

        print("Saving UpSet svg started")
        fig_interactions.write_image(report_path +'/UpSet_plot.svg')
        print("Saving UpSet jpg started")
        fig_interactions.write_image(report_path +'/UpSet_plot.jpg')
        print("Saving UpSet html started")
        fig_interactions.write_html(report_path +'/UpSet_plot_interactive.html')
        
        print("Saving Lipid Tree svg started")
        fig_tree.write_image(report_path +'/Lipid_tree_plot.svg')
        print("Saving Lipid Tree jpg started")
        fig_tree.write_image(report_path +'/Lipid_tree_plot.jpg')
        print("Saving Lipid Tree html started")
        fig_tree.write_html(report_path +'/Lipid_tree_plot_interactive.html')

        combined_checklist = [f"{param} within {enrich}" for enrich in enrichment_checklist_subset for param in parameters_checklist]
        parameters_to_report = enrichment_checklist + combined_checklist
        parameters_string = ", ".join(parameters_to_report)

        print("Creating PDF and ZIP started")
        reporter_create_pdf(session_id, parameters_string, statistical_test, alternative, statistical_method, str(alpha_level))
        print("Creating ZIP started")
        reporter_create_zip(session_id, report_path)
        print("Store zip in cache started")
        reporter_store_zip_in_cache('assets/'+session_id+'_LORA_report.zip', session_id, cache, report_path)
        print("Report creation completed started")
    
    else:
        raise PreventUpdate

    return False



@app.callback(
        Output("download-zip", "data"),
        Input("btn_report", "n_clicks"),
        prevent_initial_call=True,
)
def func(n_clicks):
    session_id = flask.session['session_id']
    report_path = cache.get('report_path'+session_id)
    def write_archive(bytes_io):
        print("write archive started")
        print(session_id+"_report")
        output = cache.get(session_id+"_report")
        decoded = base64.b64decode(output)
        bytes_io.write(decoded)
        shutil.rmtree(report_path, ignore_errors=True, onerror=None)
        print("write archive finished")
    
    LORA_report_file_name = 'LORA_report_' + str(datetime.now().strftime('%Y_%m_%d_%H_%M_%S')) + '.zip'

    return dcc.send_bytes(write_archive, LORA_report_file_name)

@app.server.after_request
def apply_sec_rules(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "frame-ancestors 'none'"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port = 8050, dev_tools_hot_reload = False)
