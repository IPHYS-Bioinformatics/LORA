import plotly.express as px
import pandas as pd

import plotly.graph_objects as go
import pandas as pd
import itertools
import numpy as np
from plotly.subplots import make_subplots
import plotly.express as px

import textwrap

def dict_intersect_multi(dict_inter, dict_exter):
    common_items =  dict_inter[0].items()
    for d in dict_inter[1:]:
        common_items &= d.items()
    for et in dict_exter[0:]:
        common_items -= et.items()
    return common_items

def upset_filter_df(df, filter_values):
    """Filter df by matching targets for multiple columns.

    Args:
        df (pd.DataFrame): dataframe
        filter_values (None or dict): Dictionary of the form:
                `{<field>: <target_values_list>}`
            used to filter columns data.
    """
    import numpy as np
    if filter_values is None or not filter_values:
        return df
    return df[
        np.logical_and.reduce([
            df[column].isin(target_values) 
            for column, target_values in filter_values.items()
        ])
    ]

def plotly_upset_plot_pivot(df, limit):
    df_with_names = df.copy(deep=True)  
    df = df.drop(['Names'], axis=1)
    df = (df <= limit) * 1

    df_minima = df.min().sort_values(ascending = True)
    min_list = df_minima.index.to_list()
    if len(min_list) > 13:
        df = df[min_list[:13]]
    else:
        pass  
    
    df_header_list = list(df.columns.values)
    dict_of_dict = {}
    for name in df_header_list:
        temp_dict = df[name].to_dict()
        temp_filtered = {key : val for key, val in temp_dict.items() if val >= 1}
        dict_of_dict[name] = temp_filtered

    subsets = []
    d = len(df_header_list)
    for i in range(1, d + 1):
        subsets = subsets + [list(x) for x in list(itertools.combinations(df_header_list, i))]
    subset_sizes = []
    for s in subsets:
        inter = []
        for term in s:
            inter.append(dict_of_dict[term])
        exter = []
        others_list = [ele for ele in df_header_list if ele not in s]
        for term in others_list:
            exter.append(dict_of_dict[term])

        tmp = dict_intersect_multi(inter, exter)
        subset_sizes.append(len(tmp))
                   
    plot_df = pd.DataFrame({'Intersection': subsets, 'Size':subset_sizes,'Counts':'1','Values':subsets})        
   
    for index, row in plot_df.iterrows():
        temp_row = row['Intersection']
        plot_df.at[index,'Counts'] = len(temp_row)

    plot_df = plot_df.sort_values(['Counts','Size'], ascending = [True,True])
    plot_df.reset_index(drop=True, inplace=True)

    plot_df = plot_df[(plot_df['Size']>0) & (plot_df['Counts']>1)]      
    plot_df.reset_index(drop=True, inplace=True)
    max_y = max(plot_df['Size'])+0.1*max(plot_df['Size'])

    ## GENERATE TABLES for intersections > 1 and counts > 0
    selected_overlap = plot_df[(plot_df['Counts']>1) & (plot_df['Size']>0)].sort_values(by = 'Counts', ascending = False)
    selected_overlap = plot_df.copy(deep=True)
    selected_overlap = selected_overlap['Intersection']
    
    for index, row in plot_df.iterrows():
        plot_df.at[index,'Bar'] = 'Bar'+str(index) 
    
    dict_of_tables = {}
    dict_of_table_keys = plot_df['Bar']
    
    for index, list_in_row in selected_overlap.items():
        search_list = list(list_in_row)
        full_list = list(df.columns)
        temp_s = set(search_list)
        difference = [x for x in full_list if x not in temp_s]
        temp_df = df_with_names
        final_df = temp_df[(temp_df[[c for c, t in zip(temp_df.columns.intersection(search_list), temp_df.dtypes) if pd.api.types.is_float_dtype(t)]]<=limit).all(axis=1) & (temp_df[[c for c, t in zip(temp_df.columns.intersection(difference), temp_df.dtypes) if pd.api.types.is_float_dtype(t)]]>=limit).all(axis=1)]
        temp_melted = final_df.melt(id_vars=['Names'], value_vars=list(list_in_row))
        if(final_df.empty):
            plot_df.at[index, 'Values']= []
        else:
            plot_df.at[index, 'Values']= list(temp_melted['value'])
            search_list.insert(0, "Names")
            table_df=final_df[search_list] 
            table_df = table_df.applymap(lambda x: np.nan if x == 1.0000 else x)
            table_df.dropna(inplace=True)

            table_df = table_df.drop_duplicates(subset='Names', keep='first')
            table_df['Names'] = table_df['Names'].str.replace(r'\(.*\)$', '', regex=True)

            temp_key = 'Bar'+str(index)
            dict_of_tables[temp_key] = table_df.to_dict()

    VIL = dict_of_tables['Bar'+str(len(dict_of_tables)-1)]
    
    for index, row in plot_df.iterrows():
        temp_row = row['Values']
        plot_df.at[index,'Counts_pval'] = len(temp_row) 
    
    return df, plot_df, subsets, dict_of_tables, VIL

