import base64
import io
from distutils.log import debug

import re
from re import search
import pandas as pd
import numpy as np

from scipy.stats import rankdata
from dash import dash_table
import plotly.graph_objects as go

import statsmodels.stats.multitest as smt
from utils.upset_chart import plotly_upset_plot_pivot, plotly_upset_figure


def fdr(p_vals, method, alpha_level):

    '''
    Get testing and adjustment of p-values

    Param
    -------
    p_vals: numpy.ndarray
            already sorted in ascending order
    method: string
            https://www.statsmodels.org/dev/generated/statsmodels.stats.multitest.multipletests.html
    alpha_level: float
                 threshold value for multiple tests
                 
    Returns
    -------
    mt[0]: numpy.ndarray, bool
           true for hypothesis that can be rejected for given alpha

    mt[1]: numpy.ndarray
           p-values corrected for multiple tests
    '''

    if p_vals != []:
        mt = smt.multipletests(pvals=p_vals, alpha=alpha_level, method=method, is_sorted=True)
        return mt[1]
    else:
        return 'N.D.'



def character_exchange(lipid_name):

    '''
    Search for misdefined entries and edit them (eg. ;2O -> ;O2)

    Param
    -------
    lipid_name: string

    Returns
    -------
    new_lipid_name: string
                    new (edited) lipid name
    lipid_name: string
                original lipid name
    '''

    try:
        position =  re.search(r';\d+O$', lipid_name).span()
        object = lipid_name[position[0]:position[1]]
        number = re.findall(r"\d+", object)
        new_lipid_name = lipid_name[:position[0]+1] + lipid_name[position[0]+2] + number[0]
        return new_lipid_name
    except:
        return lipid_name



def character_exchange_df(df):

    '''
    Edit dataframe using character_exchange function

    Param
    -------
    df: dataframe

    Returns
    -------
    df2: dataframe
         edited dataframe
    '''

    # init lipid names
    lipids = []

    try:
        # iterate over each row
        for row in df.iloc[:, 0]:
            row = character_exchange(str(row))
            lipids.append(row)
    except:
        print('Character_exchange_df cant be executed.')
        
    df2 = pd.DataFrame(lipids)

    return df2 



def separate_lipids(string):
    try:
        string = string.split('|')
        new_string = string[1]
        return new_string
    except:
        return string[0]



def prepare_for_parsing(df):

    '''
    Data preparation for parsing 

    Param
    -------
    df: dataframe

    Returns
    -------
    df: dataframe
    '''

    df = df.iloc[:, 0].dropna()

    df  = df.apply(lambda x: separate_lipids(x)).reset_index(drop=True)
    df = df.drop(df[df == ''].index)
    df = df.drop(df[df == 'Original name'].index)
    df = df.reset_index(drop=True)
    df = df.to_frame()

    return df



def prepare_for_storing(df):

    '''
    Prepare data for storing by removing NaN rows and duplicates.

    Param
    -------
    df: dataframe

    Returns
    -------
    df: dataframe
    '''

    df = df.replace(r'', np.NaN)
    df = df.replace(to_replace=r'.*UNDEFINED.*', value=np.NaN, regex=True)
    df = df.dropna(subset=['Original Name', 'Normalized Name'])
    df = df.drop_duplicates()

    df = df.dropna(how='all', axis=1)

    return df



def find_ethers(lipid_name):

    '''
    Find ethers by lipid name -> search for O-/P- within lipid name
        
    Param
    -------
    lipid_name: string

    Returns
    -------
    True/False: boolean

    Raise
    -------
    ValueError if lipid name (string) is not defined

    '''

    try:
        ether = re.findall(r' O-| P-', lipid_name)
        if ether == [' O-']:
            return True
        if ether == [' P-']:
            return True
        else: 
            return False
    except:
        raise ValueError('Lipid name not defined.')



