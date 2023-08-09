from dash import html, dcc
import dash_bootstrap_components as dbc

def get_header_version():
    return '1.1 (10.7.2023)'

### Header
header = html.Div([
            html.Div([
                html.A(
                        html.Img(src='assets/parrot.svg',style={'height':'3%', 'width':'3%', 'display': 'inline-block', 'padding-bottom':'15px', 'margin-left':'10px'}),
                        style={'padding':0},
                        href='/'
                ),
                html.H3('LORA: Lipid Over-Representation Analysis', style={'color':'white','padding':'0 1rem', 'margin':'0', 'display': 'inline-block'}),
                html.H6('version ' + str(get_header_version()), style={'color':'white', 'display': 'inline-block', 'float':'right', 'margin':'1rem 1rem 0 0'}),
                html.Div([
                        dbc.Button(children=[
                                html.Img(
                                        src='assets/icons/download-solid.svg',
                                        className="ml-2",
                                        style={"height": "1.2em", "verticalAlign": "middle", "paddingRight": "5px"},
                                        ),
                                "Report",
                                ], id="btn_report", color="light", disabled=True), 
                        dcc.Download(id="download-zip")], style={'display': 'inline-block', 
                                                                 'float':'right', 
                                                                 'margin-right':'2rem',
                                                                 'margin-top':'.5rem'}),
                html.A(
                        dbc.Button(children=[
                                html.Img(
                                        src='assets/icons/book.svg',
                                        className="ml-2",
                                        style={"height": "1.2em", "verticalAlign": "middle", "paddingRight": "5px"},
                                        ),
                                "Manual",
                                ], id="btn_manual", color="light"),
                        href='/manual',
                        style={'display': 'inline-block', 
                               'float':'right', 
                               'margin-right':'1rem',
                               'margin-top':'.5rem'}),

                ], style={'background-color': '#0053b5', 'padding':'15px 0 0 0', 'margin':'0 0 10px 0'}),
        ], style={'margin': '0 2rem 0 2rem', 'width':'auto'})



### Goslin Table
table_header = [
    html.Thead(html.Tr([html.Th("Level"), html.Th("Name"), html.Th("Description")]))
]

row1 = html.Tr([html.Td(html.P("Category (LM)", style={'margin':0})), html.Td(html.P("Glycerophospholipids (GP)", style={'margin':0})), html.Td(html.P("Lipid category", style={'margin':0}))])
row2 = html.Tr([html.Td(html.P("Class (LM)", style={'margin':0})), html.Td(html.P("Glycerophosphoethanolamine (PE) GP02", style={'margin':0})), html.Td(html.P("Lipid class", style={'margin':0}))])
row3 = html.Tr([html.Td(html.P("Species (LM Subclass)", style={'margin':0})), html.Td(html.P("Phosphatidylethanolamine, PE 32:2;O3", style={'margin':0})), html.Td(html.P("HG, FA summary, two double bond equivalents, three oxidations", style={'margin':0}))])
row4 = html.Tr([html.Td(html.P("Molecular species", style={'margin':0})), html.Td(html.P("PE 16:1_16:1;O3", style={'margin':0})), html.Td(html.P("HG, two FAs, two double bond equivalents, three oxidations", style={'margin':0}))])
row5 = html.Tr([html.Td(children=[html.I("sn", style={'display':'contents', 'margin':0}), html.P("-Position", style={'display':'contents', 'margin':0})]), html.Td(html.P("PE 16:1/16:1;O3", style={'margin':0})), html.Td(children=[html.P("HG, SN positions, here: for FA1 at ", style={'display':'contents', 'margin':0}), 
                                                                                                                                                                                                                                     html.I("sn1", style={'display':'contents', 'margin':0}), 
                                                                                                                                                                                                                                     html.P(" and FA2 at ", style={'display':'contents', 'margin':0}), 
                                                                                                                                                                                                                                     html.I("sn2", style={'display':'contents', 'margin':0}), 
                                                                                                                                                                                                                                     html.P(", two double bond equivalents, three oxidations", style={'display':'contents', 'margin':0})])]) ### upravit
row6 = html.Tr([html.Td(html.P("Structure defined", style={'margin':0})), html.Td(html.P("PE 16:1(6)/16:1;(OH)2;oxo", style={'margin':0})), html.Td(children=[html.P("HG, SN positions, here: for FA1 at ", style={'display':'contents', 'margin':0}), 
                                                                                                                                                              html.I("sn1", style={'display':'contents', 'margin':0}), 
                                                                                                                                                              html.P(" and FA2 at ", style={'display':'contents', 'margin':0}), 
                                                                                                                                                              html.I("sn2", style={'display':'contents', 'margin':0}), 
                                                                                                                                                              html.P(", three oxidations and unspecified stereo configuration (6) on FA1", style={'display':'contents', 'margin':0})])]) 
row7 = html.Tr([html.Td(html.P("Full structure", style={'margin':0})), html.Td(html.P("PE 16:1(6Z)/16:1;5OH,8OH;3oxo", style={'margin':0})), html.Td(children=[html.P("HG, SN positions, here: for FA1 at ", style={'display':'contents', 'margin':0}), 
                                                                                                                                                               html.I("sn1", style={'display':'contents', 'margin':0}), 
                                                                                                                                                               html.P(" and FA2 at ", style={'display':'contents', 'margin':0}), 
                                                                                                                                                               html.I("sn2", style={'display':'contents', 'margin':0}), 
                                                                                                                                                               html.P(", positions for oxidations and stereo configuration (6Z) on FA1", style={'display':'contents', 'margin':0})])]) 
row8 = html.Tr([html.Td(html.P("Complete structure", style={'margin':0})), html.Td(html.P("PE 16:1(6Z)/16:0;5OH[R],8OH;3oxo", style={'margin':0})), html.Td(children=[html.P("HG, SN positions, here: for FA1 at ", style={'display':'contents', 'margin':0}), 
                                                                                                                                                                      html.I("sn1", style={'display':'contents', 'margin':0}), 
                                                                                                                                                                      html.P(" and FA2 at ", style={'display':'contents', 'margin':0}), 
                                                                                                                                                                      html.I("sn2", style={'display':'contents', 'margin':0}), 
                                                                                                                                                                      html.P(", positions for oxidations and stereo configuration ([", style={'display':'contents', 'margin':0}),
                                                                                                                                                                      html.I("R", style={'display':'contents', 'margin':0}),
                                                                                                                                                                      html.P("]) and double bond position and stereo configuration (6Z) on FA1", style={'display':'contents', 'margin':0})])])

table_body = [html.Tbody([row1, row2, row3, row4, row5, row6, row7, row8])]

### Footer
footer = html.Footer(children=[
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
    