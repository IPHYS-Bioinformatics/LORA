import pandas as pd
import numpy as np
import re
from scipy.stats import fisher_exact

from utils.common_functions import fdr
from utils.hypothesis_correction import hypothesis_correction



def calculate_enrichment_fisher(levels, query, universe, alternative, statistical_method, alpha_level, filter_count):
    
    '''
    Calculate enrichment using Fisher exact test

    Param
    -------
    levels: list
            list of options at which level the enrichment is calculated
            options: 'Lipid Maps Category', 'Lipid Maps Main Class', 'Acyls'
    query: DataFrame
    universe: DataFrame
    alternative: string
                 defines the alternative hypothesis
                 options: 'greater', 'less', 'two-sided'; default: 'greater'
    statistical_method: string
                        defines the multiple hypothesis correction
                        options: 'FDR', 'Bonferroni Correction', 'Holm-Bonferroni'; default: 'FDR'
    alpha_level: float
                 threshold value for multiple tests

    Returns
    -------
    df_final: DataFrame
    '''

    query = query[query['Lipid Maps Category'] != 'Undefined lipid category [UNDEFINED]']
    universe = universe[universe['Lipid Maps Category'] != 'Undefined lipid category [UNDEFINED]'] 

    query = query.replace('0:0', np.nan)
    universe = universe.replace('0:0', np.nan)

    if 'Acyls' not in levels:

        df_final = pd.DataFrame()

        for level in levels:

            if level in universe.columns and level in query.columns:

                universe_gb = universe.groupby(by=level)
                query_gb = query.groupby(by=level)

                universe_groups = dict(list(universe_gb))
                query_groups = dict(list(query_gb))
                
                universe_grandtotal = int(universe['Normalized Name'].count())
                query_grandtotal = int(query['Normalized Name'].count())

                group_name, category_name, level_name, p_value, oddsr_ratio, number_query, number_universe = ([] for i in range(7))
                for category in [c for c in universe_groups.keys() if c not in ['nan', 'None']]: 

                    universe_n = universe_groups[category].count()
                    universe_total = int(universe_n['Normalized Name'].sum())

                    try:
                        query_n = query_groups[category].count()
                        query_total = int(query_n['Normalized Name'].sum())

                    except:
                        query_total=0

                    if query_total > filter_count and universe_total > filter_count:  
                        contingency_table = [[query_total, universe_total], [query_grandtotal-query_total, universe_grandtotal-universe_total]]  
                        oddsr, p = fisher_exact(contingency_table, alternative=alternative)

                        group_name.append(level)
                        category_name.append(category)

                        if level == 'Lipid Maps Category':
                            level_name.append('CATEGORY')
                        if level == 'Lipid Maps Main Class':
                            level_name.append('CLASS')
                        if level.startswith('Total'):
                            level_name.append('SPECIES')
                        if 'SN Position' in level:
                            level_name.append('SN_POSITION')
                        if 'Position Numbers' in level:
                            level_name.append('STRUCTURE_DEFINED')
                        if 'Position Geometries' in level:
                            level_name.append('FULL_STRUCTURE')
                        if 'DB Positions' in level:
                            level_name.append('FULL_STRUCTURE')
                        if level.startswith('FA') and not level.endswith(('SN Position', 'Position Numbers', 'Position Geometries', 'DB Positions')):
                            level_name.append('MOLECULAR_SPECIES')

                        number_universe.append(str(universe_total) + '/' + str(universe_grandtotal))
                        number_query.append(str(query_total) + '/' + str(query_grandtotal))
                        p_value.append(p)
                        oddsr_ratio.append(str(round(oddsr, 4)))


                df = pd.DataFrame(list(zip(group_name, category_name, level_name, number_query, number_universe, p_value, oddsr_ratio)), 
                                    columns =['Term (Group)', 'Term (Classifier)', 'Level', 'No Query', 'No Reference','p-value', 'Odds Ratio'])

                df = df.drop(df[df['Term (Classifier)'] == False].index)

                df = df.sort_values('p-value', ignore_index=True)

                df['FDR'] = fdr(df['p-value'].to_numpy(), statistical_method, alpha_level)
                df['FDR'] = df['FDR'].apply(lambda x: round(x, 4) if isinstance(x, float) else x)

                df['Odds Ratio'] = df['Odds Ratio'].apply(lambda x: 'N.D.' if (x=='nan') else x)

                df['Hypothesis Correction Result'] = hypothesis_correction(df['p-value'].to_numpy(), statistical_method, alpha_level)

                df_final = pd.concat([df_final, df]).reset_index(drop=True)
        
    if 'Acyls' in levels:

        df_final = pd.DataFrame()

        level_options = ['MOLECULAR_SPECIES', 'SN_POSITION', 'STRUCTURE_DEFINED', 'FULL_STRUCTURE', 'COMPLETE_STRUCTURE']

        while len(level_options) > 0:

            universe_filtered = universe.loc[universe['Level'].isin(level_options)]
            query_filtered = query.loc[query['Level'].isin(level_options)]

            for level in levels:
                universe_gb = universe_filtered.groupby(by=level)
                query_gb = query_filtered.groupby(by=level)

                universe_groups = dict(list(universe_gb))
                query_groups = dict(list(query_gb))
                
                universe_grandtotal = int(universe['Normalized Name'].count())
                query_grandtotal = int(query['Normalized Name'].count())

                group_name, category_name, level_name, p_value, oddsr_ratio, number_query, number_universe, missing_query, missing_universe, missing_query_val, missing_universe_val = ([] for i in range(11))
                for category in [c for c in universe_groups.keys() if c not in ['nan', 'None']]:
                    universe_n = universe_groups[category].count()
                    universe_total = int(universe_n['Normalized Name'].sum())

                    universe_n_all = universe[universe[level] == category].shape[0]

                    try:
                        query_n = query_groups[category].count()
                        query_total = int(query_n['Normalized Name'].sum())

                        query_n_all = query[query[level] == category].shape[0]

                    except:
                        query_total=0

                    if query_total > filter_count and universe_total > filter_count:  
                        contingency_table = [[query_total, universe_total], [query_grandtotal-query_total, universe_grandtotal-universe_total]]  
                        oddsr, p = fisher_exact(contingency_table, alternative=alternative)

                        group_name.append(level)
                        category_name.append(category)
                        level_name.append(level_options[0])
                        number_universe.append(str(universe_total) + '/' + str(universe_grandtotal))
                        number_query.append(str(query_total) + '/' + str(query_grandtotal))
                        p_value.append(p)
                        oddsr_ratio.append(round(oddsr, 4))

                        missing_query.append(str(query_total) + '/' + str(query_n_all))
                        missing_universe.append(str(universe_total) + '/' + str(universe_n_all))

                        if (query_total/query_n_all) == 1:
                            missing_query_val.append(str(False))
                        if (query_total/query_n_all) != 1:
                            missing_query_val.append(str(True))

                        if (universe_total/universe_n_all) == 1:
                            missing_universe_val.append(str(False))
                        if (universe_total/universe_n_all) != 1:
                            missing_universe_val.append(str(True))


                df = pd.DataFrame(list(zip(group_name, category_name, level_name, number_query, number_universe, p_value, oddsr_ratio, missing_query, missing_universe, missing_query_val, missing_universe_val)), 
                                    columns =['Term (Group)', 'Term (Classifier)', 'Level', 'No Query', 'No Reference','p-value', 'Odds Ratio', 'Missing Query', 'Missing Reference', 'Missing Query Val', 'Missing Reference Val'])

                df = df.drop(df[df['Term (Classifier)'] == False].index)

                df = df.sort_values('p-value', ignore_index=True)

                df['FDR'] = fdr(df['p-value'].to_numpy(), statistical_method, alpha_level)
                df['FDR'] = df['FDR'].apply(lambda x: round(x, 4) if isinstance(x, float) else x)

                df['Odds Ratio'] = df['Odds Ratio'].apply(lambda x: 'N.D.' if (x=='nan') else x)

                df['Hypothesis Correction Result'] = hypothesis_correction(df['p-value'].to_numpy(), statistical_method, alpha_level)

                df_final = pd.concat([df_final, df]).reset_index(drop=True)

                level_options = level_options[1:]
    
    return df_final