def find_matches(df_query, df_universe):

    '''
    Compare query and universe datasets to find lipids occurring in both
        
    Param
    -------
    df_query: dataframe
    df_universe: dataframe

    Returns
    -------
    df_query: dataframe
              df with an additional column ['T/F'] with boolean values to indicate rows with lipids occurring in both the query and universe datasets (True) 
    df_universe: dataframe
                 df with an additional column ['T/F'] with boolean values to indicate rows with lipids occurring in both the query and universe datasets (True)

    '''

    exceptions = ['UNDEFINED', '']

    list_lipid_query = df_query['Normalized Name'].tolist()

    for i in exceptions:
        
        try:
            if i in list_lipid_query:
                list_lipid_query = [value for value in list_lipid_query if value != i]
        except:
            print('Cannot find any exceptions.')
            pass



    list_lipid_universe = df_universe['Normalized Name'].tolist()
    
    for i in exceptions: 
        
        try:
            if i in list_lipid_universe:
                list_lipid_universe = [value for value in list_lipid_universe if value != i]
        except:
            print('Cannot find any exceptions.')
            pass



    check_lipid_query = df_query['Normalized Name'].isin(list_lipid_universe)
    df_query['T/F'] = check_lipid_query
    df_query['T/F'] = df_query['T/F'].astype('str')

    check_lipid_universe = df_universe['Normalized Name'].isin(list_lipid_query)
    df_universe['T/F'] = check_lipid_universe
    df_universe['T/F'] = df_universe['T/F'].astype('str')

    return df_query, df_universe



def get_prepared_table_data(df):

    '''
    Divides a df into two so that df_a contains all normalized lipids and df_b contains all non-normalized lipids, 
    these both dfs are then sorted by normalized (df_a) or original (df_b) name and concatenated
        
    Param
    -------
    df: dataframe

    Returns
    -------
    df: dataframe
        modified df 
    '''

    df_a = df[(df['Normalized Name'] != '') & (df['Normalized Name'] != 'UNDEFINED')]
    df_b = df[(df['Normalized Name'] == '') | (df['Normalized Name'] == 'UNDEFINED')]

    df_a = df_a.sort_values(by =['T/F', 'Normalized Name'] , ascending=[False, True])
    df_b = df_b.sort_values(by ='Original Name' , ascending=True)
    df = pd.concat([df_a, df_b]).reset_index(drop=True)

    return df



def get_message(df):

    '''
    Calculate percentage of normalized lipids
    
    Param
    -------
    df: dataframe

    Returns
    -------
    message: string
    '''

    parsed_df = len(df[(df['Normalized Name'] != '') & (df['Normalized Name'] != 'UNDEFINED')])
    percentage = round((100 * parsed_df) / (len(df)), 2)
    message ='Percentage of normalized lipids: ' + str(percentage) + ' %.'

    return message



def table_update_query_and_universe_output(df):

    '''
    Generate table for tab_1

    Param
    -------
    df: dataframe

    Returns
    -------
    table: dash table

    '''

    if df.shape[0] < 500:
        margin = '44px' 
    if df.shape[0] > 500:
        margin = 0

    table = dash_table.DataTable(
                    df.to_dict('records'), 
                    [{"name": i, "id": i} for i in df[['Original Name', 'Normalized Name']].columns],
                    style_data={
                        'whiteSpace': 'normal',
                        'lineHeight': '20px'
                    },
                    style_cell={
                        'font_family': 'sans-serif',
                        'font_size': '12px',
                        'width':'50%',
                    },
                    style_as_list_view=True,
                    style_header={'backgroundColor': '#0053b5', 'color': 'white', 'fontWeight': 'bold', 'border-bottom': '2px solid #0053b5'},
                    style_table={'height': '400px', 'overflowY': 'auto', 'maxWidth': '100%', 'margin-bottom':margin},
                    fixed_rows={'headers': True},
                    style_data_conditional=[{
                        'if': {
                            'filter_query': '{T/F} eq "True"'},
                        'backgroundColor': 'rgb(130,195,65, 0.2)',
                    }],
                    page_size=500,
                    )
    
    return table



