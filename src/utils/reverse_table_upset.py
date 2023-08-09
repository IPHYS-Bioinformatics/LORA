import pandas as pd
import re
from utils.common_functions import *

def table_for_upset(df, query):
    
    '''
    Get table for upset plot

    Param
    -------
    df: DataFrame
        statistically significant terms
    query: DataFrame
           query df
    Returns
    -------
    upset: DataFrame
           df for upset plot
    '''

    letters = np.array(list('abcdefghijklmnopqrstuvwxyz'))
    s_duplicates = query['Normalized Name'].astype(str) + ' (' + letters[query['Normalized Name'].groupby(query['Normalized Name']).cumcount()] + ')'
    s_duplicates = s_duplicates.apply(lambda x: x.replace(' (a)', ''))

    query.insert(loc=1, column='Unique Name', value=s_duplicates.tolist())

    upset = pd.DataFrame()

    for i in range(len(df)):

        if df.iloc[i, 0] == 'Lipid Maps Category' or  df.iloc[i, 0] == 'Lipid Maps Main Class':

            filtered_df = query[query[df.iloc[i, 0]] == df.iloc[i, 1]]
            filtered_df = filtered_df.drop_duplicates(subset='Unique Name')

            inter_df = filtered_df['Unique Name'].to_frame()
            inter_df['{}: {}'.format(df.iloc[i, 0], df.iloc[i, 1])] = df.iloc[i, 5]
            inter_df = inter_df.set_index('Unique Name')

            upset = pd.concat([upset, inter_df], axis=1)

        if (re.findall("^Acyls", df.iloc[i, 0]) != []) and (re.findall("Acyls$", df.iloc[i, 0]) != []):
            
            level_options = ['MOLECULAR_SPECIES', 'SN_POSITION', 'STRUCTURE_DEFINED', 'FULL_STRUCTURE', 'COMPLETE_STRUCTURE']
            level_index = level_options.index(df.iloc[i, 2])
            level_selected = level_options[level_index:]

            query_FA = get_FA_df(query)

            filtered_df = query_FA[(query_FA[df.iloc[i, 0]] == df.iloc[i, 1]) & (query_FA['Level'].isin(level_selected))]
            filtered_df = filtered_df.drop_duplicates(subset=['Unique Name', 'FAs'])

            inter_df = filtered_df['Unique Name'].to_frame()
            inter_df['{} [{}]: {}'.format(df.iloc[i, 0], df.iloc[i, 2], df.iloc[i, 1])] = df.iloc[i, 5]

            s = inter_df.groupby('Unique Name').cumcount().add(1).astype(str)
            inter_df['Unique Name'] += (' (' + s + ')').replace(' (1)', '')

            inter_df = inter_df.set_index('Unique Name')

            upset = pd.concat([upset, inter_df], axis=1)


        if (list(filter(df.iloc[i, 0].startswith, ['Total'])) != []) == True:
            param = df.iloc[i, 0].split(' within ')[0]
            subset = df.iloc[i, 0].split(' within ')[1]

            if subset in query['Lipid Maps Category'].values:
                if df.iloc[i, 1].isdigit():
                    filtered_df = query[(query['Lipid Maps Category'] == subset) & (query[param] == int(df.iloc[i, 1]))]
                else:
                    filtered_df = query[(query['Lipid Maps Category'] == subset) & (query[param] == df.iloc[i, 1])]
            if subset in query['Lipid Maps Main Class'].values:
                if df.iloc[i, 1].isdigit():
                    filtered_df = query[(query['Lipid Maps Main Class'] == subset) & (query[param] == int(df.iloc[i, 1]))]
                else:
                    filtered_df = query[(query['Lipid Maps Main Class'] == subset) & (query[param] == df.iloc[i, 1])]

            
            filtered_df = filtered_df.drop_duplicates(subset='Unique Name')
            
            inter_df = filtered_df['Unique Name'].to_frame()
            inter_df['{}: {}'.format(df.iloc[i, 0], df.iloc[i, 1])] = df.iloc[i, 5]
            inter_df = inter_df.set_index('Unique Name')

            upset = pd.concat([upset, inter_df], axis=1)

        if (re.findall("^Acyls", df.iloc[i, 0]) != []) and (re.findall("Acyls$", df.iloc[i, 0]) == []):
            param = df.iloc[i, 0].split(' within ')[0]
            subset = df.iloc[i, 0].split(' within ')[1]

            level_options = ['MOLECULAR_SPECIES', 'SN_POSITION', 'STRUCTURE_DEFINED', 'FULL_STRUCTURE', 'COMPLETE_STRUCTURE']
            level_index = level_options.index(df.iloc[i, 2])
            level_selected = level_options[level_index:]
            
            query_FA = get_FA_df(query)

            if subset in query_FA['Lipid Maps Category'].values:
                filtered_df = query_FA[(query_FA['Lipid Maps Category'] == subset) & (query_FA[param] == df.iloc[i, 1]) & (query_FA['Level'].isin(level_selected))]
            if subset in query_FA['Lipid Maps Main Class'].values:
                filtered_df = query_FA[(query_FA['Lipid Maps Main Class'] == subset) & (query_FA[param] == df.iloc[i, 1]) & (query_FA['Level'].isin(level_selected))]

            filtered_df = filtered_df.drop_duplicates(subset=['Original Name', 'FAs'])

            inter_df = filtered_df['Unique Name'].to_frame()
            inter_df['{} [{}]: {}'.format(df.iloc[i, 0], df.iloc[i, 2], df.iloc[i, 1])] = df.iloc[i, 5]

            s = inter_df.groupby('Unique Name').cumcount().add(1).astype(str)
            inter_df['Unique Name'] += (' (' + s + ')').replace(' (1)', '')

            inter_df = inter_df.set_index('Unique Name')

            upset = pd.concat([upset, inter_df], axis=1)

        if (df.iloc[i, 0] in query['Lipid Maps Category'].values) or (df.iloc[i, 0] in query['Lipid Maps Main Class'].values): ### not so specific, might be changed/improved

            subset = df.iloc[i, 0]
            searching_param = df.iloc[i, 1].split(' with ')[1]
            
            column_names_list = query.columns.to_list()

            if 'carbon' in searching_param:
                matches = re.findall(r'FA\d #C', ' '.join(map(str, column_names_list)))
            if 'double bonds' in searching_param:
                matches = re.findall(r'FA\d #DB', ' '.join(map(str, column_names_list)))

            filtered_df_new = pd.DataFrame()
            for ii in matches:
                query[ii] = query[ii].replace(0, np.nan)

                ### CARBONS
                if searching_param == 'acyls containing less than 16 carbon atoms':
                    if subset in query['Lipid Maps Category'].values:
                        filtered_df = query.loc[(query['Lipid Maps Category'] == subset) & (query[ii] < 16)]
                    if subset in query['Lipid Maps Main Class'].values:
                        filtered_df = query.loc[(query['Lipid Maps Main Class'] == subset) & (query[ii] < 16)]

                if searching_param == 'acyls containing 16-18 carbon atoms':
                    if subset in query['Lipid Maps Category'].values:
                        filtered_df = query.loc[(query['Lipid Maps Category'] == subset) & (query[ii] >= 16) & (query[ii] <= 18)]
                    if subset in query['Lipid Maps Main Class'].values:
                        filtered_df = query.loc[(query['Lipid Maps Main Class'] == subset) & (query[ii] >= 16) & (query[ii] <= 18)]

                if searching_param == 'acyls containing more than 18 carbon atoms':
                    if subset in query['Lipid Maps Category'].values:
                        filtered_df = query.loc[(query['Lipid Maps Category'] == subset) & (query[ii] > 18)]
                    if subset in query['Lipid Maps Main Class'].values:
                        filtered_df = query.loc[(query['Lipid Maps Main Class'] == subset) & (query[ii] > 18)]

                ### DOUBLE BONDS
                if searching_param == 'acyls containing 0 double bonds (saturated)':
                    if subset in query['Lipid Maps Category'].values:
                        filtered_df = query.loc[(query['Lipid Maps Category'] == subset) & (query[ii] == 0)]
                    if subset in query['Lipid Maps Main Class'].values:
                        filtered_df = query.loc[(query['Lipid Maps Main Class'] == subset) & (query[ii] == 0)]
                
                if searching_param == 'acyls containing 1 double bonds (monounsaturated)':
                    if subset in query['Lipid Maps Category'].values:
                        filtered_df = query.loc[(query['Lipid Maps Category'] == subset) & (query[ii] == 1)]
                    if subset in query['Lipid Maps Main Class'].values:
                        filtered_df = query.loc[(query['Lipid Maps Main Class'] == subset) & (query[ii] == 1)]

                if searching_param == 'acyls containing 2 or more double bonds (polyunsaturated)':
                    if subset in query['Lipid Maps Category'].values:
                        filtered_df = query.loc[(query['Lipid Maps Category'] == subset) & (query[ii] >= 2)]
                    if subset in query['Lipid Maps Main Class'].values:
                        filtered_df = query.loc[(query['Lipid Maps Main Class'] == subset) & (query[ii] >= 2)]


                filtered_df_new = pd.concat([filtered_df_new, filtered_df])
                filtered_df_new = filtered_df_new.drop_duplicates(subset='Unique Name', keep='first')
                

            inter_df = filtered_df_new['Unique Name'].to_frame()
            inter_df['{} {}'.format(df.iloc[i, 0], searching_param)] = df.iloc[i, 5]
            inter_df = inter_df.set_index('Unique Name')

            upset = pd.concat([upset, inter_df], axis=1)

        if (list(filter(df.iloc[i, 0].startswith, ['FA', 'LCB'])) != []) == True:

            param = df.iloc[i, 0].split(' within ')[0]
            subset = df.iloc[i, 0].split(' within ')[1]

            if (df.iloc[i, 1]).isnumeric():
                condition = float(df.iloc[i, 1])
            else:
                condition = df.iloc[i, 1]

            if subset in query['Lipid Maps Category'].values:
                filtered_df = query[(query['Lipid Maps Category'] == subset) & (query[param] == condition)]
            if subset in query['Lipid Maps Main Class'].values:
                filtered_df = query[(query['Lipid Maps Main Class'] == subset) & (query[param] == condition)]

            filtered_df = filtered_df.drop_duplicates(subset='Unique Name')

            inter_df = filtered_df['Unique Name'].to_frame()
            inter_df['{}: {}'.format(df.iloc[i, 0], df.iloc[i, 1])] = df.iloc[i, 5]
            inter_df = inter_df.set_index('Unique Name')

            upset = pd.concat([upset, inter_df], axis=1)

    upset = upset.reset_index()
    upset = upset.rename(columns = {'Unique Name':'Names'})
    print(upset)
    if 'Names' in upset.columns:
        upset['Names'] = upset['Names'].apply(lambda x: re.sub(r' \(\d+\)', '', x))
    else:
        print("Names column not found in DataFrame")

    upset = upset.fillna(1)
    
    return upset