def calculate_enrichment_within_subset_fisher(levels, subsets, query, universe, alternative, statistical_method, alpha_level, filter_count):

    '''
    Calculate enrichment within chosen subsets using Fisher exact test
    Param
    -------
    levels: list
            list of options at which level the enrichment is calculated
            options: 'Lipid Maps Category', 'Lipid Maps Main Class'
    subsets: list
             list of options within which subsets the enrichment is calculated
             options: 'Total #C', 'Total #DB', 'Total #O', 'Ethers', 'Acyls'
    query: DataFrame
    universe: DataFrame
    alternative: string
                 defines the alternative hypothesis
                 options: 'greater', 'less', 'two-sided'; default: 'greater'
    statistical_method: string
                        defines the multiple hypothesis correction
                        options: 'FDR', 'Bonferroni Correction', 'Holm-Bonferroni'; default: 'FDR'
    alpha_level: float
                 threshold value for multiple tests
    Returns
    -------
    df_final: DataFrame
    '''

    if 'Total #O' not in query.columns or 'Total #O' not in universe.columns:
        subsets = [s for s in subsets if s != 'Total #O']
    
    if 'Ethers' not in query.columns or 'Ethers' not in universe.columns:
        subsets = [s for s in subsets if s != 'Ethers']
    
    
    df_final = pd.DataFrame()

    for level in levels:

        universe_gb = universe.groupby(by=level)
        query_gb = query.groupby(by=level)

        universe_groups = dict(list(universe_gb))
        query_groups = dict(list(query_gb))

        for category in [c for c in universe_groups.keys() if c not in ['nan', 'None']]:
            universe_groups_category = universe_gb.get_group(category)
            try:
                query_groups_category = query_gb.get_group(category)
            except:
                query_groups_category = universe_gb.get_group(category)

            df = calculate_enrichment_fisher(subsets, query_groups_category, universe_groups_category, alternative, statistical_method, alpha_level, filter_count)

            df['Term (Group)'] = df['Term (Group)'].apply(lambda x: str(x) + ' within ' + str(category))

            df_final = pd.concat([df_final, df]).reset_index(drop=True)

        
    return df_final