def table_create_table_statistics(df):

    '''
    Generate table for tab_3

    Param
    -------
    df: dataframe

    Returns
    -------
    table: dash table
    '''
    
    # custom width for each column query
    long_column_names = [{"if": {"column_id": column}, "min-width": "250px"} for column in df.columns if len(column) >= 30]
    med_column_names = [{"if": {"column_id": column}, "min-width": "150px"} for column in df.columns if (len(column) > 15 and len(column)) < 30]
    small_column_names = [{"if": {"column_id": column}, "min-width": "75px"} for column in df.columns if len(column) <= 15]

    adjusted_columns = long_column_names + med_column_names + small_column_names

    table = dash_table.DataTable(
        df.to_dict('records'), 
        [{"name": i, "id": i} for i in df.columns],
        hidden_columns=['Hypothesis Correction Result', 'Missing Query Val', 'Missing Reference Val'],
        tooltip_header={
        'Term (Group)': 'The main parameter of lipid partitioning.',
        'Term (Classifier)': 'The sub-parameter of lipid partitioning.',
        'Level': 'The structural level of lipids used for calculations.',
        'No Query': 'Number of specified queries out of the total number of queries.',
        'No Reference': 'Number of specified universe out of the total number of universe.',
        'p-value': 'Calculated p-value.',
        'Odds Ratio': 'Calculated Odds Ratio.',
        'FDR': 'Calculated False Discovery Rate.',
        'Missing Query': 'The number of missing lipids in the query out of the total number of lipids in the query based on lipid level.',
        'Missing Reference': 'The number of missing lipids in the reference lipidome out of the total number of lipids in the reference lipidome based on lipid level.',
        },
        tooltip_delay=0,
        tooltip_duration=None,
        style_cell={
            'font_family': 'sans-serif',
            'font_size': '12px',
        },
        style_data={
            'whiteSpace': 'normal',
            'lineHeight': '20px',
            'border': 'none'
        },
        style_as_list_view=True,
        style_header={'backgroundColor': '#0053b5', 'color': 'white', 'fontWeight': 'bold', 'whiteSpace': 'normal', 'border-bottom': '2px solid #0053b5', 'textDecoration': 'underline', 'textDecorationStyle': 'dotted',},
        style_table={'overflowY': 'auto', 'maxWidth': '100%', 'margin-top':'10px'},
        fixed_rows={'headers': True},
        style_cell_conditional=adjusted_columns,
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#eeeeee',
            }, 
            {
                'if': {'filter_query': '{Missing Query Val} eq "True"',
                'column_id':'Missing Query'},
                'color':'#ff0000',
            },
            {
                'if': {'filter_query': '{Missing Reference Val} eq "True"',
                'column_id':'Missing Reference'},
                'color':'#ff0000',
            },
            ],
        sort_action='native',
        sort_mode='multi',
        sort_as_null=['', 'No'],
        sort_by=[{'column_id': 'Normalized Name', 'direction': 'asc'}],
        editable=True,
        css=[{"selector": ".show-hide", "rule": "display: none"}]
        )
    
    return table



def edit_pval(number):

    '''
    Searche for and edit numbers less than 0.0001 to scientific notation

    Param
    -------
    number: float

    Returns
    -------
    scientific_number: string
    number: float
    '''

    if number < 0.0001:
        scientific_number = np.format_float_scientific(number, precision = 2, exp_digits=2)
        return scientific_number
    else:
        rounded_number = round(number, 4)
        return rounded_number



def get_FA_options(df):

    '''
    Generate list of column names containing FA within the name

    Param
    -------
    df: dataframe

    Returns
    -------
    FA_options: list
    '''

    df_FA = df.filter(like='FA', axis=1)
    FA_names_list = df_FA.columns.str.split(' ').str[0].tolist()
    FA_options = [FA_names_list[i] for i in range(len(FA_names_list)) if i == FA_names_list.index(FA_names_list[i])]

    return FA_options



