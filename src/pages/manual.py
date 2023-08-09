from dash import html
import dash_bootstrap_components as dbc
from pages.layout import get_header_version

manual_layout = html.Div([

    html.Div([
            html.Div([
                html.A(
                        html.Img(src='assets/parrot.svg',style={'height':'3%', 'width':'3%', 'display': 'inline-block', 'padding-bottom':'15px', 'margin-left':'10px'}),
                        style={'padding':0},
                        href='/'
                ),
                html.H3('LORA: Manual', style={'color':'white','padding':'0 1rem', 'margin':'0', 'display': 'inline-block'}),
                html.H6('version ' + str(get_header_version()), style={'color':'white', 'display': 'inline-block', 'float':'right', 'margin':'1rem 1rem 0 0'}),
                html.A(
                        dbc.Button(children=[
                                html.Img(
                                        src='assets/icons/chevron-compact-left.svg',
                                        className="ml-2",
                                        style={"height": "1.2em", "verticalAlign": "middle", "paddingRight": "5px"},
                                        ),
                                "LORA App",
                                ], id="btn_manual", color="light"),
                        href='/',
                        style={'display': 'inline-block', 
                               'float':'right', 
                               'margin-right':'2rem',
                               'margin-top':'.5rem'}),

                ], style={'background-color': '#0053b5', 'padding':'15px 0 0 0', 'margin':'0 0 10px 0'}),
        ], style={'margin': '0 2rem 0 2rem', 'width':'auto'}),

    dbc.Container(children=[

        html.H2('Preparing Reference Lipidome and Query', style={'margin-top':'2rem'}),
        html.H6('Reference Lipidome'),
            html.Ul([
                html.Li('Determining your reference lipidome depends on the specifics of your experiment. This could be lipids detectable by the chosen analytical method or lipids known for your organism of interest. From these lipids, construct a structured list (the individual lipid names must be one below the other) using either CSV or TXT formats. While your list may include a header for organization, please ensure it only contains the following terms: ‘lipid’, ‘query’, ‘reference’, ‘universe’.'),           
            ]),
        html.H6('Query'),
            html.Ul([
                html.Li('Prepare the query dataset in a similar manner. The query is a subset of the reference lipidome. It is the set of lipids that are detected in your experiment or are relevant to your study. For example, it may be a list of lipids that were detected in a particular sample, or lipids that differ between control and experimental conditions.'),
            ]),
        html.P('You can download the Reference Lipidome and Query for DEMO 1-4 in the app and check their formats.'),
    
        html.H2('Getting Started', style={'margin-top':'2rem'}),
        html.Ul([
            html.Li('Select a parser that suits your needs. The default parser is the Universal Lipid Parser, which employs multiple grammars to parse lipid names.'),
            html.Img(
                src='assets/manual_images/parser.png',
                alt='Parser selection',
                className="ml-2",
                style={
                    'width': '100%',  
                    'border': '1px solid black',
                    'box-shadow': '0px 0px 5px rgba(0, 0, 0, 0.5)',
                    'margin-top': '20px',
                    'margin-bottom': '20px',
                },
            ),
            html.Li('To upload your query and universe datasets, ensure that they are saved in CSV or TXT format on your computer. You can then upload these files onto the application one of two ways: either by dragging and dropping them from your folder directly onto the upload area or by clicking on the upload area and selecting the appropriate files from your folder.'),
            html.Li('After uploading both datasets, the lipids will be converted to standardized nomenclature and presented in a table. Any lipids that exist in both the query and universe files will be highlighted in green for easy identification.'),
            html.Img(
                src='assets/manual_images/loading.png',
                alt='Files uploading',
                className="ml-2",
                style={
                    'width': '100%',  
                    'border': '1px solid black',
                    'box-shadow': '0px 0px 5px rgba(0, 0, 0, 0.5)',
                    'margin-top': '20px',
                    'margin-bottom': '20px',
                },
            ),
            html.Li('Go to the second tab.'),
            html.Img(
                src='assets/manual_images/tab_2.png',
                alt='Go to tab 2',
                className="ml-2",
                style={
                    'width': '100%',  
                    'border': '1px solid black',
                    'box-shadow': '0px 0px 5px rgba(0, 0, 0, 0.5)',
                    'margin-top': '20px',
                    'margin-bottom': '20px',
                },
            ),
        ]),

        html.H2('Lipid Nomenclature Parsing And Normalization', style={'margin-top':'2rem'}),
        html.Ul([
            html.Li('After reading the information in blue box, click on the "Process" button. The processing will only apply to the lipids that are able to be parsed, and comprehensive details will be displayed in the tables for each of the datasets.'),
            html.Img(
                src='assets/manual_images/tab_2_schema.png',
                alt='tab 2 schema',
                className="ml-2",
                style={
                    'width': '100%',  
                    'border': '1px solid black',
                    'box-shadow': '0px 0px 5px rgba(0, 0, 0, 0.5)',
                    'margin-top': '20px',
                    'margin-bottom': '20px',
                },
            ),
            html.Li('Explore the tables.'),
            html.Img(
                src='assets/manual_images/query_table.png',
                alt='query table',
                className="ml-2",
                style={
                    'width': '100%',  
                    'border': '1px solid black',
                    'box-shadow': '0px 0px 5px rgba(0, 0, 0, 0.5)',
                    'margin-top': '20px',
                    'margin-bottom': '20px',
                },
            ),
            html.Li('Go to the third tab.'),
            html.Img(
                src='assets/manual_images/tab_3.png',
                alt='go to tab 3',
                className="ml-2",
                style={
                    'width': '100%',  
                    'border': '1px solid black',
                    'box-shadow': '0px 0px 5px rgba(0, 0, 0, 0.5)',
                    'margin-top': '20px',
                    'margin-bottom': '20px',
                },
            ),
            
        ]),

        html.H2('Enrichment Analysis', style={'margin-top':'2rem'}),
        html.Ul([
            html.Li('Choose test suitable for over-representation analysis.'),
            html.Img(
                src='assets/manual_images/enrichment_test.png',
                alt='select enrichment test',
                className="ml-2",
                style={
                    'width': '100%',  
                    'border': '1px solid black',
                    'box-shadow': '0px 0px 5px rgba(0, 0, 0, 0.5)',
                    'margin-top': '20px',
                    'margin-bottom': '20px',
                },
            ),
            html.Li('Select the parameters that you are interested in. These parameters indicate whether the analysis will be conducted on the category, class, or acyl level within the input data. Alternatively, you can set the parameters to calculate the enrichment of the structural features obtained from lipid parsing.'),
            html.Img(
                src='assets/manual_images/select_parameters.png',
                alt='select parameters',
                className="ml-2",
                style={
                    'width': '100%',  
                    'border': '1px solid black',
                    'box-shadow': '0px 0px 5px rgba(0, 0, 0, 0.5)',
                    'margin-top': '20px',
                    'margin-bottom': '20px',
                },
            ),
            html.Li('Select an option for multiple hypothesis testing including an alpha level.'),
            html.Img(
                src='assets/manual_images/mht.png',
                alt='select mht',
                className="ml-2",
                style={
                    'width': '100%',  
                    'border': '1px solid black',
                    'box-shadow': '0px 0px 5px rgba(0, 0, 0, 0.5)',
                    'margin-top': '20px',
                    'margin-bottom': '20px',
                },
            ),
            html.Li('Edit the filter count value.'),
            html.Img(
                src='assets/manual_images/filter_count.png',
                alt='filter count',
                className="ml-2",
                style={
                    'width': '100%',  
                    'border': '1px solid black',
                    'box-shadow': '0px 0px 5px rgba(0, 0, 0, 0.5)',
                    'margin-top': '20px',
                    'margin-bottom': '20px',
                },
            ),
            html.Li('Initiate the over-representation analysis by clicking on the "Process" button.'),
            html.Img(
                src='assets/manual_images/process.png',
                alt='process button',
                className="ml-2",
                style={
                    'width': '100%',  
                    'border': '1px solid black',
                    'box-shadow': '0px 0px 5px rgba(0, 0, 0, 0.5)',
                    'margin-top': '20px',
                    'margin-bottom': '20px',
                },
            ),
            html.Li('Check your results.'),
            html.Img(
                src='assets/manual_images/tab_3_results.png',
                alt='tab 3 results',
                className="ml-2",
                style={
                    'width': '100%',  
                    'border': '1px solid black',
                    'box-shadow': '0px 0px 5px rgba(0, 0, 0, 0.5)',
                    'margin-top': '20px',
                    'margin-bottom': '20px',
                },
            ),
            html.Li('Go to the fourth tab, or modify the parameters and re-run the analysis.'),
            html.Img(
                src='assets/manual_images/tab_4.png',
                alt='go to tab 4',
                className="ml-2",
                style={
                    'width': '100%',  
                    'border': '1px solid black',
                    'box-shadow': '0px 0px 5px rgba(0, 0, 0, 0.5)',
                    'margin-top': '20px',
                    'margin-bottom': '20px',
                },
            ),
        ]),

        html.H2('Graphical Representation', style={'margin-top':'2rem'}),
            html.Ul([
                html.Li('Examine the visual representations of your results.'),
                html.Img(
                src='assets/manual_images/lipidome_tree.png',
                alt='lipidome tree',
                className="ml-2",
                style={
                    'width': '100%',  
                    'border': '1px solid black',
                    'box-shadow': '0px 0px 5px rgba(0, 0, 0, 0.5)',
                    'margin-top': '20px',
                    'margin-bottom': '20px',
                },
            ),
            html.Img(
                src='assets/manual_images/lipidome_network.png',
                alt='lipidome network',
                className="ml-2",
                style={
                    'width': '100%',  
                    'border': '1px solid black',
                    'box-shadow': '0px 0px 5px rgba(0, 0, 0, 0.5)',
                    'margin-top': '20px',
                    'margin-bottom': '20px',
                },
            ),           
            ]),

        html.H2('Downloading Report', style={'margin-top':'2rem'}),
            html.Ul([
                html.Li('Download your report by clicking on the "Report" button located in the top bar.'),           
            ]),

        html.H2('Troubleshooting', style={'margin-top':'2rem'}),
        html.P('If you experience any difficulties, please do not hesitate to leave a message for us on Git.')
        
    ], style={'margin':'0 2rem', 'margin-bottom':'5rem'}),

    html.Footer(children=[
                html.A('Laboratory of Metabolism of Bioactive Lipids, Institute of Physiology, Czech Academy of Sciences, 2022', 
                        href='https://www.fgu.cas.cz/en/departments/laboratory-of-metabolism-of-bioactive-lipids',
                        className='footer-link', 
                        style={'color':'white',
                               'text-decoration':'none'})
                ], 
        style={'position':'fixed', 
               'bottom':'0', 
               'left':'0', 
               'width':'100%', 
               'background-color':'black', 
               'text-align':'center', 
               'padding':'5px'}
    )

])