def calculate_enrichment_fisher_advanced(levels, query, universe, alternative, specific, filter, statistical_method, alpha_level, filter_count):

    '''
    Calculate enrichment based on defined condition using Fisher exact test
    Param
    -------
    levels: list
            list of options at which level the enrichment is calculated
            options: 'Lipid Maps Category', 'Lipid Maps Main Class'
    query: DataFrame
    universe: DataFrame
    alternative: string
                 defines the alternative hypothesis
                 options: 'greater', 'less', 'two-sided'; default: 'greater'
    specific: string
              specifies whether lipids are filtered based on the number of carbons within acyls or double bonds
              options: 'CARBONS', 'DOUBLE BONDS'
    statistical_method: string
                        defines the multiple hypothesis correction
                        options: 'FDR', 'Bonferroni Correction', 'Holm-Bonferroni'; default: 'FDR'
    filter: string
            filter condition
            options: find options in carbon_options.txt and double_bonds_option.txt
    alpha_level: float
                 threshold value for multiple tests

    Returns
    -------
    df_final: DataFrame
    '''

    query = query[query['Lipid Maps Category'] != 'Undefined lipid category [UNDEFINED]']
    universe = universe[universe['Lipid Maps Category'] != 'Undefined lipid category [UNDEFINED]']

    df_final = pd.DataFrame()

    for level in levels:

        universe_gb = universe.groupby(by=level)
        query_gb = query.groupby(by=level)

        universe_groups = dict(list(universe_gb))
        query_groups = dict(list(query_gb))

        group_name, category_name, level_name, p_value, oddsr_ratio, number_query, number_universe = ([] for i in range(7))
        for category in [c for c in universe_groups.keys() if c not in ['nan', 'None']]:

            universe_groups_category = universe_gb.get_group(category)

            try:
                query_groups_category = query_gb.get_group(category)
            except:
                query_groups_category = universe_gb.get_group(category)


            universe_grandtotal = int(universe_groups_category['Normalized Name'].count())
            query_grandtotal = int(query_groups_category['Normalized Name'].count())


            column_names_list = query_groups_category.columns.to_list()


            if specific == 'CARBONS':
                matches = re.findall(r'FA\d #C', ' '.join(map(str, column_names_list)))
            if specific == 'DOUBLE BONDS':
                matches = re.findall(r'FA\d #DB', ' '.join(map(str, column_names_list)))


            universe_filtered_new = pd.DataFrame()
            query_filtered_new = pd.DataFrame()


            for i in matches:
                universe_groups_category_copy = universe_groups_category.copy()
                universe_groups_category_copy.loc[universe_groups_category_copy[i] == 0, i] = np.nan

                query_groups_category_copy = query_groups_category.copy()
                query_groups_category_copy.loc[query_groups_category_copy[i] == 0, i] = np.nan

                ### CARBONS
                if filter == 'acyls containing less than 16 carbon atoms':
                    universe_filtered = universe_groups_category_copy.loc[universe_groups_category_copy[i] < 16]
                    query_filtered = query_groups_category_copy.loc[query_groups_category_copy[i] < 16]

                if filter == 'acyls containing 16-18 carbon atoms':
                    universe_filtered = universe_groups_category_copy.loc[(universe_groups_category_copy[i] >= 16) & (universe_groups_category_copy[i] <= 18)]
                    query_filtered = query_groups_category_copy.loc[(query_groups_category_copy[i] >= 16) & (query_groups_category_copy[i] <= 18)]

                if filter == 'acyls containing more than 18 carbon atoms':
                    universe_filtered = universe_groups_category_copy.loc[universe_groups_category_copy[i] > 18]
                    query_filtered = query_groups_category_copy.loc[query_groups_category_copy[i] > 18]


                ### DOUBLE BONDS
                if filter == 'acyls containing 0 double bonds (saturated)':
                    universe_filtered = universe_groups_category_copy.loc[universe_groups_category_copy[i] == 0]
                    query_filtered = query_groups_category_copy.loc[query_groups_category_copy[i] == 0]
                
                if filter == 'acyls containing 1 double bonds (monounsaturated)':
                    universe_filtered = universe_groups_category_copy.loc[universe_groups_category_copy[i] == 1]
                    query_filtered = query_groups_category_copy.loc[query_groups_category_copy[i] == 1]

                if filter == 'acyls containing 2 or more double bonds (polyunsaturated)':
                    universe_filtered = universe_groups_category_copy.loc[universe_groups_category_copy[i] >= 2]
                    query_filtered = query_groups_category_copy.loc[query_groups_category_copy[i] >= 2]

                universe_filtered_new = pd.concat([universe_filtered_new, universe_filtered])
                query_filtered_new = pd.concat([query_filtered_new, query_filtered])


            universe_filtered_new = universe_filtered_new.drop_duplicates()
            query_filtered_new = query_filtered_new.drop_duplicates()

            universe_n = universe_filtered_new.count()
            universe_total = int(universe_n['Normalized Name'].sum())


            try:
                query_n = query_filtered_new.count()
                query_total = int(query_n['Normalized Name'].sum())
            except:
                query_total=0


            if query_total > filter_count and universe_total > filter_count:  
                contingency_table = [[query_total, universe_total], [query_grandtotal-query_total, universe_grandtotal-universe_total]]  
                oddsr, p = fisher_exact(contingency_table, alternative=alternative)

                abbr_match = re.search('(?<=\[).*?(?=\])', category)

                if abbr_match:
                    abbr = abbr_match.group()
                else:
                    abbr = None

                group_name.append(category)
                
                if abbr is not None:
                    category_name.append('[' + abbr + ']' + ' with ' + filter)
                else:
                    category_name.append('[' + category + ']' + ' with ' + filter)

                level_name.append('MOLECULAR_SPECIES')
                number_universe.append(str(universe_total) + '/' + str(universe_grandtotal))
                number_query.append(str(query_total) + '/' + str(query_grandtotal))
                p_value.append(p)
                oddsr_ratio.append(round(oddsr, 4))
            
        df = pd.DataFrame(list(zip(group_name, category_name, level_name, number_query, number_universe, p_value, oddsr_ratio)), 
                columns =['Term (Group)', 'Term (Classifier)', 'Level', 'No Query', 'No Reference','p-value', 'Odds Ratio'])
    

        df = df.sort_values('p-value', ignore_index=True)

        df['FDR'] = fdr(df['p-value'].to_numpy(), statistical_method, alpha_level)
        df['FDR'] = df['FDR'].apply(lambda x: round(x, 4) if isinstance(x, float) else x)

        df['Odds Ratio'] = df['Odds Ratio'].apply(lambda x: 'N.D.' if (x=='nan') else x)

        df['Hypothesis Correction Result'] = hypothesis_correction(df['p-value'].to_numpy(), statistical_method, alpha_level)

        df_final = pd.concat([df_final, df]).reset_index(drop=True)
            
    return df_final