def get_FA(carbon_chain, double_bond, bond_type, name):

    '''
    Generate fatty acyl

    Param
    -------
    carbon_chain: float
    double_bond: float
    bond_type: string
               ESTER/ETHER_PLASMANYL/ETHER_PLASMENYL
    name: string
          normalized lipid name

    Returns
    -------
    fatty acyl: string 
                fatty acyl generated by joining number of carbons with double bonds
    '''
    
    try:
        if pd.isna(carbon_chain) != True or pd.isna(double_bond) != True:
            if bond_type == 'ESTER':
                return str(int(carbon_chain)) + ':' + str(int(double_bond))
            if bond_type == 'ETHER_PLASMANYL':
                ether_plasmanyl = re.findall(r' O-', name)
                return ''.join(ether_plasmanyl).strip() + str(int(carbon_chain)) + ':' + str(int(double_bond))
            if bond_type == 'ETHER_PLASMENYL':
                ether_plasmenyl = re.findall(r' P-', name)
                return ''.join(ether_plasmenyl).strip() + str(int(carbon_chain)) + ':' + str(int(double_bond))
        else:
            return np.nan
    except:
        print('Unable to get FA.')
        pass



def get_FA_df(df):

    '''
    Generate melted dataframe for calculation fatty acyls enrichment

    Param
    -------
    df: dataframe

    Returns
    -------
    df: dataframe
    
    '''

    FA_chains = get_FA_options(df)

    for i in FA_chains:
        i_cols = [col for col in df.columns if '{}'.format(i) in col]
        df['{}'.format(i)] = df.apply(lambda x: get_FA(x[i + ' #C'], x[i + ' #DB'], x[i + ' Bond Type'], x['Normalized Name']), axis=1)
    
    col_names = list(df.columns.values)[:-(len(FA_chains))]
    df = df.melt(id_vars = col_names, var_name ='FAs', value_name ='Acyls')

    return df


def gen_table_demo(path_to_dir):

    '''
    Generate a table showing an example input csv file in tab-1 (Upload Datasets)

    Param
    -------
    path_to_dir: string

    Returns
    -------
    table: dash table
    
    '''

    df = pd.read_csv(path_to_dir, sep='\t')
    df = df.sample(frac=1)

    table = dash_table.DataTable(
            df[:50].to_dict('records'),
            [{"name": i, "id": i} for i in df.columns],
            style_header={
                'backgroundColor': 'white',
                'margin':0, 
                'padding':'0 10px 0 0'
            },
            style_cell={'margin':0, 'padding':'0 10px 0 0'},
            style_table={'height': '200px', 'overflowY': 'auto'} 
            )
            
    return table


def gen_textarea_demo(path_to_dir):

    '''
    Generate a string to textarea showing an example input txt file in tab-1 (Upload Datasets)

    Param
    -------
    path_to_dir: string

    Returns
    -------
    placeholder_string: string 
                        (with separator=\n)
    
    '''

    placeholder_string = ''
    with open(path_to_dir) as f:
        for line in f:
            try:
                placeholder_string = placeholder_string + line.strip() + '\n'
            except:
                placeholder_string = placeholder_string
                continue
    f.close()

    return placeholder_string


def rename_columns(column_name, category):

    '''
    Rename column names

    Param
    -------
    column_name: string
    categor: string

    Returns
    -------
    column_name_renamed: string
    column_name: string
    
    '''

    extensions = ['Total #DB', 'Total #C', 'Total #O', 'Ethers', 'Acyls']
    result = list(filter(column_name.startswith, extensions)) != []

    if result == True:
        if column_name.startswith('Ethers'):
            column_name = column_name.replace(': ', '')
            position =  re.search(r'False$|True$', column_name).span()
            column_name_renamed = column_name[:position[0]] + ' within ' + str(category) + ': ' + column_name[position[0]:]
        elif column_name.startswith('Acyls'):
            position =  re.search(r'\[.*?\]', column_name).span()
            column_name_renamed = column_name[:position[0]] + 'within ' + str(category) + column_name[position[0]:]
            column_name_renamed = re.sub('\_y$', '', column_name_renamed)
        else:
            position =  re.search(r': \d+$', column_name).span()
            column_name_renamed = column_name[:position[0]] + ' within ' + str(category) + column_name[position[0]:]
        return column_name_renamed
    else:
        return column_name



def rename_columns_acyl(string):
    string_renamed = string.replace('_x', '')
    return string_renamed