def plotly_upset_figure(plot_df, original_df, subsets, limit):
    plot_df = plot_df
    df = original_df

    subsets = subsets
    limit = limit
    max_y = max(plot_df['Size'])+0.1*max(plot_df['Size'])
    d = len(df.columns)

    ## DEFINE FIG PARAMETERS
    base = (d*(-3.5))+160
    part = base/(d*base)
    height_row_1 = part
    height_row_2 = 1-(2*part)
    height_row_3 = part
    font_size=(0.333*d)+10

    ## START PLOTTING  
    fig = make_subplots(
        rows=3, cols=3,
        column_widths=[0.5,0.25,0.25],
        row_width=[height_row_1,height_row_2,height_row_3],
        horizontal_spacing=0.01,
        vertical_spacing=0.01,
        subplot_titles=('','','','','','','','',''),
        print_grid=True,
        )   

    ## GLOBAL PLOT OPTIONS 
    dot_size = {2:14,3:13,4:12,5:11,6:10,7:10,8:10,9:10,10:10,11:10,12:10,13:10,14:10,15:10}
    subsets = list(plot_df['Intersection'])
    n_colors = len(subsets)
    colors = px.colors.sample_colorscale("turbo", [n/(n_colors) for n in range(n_colors)])  
    hover_wrap = plot_df['Intersection'].tolist()
    intersections_wrap = []
    for item in hover_wrap:
        itemstring = '<br>'.join([str(elem) for elem in item])        
        intersections_wrap.append(itemstring)     
    template =  [f'<extra><br><b>{lab}</b><br><b>Cardinality count</b>: {n}</extra>' for  lab, n in zip(intersections_wrap, plot_df['Size'])]
    dot_template = [f'<extra><br>{lab}<br><b>Intersections</b>: {n}</extra>' for  lab, n in zip(intersections_wrap, plot_df['Counts'])]
    pval_template = [f'<extra><br>{lab}</extra>' for  lab in intersections_wrap]
    subsets = list(plot_df['Intersection'])

    ## WHITE DOTPLOT row=2 col=1   
    scatter_x = []
    scatter_y = []
    for i, s in enumerate(subsets):
        for j in range(d):
            scatter_x.append(i)
            scatter_y.append(-j*max_y/d-0.1*max_y)   
    fig.add_trace(go.Scatter(x = scatter_y, y = scatter_x, mode = 'markers', hoverinfo='none', showlegend=False, marker=dict(size=dot_size[d],color='#C9C9C9')), row=2, col=1)
    fig.update_yaxes(showticklabels=False, title='Terms combination matrix', showgrid=True, gridcolor='white', tick0=0, dtick=100, range=[scatter_x[0]-1,scatter_x[-1]+1], row=2, col=1)
    fig.update_xaxes(visible=False, showticklabels=False, showgrid=True, row=2, col=1)

    ## BLACK DOTPLOT row=2 col=1
    for i, s in enumerate(subsets):
        scatter_x_has = []
        scatter_y_has = []
        for j in range(d):
            if df.columns[j] in s:
                scatter_x_has.append(i)
                scatter_y_has.append(-j*max_y/d-0.1*max_y)
                fig.add_trace(go.Scatter(x = scatter_y_has, y = scatter_x_has, mode = 'markers+lines', showlegend=False, hovertemplate=dot_template[i], marker=dict(size=dot_size[d],color='#000000',showscale=False)), row=2, col=1)
    
    ## STAT PLOT scatter graph row=2, col=3
    fig.add_trace(go.Scatter(x=scatter_x, y=[0.1]*len(scatter_x), mode = 'markers', showlegend=False, marker=dict(size=12,color='rgba(0, 0, 0, 0.0)')), row=2, col=3)   ## add transparent WHITE DOT plot to align X axes
    for i,s in enumerate(subsets):
        fig_stat=go.Scatter(x=plot_df['Values'][i], y=[i]*len(plot_df['Values'][i]), mode='markers', marker=dict(size=4, symbol='diamond', color=colors[i]), hovertemplate=pval_template[i], showlegend=False,)        
        fig.add_trace(fig_stat, row=2, col=3)
    fig.update_yaxes(showticklabels=False, gridcolor='white', tick0=0, dtick=1, showline=True, linewidth=1, linecolor='#696969', ticks="outside", tickwidth=0.5, tickcolor='#696969', ticklen=2, range=[scatter_x[0]-1,scatter_x[-1]+1], row=2, col=3)
    fig.update_xaxes(title='<em>p</em>-values within<br>term intersections', range=[-0.001,limit*1.1], ticks="outside", showline=True, linewidth=1, linecolor='#696969', title_font_size=font_size*0.8, row=2, col=3)    
    ## STAT PLOT ADD SECONDARY TOP X AXIS
    fig.data[1].update(xaxis='x3')
    fig.update_layout(xaxis3=dict(range=[-0.001,limit*1.1], side="top", position=height_row_2+height_row_3, tick0=0))
    fig.update_xaxes(title='<em>p</em>-values within<br>term intersections', range=[-0.001,limit*1.1], ticks="inside", showline=True, linewidth=1, linecolor='#696969', title_font_size=font_size*0.8, row=1, col=3)    

    ## CARDINALITY PLOT bar graph row=2, col=2
    plot_df['Intersection'] = ['+'.join(x) for x in plot_df['Intersection']]  
    fig_cardinality = go.Bar(y=list(range(len(subsets))), x=plot_df['Size'], orientation='h', marker=dict(color=colors), text=plot_df['Size'], customdata=plot_df['Bar'], hovertemplate=template, textposition='outside', hoverinfo='none', cliponaxis = False, showlegend=False)
    fig.add_trace(fig_cardinality, row=2, col=2)   
    fig.update_yaxes(showticklabels=False, gridcolor='white', tick0=0, dtick=1, showline=True, linewidth=1, linecolor='#696969', ticks="outside", tickwidth=0.5, tickcolor='#696969', range=[scatter_x[0]-1,scatter_x[-1]+1], ticklen=2, row=2, col=2)
    fig.update_xaxes(title='Cardinality [n]<br>term intersection size', gridcolor='white', range=[0,max_y], ticks="outside", showline=True, linewidth=1, linecolor='#696969', title_font_size=font_size*0.8, row=2, col=2)
    ## CARDINALITY ADD SECONDARY TOP X AXIS
    fig.data[3].update(xaxis='x2')
    fig.update_layout(xaxis2=dict(range=[0,max_y], side="top", position=height_row_2+height_row_3, tick0=0))       
    fig.update_xaxes(title='Cardinality [n]<br>term intersection size', gridcolor='white', range=[0,max_y], ticks="inside", showline=True, linewidth=1, linecolor='#696969', title_font_size=font_size*0.8, row=1, col=2)

    ## TOP BAR PLOT TERM NAMES 
    col_titles_list = df.columns.tolist()
    titles_wrap = []
    for item in col_titles_list:
        wrapped = textwrap.wrap(item, width=20, break_long_words=False)
        newone = '<br>'.join(wrapped)
        titles_wrap.append(newone) 
    fig_names = go.Bar(y=[1]*d, x=df.columns, name="(names)", marker = dict(color='white'), text=titles_wrap, insidetextanchor="start", hovertemplate=titles_wrap, textangle = -90, cliponaxis = False, textposition='inside', showlegend=False)
    fig.add_trace(fig_names, row=1, col=1)
    fig.update_yaxes(title='Top significant terms', showticklabels=False, title_font_size=font_size*0.9, row=1, col=1)
    fig.update_xaxes(visible=False, autorange="reversed",showticklabels=False, row=1, col=1)   
    
    ## BOTTOM BAR PLOT TERM SIZES sets row=3 col=1        
    df_sum = df[df > 0].count()
    fig_sets = go.Bar(y=df_sum, x = scatter_y, marker = dict(color='#00CCCC'), textposition='outside', texttemplate='%{y}', hoverinfo='none', insidetextanchor="start", cliponaxis = False, showlegend=False)
    fig.add_trace(fig_sets, row=3, col=1)
    fig.update_yaxes(title='Term size [n]', showticklabels=True, range=[0,max(fig_sets.y)*1.2], showline=True, linewidth=1, linecolor='black', ticks="outside", tickwidth=0.5, tickcolor='#696969', ticklen=2, row=3, col=1)
    fig.update_xaxes(showticklabels=False, showline=True, linewidth=1, linecolor='black', row=3, col=1)
    
    ## final figure layout
    fig.update_layout(height=base*(d+1), width=base*d, plot_bgcolor='rgba(248,248,248,0.9)', margin=dict(l=20, r=20, t=20, b=20))

    return fig