import dash_cytoscape as cyto
cyto.load_extra_layouts()
import pandas as pd
import uuid
import math

def get_elements(df_universe, df_query, df_statistics):
    df_universe['Functional Class Abbr'] = df_universe['Functional Class Abbr'].astype(str)
    df_universe['Functional Class Abbr'] =  df_universe['Functional Class Abbr'].apply(lambda x: x.replace('[','').replace(']',''))
    allnodes = df_universe['Functional Class Abbr']

    dfs = [] 
    for i in range(len(allnodes)):
        query = allnodes[i]  
        dfs.append(
            {
                'Category' : query[0:2],
                'Class' : query[0:4],
                'Subclass' : query[0:6],
                'Count': 1,
                'Source1' : query[0:2],
                'Target1' : query[0:4],
                'Source2' : query[0:4],
                'Target2' : query[0:6]
            }  
        )
    df_net = pd.DataFrame(dfs)
    df_net.replace(to_replace="nan",value="Unknown", inplace=True)
    df_net.replace(to_replace="na",value="Unspecified", inplace=True)

    ## build nodes
    categories = df_net.groupby(['Category'], as_index=False).size()
    categories.loc[len(categories.index)] = ['LIPIDOME', 0]
    categories['type'] = 'LMCATEGORY'

    classes = df_net.groupby(['Class'], as_index=False).size()
    classes = classes.rename(columns={'Class': 'Category'})
    classes['type'] = 'LMCLASS'

    subclasses = df_net.groupby(['Subclass'], as_index=False).size()
    subclasses = subclasses.rename(columns={'Subclass': 'Category'})
    subclasses['type'] = 'LMSUBCLASS'

    all_nodes = pd.concat([categories, classes, subclasses])
    all_nodes.reset_index(drop=True, inplace=True)
    all_nodes.drop_duplicates(subset='Category', keep="last", inplace = True)

    all_nodes['Sector1'] = 0
    all_nodes['Sector2'] = 100
    all_nodes['Sector3'] = 0

    df_query['Functional Class Abbr'] = df_query['Functional Class Abbr'].astype(str)
    df_query['Functional Class Abbr'] =  df_query['Functional Class Abbr'].apply(lambda x: x.replace('[','').replace(']',''))
    allqnodes = df_query['Functional Class Abbr']

    dfs = [] 
    for i in range(len(allqnodes)):
        query = allqnodes[i]  
        dfs.append(
            {
                'Category' : query[0:2],
                'Class' : query[0:4],
                'Subclass' : query[0:6],
                'Count': 1,
                'Source1' : query[0:2],
                'Target1' : query[0:4],
                'Source2' : query[0:4],
                'Target2' : query[0:6]
            }  
        )
    df_qnet = pd.DataFrame(dfs)
    df_qnet.replace(to_replace="nan",value="Unknown", inplace=True)
    df_qnet.replace(to_replace="na",value="Unspecified", inplace=True)

    qcategories = df_qnet.groupby(['Category'], as_index=False).size()
    qcategories['type'] = 'LMCATEGORY'

    qclasses = df_qnet.groupby(['Class'], as_index=False).size()
    qclasses = qclasses.rename(columns={'Class': 'Category'})
    qclasses['type'] = 'LMCLASS'

    qsubclasses = df_qnet.groupby(['Subclass'], as_index=False).size()
    qsubclasses = qsubclasses.rename(columns={'Subclass': 'Category'})
    qsubclasses['type'] = 'LMSUBCLASS'

    all_qnodes = pd.concat([qcategories, qclasses, qsubclasses])
    all_qnodes.reset_index(drop=True, inplace=True)
    all_qnodes.drop_duplicates(subset='Category', keep="last", inplace = True)

    ## add statistics
    statistics = df_statistics
    stat_options = ['CATEGORY', 'CLASS']
    sig_stat_df = statistics[(statistics['Level'].isin(stat_options)) & (statistics['Hypothesis Correction Result'] == True)]
    sig_stat_all_df = statistics[statistics['Hypothesis Correction Result'] == True]

    for index, row in all_nodes.iterrows():
            key = row['Category']
            key2 = '\['+key+'\]'
            sigs_found = sig_stat_df[sig_stat_df['Term (Classifier)'].str.contains(pat=key2)]          
            try:
                q_size = int(all_qnodes[all_qnodes['Category'] == key]['size'].values[0])
                u_size = int(row['size'])
                sector1 = q_size/u_size
                sector2 = 1-sector1 
                if(len(sigs_found)>0):            
                    all_nodes.at[index,'Sector3'] = round(sector1*100,0)
                else:
                    all_nodes.at[index,'Sector1'] = round(sector1*100,0)

                all_nodes.at[index,'Sector2'] = round(sector2*100,0)
            except:
                pass

    rootedges = categories.copy(deep=True)    
    rootedges = rootedges.rename(columns={'Category': 'Source1', 'size': 'Target1'})
    rootedges['Target1']='LIPIDOME'

    edges1 = df_net[['Source1','Target1']].value_counts().reset_index(name='count')
    edges2 = df_net[['Source2','Target2']].value_counts().reset_index(name='count')
    edges2 = edges2.rename(columns={'Source2': 'Source1', 'Target2': 'Target1'})

    edges = pd.concat([edges1, edges2, rootedges])
    edges.reset_index(drop=True, inplace=True)
    edges.drop(edges[edges['Source1'] == edges['Target1']].index, inplace = True)
    edges = edges.drop('count', axis=1)

    ## build cy
    final = {}
    final["nodes"] = []
    final["edges"] = []

    for index, row in all_nodes.iterrows():
        nx = {}
        nx["data"] = {}            
        nx["data"]["id"] = row['Category']
        nx["data"]["label"] = row['Category'] 
        nx["data"]["shape"] = 'ellipse'
        nx["data"]["sector1"] = row['Sector1']
        nx["data"]["sector2"] = row['Sector2']
        nx["data"]["sector3"] = row['Sector3']
        nx["data"]["size"] = math.sqrt(row['size']*100)
        nx["data"]["valign"] = 'top'
        nx["data"]["halign"] = 'center'

        key2 = '\['+row['Category']+'\]'
        stat_df = sig_stat_all_df[sig_stat_all_df['Term (Classifier)'].str.contains(pat=key2)]
        if(len(stat_df)>0):
            nx["data"]["highlight"] = ' #80FF66'
            nx["data"]["border_width"] = 2.0
            nx["classes"]="pink"
        else:
            nx["data"]["highlight"] = 'grey'           
                
        final["nodes"].append(nx)
        
    for index, row in edges.iterrows():
        nx = {}
        nx["data"] = {}            
        nx["data"]["id"] = "e"+str(uuid.uuid4())
        nx["data"]["source"]=row['Source1']
        nx["data"]["target"]=row['Target1']
        final["edges"].append(nx)

    ## create legend
    legend_bubbles = [10,20,40,80,160]
    
    for el in legend_bubbles:
        legend_node = {}
        legend_node["data"] = {}            
        legend_node["data"]["id"] = 'n = '+str(el)
        legend_node["data"]["label"] = str(el) 
        legend_node["data"]["font-size"] = 5,
        legend_node["data"]["shape"] = 'ellipse'
        legend_node["data"]["sector1"] = 0
        legend_node["data"]["sector2"] = 100
        legend_node["data"]["sector3"] = 0
        legend_node["data"]["size"] = math.sqrt(el*100)
        legend_node["data"]["valign"] = 'top'
        legend_node["data"]["halign"] = 'center'
        legend_node["data"]["highlight"] = 'grey'                         
        final["nodes"].append(legend_node)
        
    for elem in legend_bubbles:                  
        if (legend_bubbles.index(elem))+1 != len(legend_bubbles):
            thiselem = elem
            nextelem = legend_bubbles[legend_bubbles.index(elem)+1]                
            legend_e1 = {}
            legend_e1["data"] = {}            
            legend_e1["data"]["id"] = "e"+str(uuid.uuid4())
            legend_e1["data"]["source"]='n = '+str(thiselem)
            legend_e1["data"]["target"]='n = '+str(nextelem)
            final["edges"].append(legend_e1)
    
    elements = final["nodes"]+ final["edges"]
    
    return elements, sig_stat_all_df, final["nodes"], final["edges"]


def get_abbr():

    LM_abbreviations = pd.read_excel('./data/LM_list_of_abbreviations.xlsx')
    LM_abbreviations['Abbreviation'] =  LM_abbreviations['Abbreviation'].apply(lambda x: x.replace('[','').replace(']',''))

    return LM_abbreviations