def float_to_int(name):

    '''
    Check if the inupt name is float, if yes, covert it to int

    Param
    -------
    name: any

    Returns
    -------
    name: int
    name: any data type
    '''

    if isinstance(name, float) == True:
        return int(name)
    else:
        return name



def get_significant_values_upset(df, df_upset):

    '''
    Get significant values for upset plot

    Param
    -------
    df: dataframe
    df_upset: dataframe

    Returns
    -------
    df_final: dataframe
    '''
    
    df = df.reset_index(inplace=False)

    list_complete_name = ['Names']
    df_upset_columns = list(df_upset.columns)

    for i in df.index:

        if search('Acyls within', df['Term (Group)'][i]):
            complete_name = df['Term (Group)'][i] + '[' + df['Level'][i] + ']: ' + df['Term (Classifier)'][i]
            if complete_name in df_upset_columns:
                list_complete_name.append(complete_name)

        elif search('Acyls', df['Term (Group)'][i]):
            complete_name = df['Term (Group)'][i] + ' [' + df['Level'][i] + ']: ' + df['Term (Classifier)'][i]
            if complete_name in df_upset_columns:
                list_complete_name.append(complete_name)

        elif ((df['Term (Group)'][i]).split())[-1] == ((df['Term (Classifier)'][i]).split())[0]:
            complete_name = df['Term (Classifier)'][i]
            if complete_name in df_upset_columns:
                list_complete_name.append(complete_name)

        else:
            complete_name = df['Term (Group)'][i] + ': ' + df['Term (Classifier)'][i]
            if complete_name in df_upset_columns:
                list_complete_name.append(complete_name)

    df_final = df_upset[list_complete_name]
    
    return df_final


def vil_table(dict_vil):

    '''
    It creates a Dash DataTable from a given dictionary containing VIL data. The function processes the data, applies specific formatting, and styles the table before returning the DataTable object.

    Param
    -------
    dict_vil: dict

    Returns
    -------
    VIL_table: dash_table.DataTable
    '''

    VIL = pd.DataFrame.from_dict(dict_vil)

    for column in VIL.iloc[:, 1:]:
        VIL[column] = VIL[column].apply(lambda x: edit_pval(float(x)))

    VIL_data = VIL.to_dict(orient='records')
    VIL_columns =  [{"name": i, "id": i,} for i in (VIL.columns)]

    VIL_table = dash_table.DataTable(
                    data=VIL_data, 
                    columns=VIL_columns,
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
                    style_table={
                        'overflowY': 'auto',
                        'maxHeight': '400px',
                    },
                    fixed_rows={'headers': True},
                    tooltip_header={i: i for i in VIL.columns},
                    tooltip_duration=None
                )
    return VIL_table



def get_db_position_geometry(cell):

    '''
    Takes any object of dataframe as input and check if it is a list of positions, if so separate postion number from geometry (Z for cis, E for trans).
    Before applying this function use split function to separate particular positions (e.g. 4Z|7Z|10Z|13Z|15E|19Z -> ['4Z', '7Z', '10Z', '13Z', '15E', '19Z'])

    Param
    -------
    cell: object

    Returns
    -------
    full: string
          contains double bond position numbers and/or E/Z geometries separated by ','
    '''

    if isinstance(cell, list):
        db_position_number, db_position_geometry = '', ''
        for position in cell:

            r0 = re.compile("([0-9]+)([a-zA-Z]+)")
            r1 = re.compile("\d+$")
            r2 = re.compile("^[a-zA-Z]+$")

            if r0.search(position):
                m = r0.match(position)
                db_position_number = '|'.join([db_position_number, m.group(1)])
                db_position_geometry = '|'.join([db_position_geometry, m.group(2)])

            if r1.search(position):
                m = r1.match(position)
                db_position_number = '|'.join([db_position_number, m.group()])

            if r2.search(position):
                m = r2.match(position)
                db_position_geometry = '|'.join([db_position_geometry, m.group()])

            db_position_number = db_position_number.lstrip('|')
            db_position_geometry = db_position_geometry.lstrip('|')

        full = ','.join([db_position_number, db_position_geometry])
        return full
    else:
        pass



def separate_db_position_geometry(df):

    '''
    Apply get_db_position_geometry function to dataframe and generate two new columns - one for position numbers, second for position geometry.

    Param
    -------
    df: DataFrame

    Returns
    -------
    df: DataFrame
    '''

    for column in df.columns:
        if 'DB Position' in column and 'LCB' not in column:

            FA_position = re.search(r'^FA\d+ ', column).span()
            FA_name = column[:FA_position[1]]

            df[column] = df[column].fillna('')
            df['{}DB Position Numbers'.format(FA_name)] = df[column].str.split('|')

            df['{}DB Position Geometries'.format(FA_name)] = np.nan
            df['{}DB Position Numbers'.format(FA_name)] = df['{}DB Position Numbers'.format(FA_name)].apply(lambda x: get_db_position_geometry(x))
            df['{}DB Position Numbers'.format(FA_name)] = df['{}DB Position Numbers'.format(FA_name)].fillna(value=np.nan)
            for i, row in df['{}DB Position Numbers'.format(FA_name)].items():
                if pd.isna(row) != True:
                    try:
                        df.loc[i, '{}DB Position Numbers'.format(FA_name)] = row.split(',')[0]
                        df.loc[i, '{}DB Position Geometries'.format(FA_name)] = row.split(',')[1]
                    except:
                        pass
    
    return df



def has_header(data_input):

    '''
    Checks if the input data has a header row by reading a sample of the data, examining the first row, and looking for specific keywords. If the keywords are found in the first row, the function returns True, indicating that the data has a header row. Otherwise, it returns False.
    
    Param
    -------
    data_input: bytes

    Returns
    -------
    True/False: bool

    '''

    sample_data = pd.read_csv(io.StringIO(data_input.decode('utf-8')), sep='\t', header=None, nrows=5)

    first_row = sample_data.iloc[0]

    lipid_name_keywords = ['lipid', 'query', 'universe', 'reference']

    if isinstance(first_row[0], str) and any(keyword.lower() in first_row[0].lower() for keyword in lipid_name_keywords):
        return True

    return False



def create_upset_figure(upset_df, df, LIM_MAX):

    '''
    Creates a Plotly figure based on the given DataFrame inputs. The function handles four scenarios:

    1. If the 'upset_df' DataFrame is empty, it returns a figure with an annotation indicating insufficient data.
    2. If the number of rows in 'df' DataFrame is less than 2, it returns a figure with an annotation indicating insufficient data for a meaningful plot.
    3. If the number of rows in 'df' DataFrame is between 2 and 13 (inclusive), it creates an upset plot with the data.
    4. If the number of rows in 'df' DataFrame exceeds 13, it creates an upset plot but adds an annotation indicating that the visualization is limited to the top 13 terms.

    Parameters
    ----------
    upset_df : pd.DataFrame
        DataFrame that is required to be non-empty to create the upset plot. This DataFrame should contain the upset information.

    df : pd.DataFrame
        DataFrame used to determine which scenario to handle based on its number of rows. This DataFrame should contain the data to be visualized.

    LIM_MAX : int
        The maximum limit value used in the 'plotly_upset_plot_pivot' function. This is used to control the amount of data to be visualized in the upset plot.

    Returns
    -------
    fig : plotly.graph_objects.Figure
        The resulting figure that is created based on the scenario. It could be an upset plot or a figure with annotations.

    fig_dict : dict
        A dictionary containing information about the figure such as subsets, cardinality etc. This dictionary is empty in cases where an upset plot isn't created due to insufficient data.

    VIL : dict
        A dictionary containing information about the visualization such as counts, intersects etc. This dictionary is empty in cases where an upset plot isn't created due to insufficient data.
    '''

    if upset_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="The requested operation could not be completed due to insufficient data.",
            font={"size": 16},
            showarrow=False
        )
        fig.update_layout(
            autosize=True,
            width=None,
            height=400,
        )
        fig_dict = {}
        VIL = {}

    else:
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

    return fig, fig_dict, VIL
