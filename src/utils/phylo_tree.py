from collections import defaultdict
from dict2xml import dict2xml
from xml.dom.minidom import parseString
import pandas as pd

from Bio import Phylo
from Bio.Phylo import PhyloXML as PX
import numpy as np
import plotly.graph_objs as go
from itertools import groupby

def phylo_recursive_tree():
    return defaultdict(phylo_recursive_tree)  

def phylo_subtree_setup(name, a_dict):
    my_dict = {'name': name}   
    if a_dict.keys():
        my_dict["clade"] = [phylo_subtree_setup(key, val) for key, val in a_dict.items()]        
    return my_dict

def phylo_create_phyloXML(df, session_id):
    """
    Convert tabular hierarchy - Goslin levels - into phylogenetic tree.
    Input: df with all Lipid Shorthand levels from jgoslin or selected columns
    Output: phyloXML file saved to disk or session    
    """ 
    
    T = phylo_recursive_tree() 

    c = ['Normalized Name','Lipid Shorthand CATEGORY','Lipid Shorthand CLASS','Lipid Shorthand SPECIES','Lipid Shorthand MOLECULAR_SPECIES','Lipid Shorthand SN_POSITION','Lipid Shorthand STRUCTURE_DEFINED','Lipid Shorthand FULL_STRUCTURE','Lipid Shorthand COMPLETE_STRUCTURE']

    for _, row in df.iterrows():
        subdict = T[row[c[1]]]   
        for col in c[2:]: 
            if not isinstance(row[col], float):
                subdict = subdict[row[col]]
    dict_list = [] 
    for name, a_dict in T.items():   
        dict_list.append(phylo_subtree_setup(name, a_dict))
    
    D = {'name': 'Lipidome', 'clade': dict_list}
    level_CATEGORY=len(D['clade'])
    
    for i in range(level_CATEGORY):
        D['clade'][i]['branch_length'] = 0.15
        D['clade'][i]['property'] = D['clade'][i]['name']
        D['clade'][i]['confidence'] = int(i+1)
        try:
            cyklus_j = len(D['clade'][i]['clade'])        
            for j in range(cyklus_j):
                D['clade'][i]['clade'][j]['branch_length'] = 0.6
                D['clade'][i]['clade'][j]['property'] = D['clade'][i]['name']
                D['clade'][i]['clade'][j]['confidence'] = int(i+1)
                try: 
                    cyklus_k = len(D['clade'][i]['clade'][j]['clade'])
                    for k in range(cyklus_k):
                        D['clade'][i]['clade'][j]['clade'][k]['branch_length'] = 0.2
                        D['clade'][i]['clade'][j]['clade'][k]['property'] = D['clade'][i]['name']
                        D['clade'][i]['clade'][j]['clade'][k]['confidence'] = int(i+1)
                        try:
                            cyklus_l = len(D['clade'][i]['clade'][j]['clade'][k]['clade'])          
                            for l in range(cyklus_l):
                                D['clade'][i]['clade'][j]['clade'][k]['clade'][l]['branch_length'] = 0.0501
                                D['clade'][i]['clade'][j]['clade'][k]['clade'][l]['property'] = D['clade'][i]['name']
                                D['clade'][i]['clade'][j]['clade'][k]['clade'][l]['confidence'] = int(i+1)
                                try:
                                    cyklus_m = len(D['clade'][i]['clade'][j]['clade'][k]['clade'][l]['clade']) 
                                    for m in range(cyklus_m):
                                        D['clade'][i]['clade'][j]['clade'][k]['clade'][l]['clade'][m]['branch_length'] = 0.0502
                                        D['clade'][i]['clade'][j]['clade'][k]['clade'][l]['clade'][m]['property'] = D['clade'][i]['name']
                                        D['clade'][i]['clade'][j]['clade'][k]['clade'][l]['clade'][m]['confidence'] = int(i+1)
                                        try:
                                            cyklus_n = len(D['clade'][i]['clade'][j]['clade'][k]['clade'][l]['clade'][m]['clade']) 
                                            for n in range(cyklus_n):
                                                D['clade'][i]['clade'][j]['clade'][k]['clade'][l]['clade'][m]['clade'][n]['branch_length'] = 0.0503
                                                D['clade'][i]['clade'][j]['clade'][k]['clade'][l]['clade'][m]['clade'][n]['property'] = D['clade'][i]['name']
                                                D['clade'][i]['clade'][j]['clade'][k]['clade'][l]['clade'][m]['clade'][n]['confidence'] = int(i+1)
                                                try:
                                                    cyklus_o = len(D['clade'][i]['clade'][j]['clade'][k]['clade'][l]['clade'][m]['clade'][n]['clade']) 
                                                    for o in range(cyklus_o):
                                                        D['clade'][i]['clade'][j]['clade'][k]['clade'][l]['clade'][m]['clade'][n]['clade'][o]['branch_length'] = 0.0504
                                                        D['clade'][i]['clade'][j]['clade'][k]['clade'][l]['clade'][m]['clade'][n]['clade'][o]['property'] = D['clade'][i]['name']
                                                        D['clade'][i]['clade'][j]['clade'][k]['clade'][l]['clade'][m]['clade'][n]['clade'][o]['confidence'] = int(i+1)
                                                        try:
                                                            cyklus_p = len(D['clade'][i]['clade'][j]['clade'][k]['clade'][l]['clade'][m]['clade'][n]['clade'][o]['clade']) 
                                                            for p in range(cyklus_p):
                                                                D['clade'][i]['clade'][j]['clade'][k]['clade'][l]['clade'][m]['clade'][n]['clade'][o]['clade'][p]['branch_length'] = 0.0505          ## COMPETE_STRUCTURE
                                                                D['clade'][i]['clade'][j]['clade'][k]['clade'][l]['clade'][m]['clade'][n]['clade'][o]['clade'][p]['property'] = D['clade'][i]['name']
                                                                D['clade'][i]['clade'][j]['clade'][k]['clade'][l]['clade'][m]['clade'][n]['clade'][o]['clade'][p]['confidence'] = int(i+1)
                                                        except:
                                                            pass                                            
                                                except:
                                                    pass
                                        except:
                                            pass
                                except:
                                    pass
                        except:
                            pass
                except:
                    pass       
        except:
            pass

    xml = dict2xml(D, wrap ='phylogeny', indent ="   ")
    xml_body = xml[xml.find('\n') + 1: xml.rfind('\n')]

    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n<phyloxml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.phyloxml.org http://www.phyloxml.org/1.00/phyloxml.xsd" xmlns="http://www.phyloxml.org">\n<phylogeny rooted="true">\n<clade>\n'
    xml_footer = '\n<property>Lipidome</property><confidence type="bootstrap">0.1</confidence></clade>\n</phylogeny>\n</phyloxml>'
    
    final_xml = xml_header + xml_body + xml_footer
    final_xml = final_xml.replace('<confidence>','<confidence type="bootstrap">')   

    xmlfile = open("assets/"+session_id+"/phylo_lipids.xml", "w")
    xmlfile.write(final_xml)
    xmlfile.close()
    print('PhyloXML saved.')    
    return final_xml

def phylo_get_circular_tree_data(tree, order='level', dist=1, start_angle=0, end_angle=360, start_leaf='first'):

    """
    Define data needed to get the Plotly plot of a circular tree
    """

    start_angle *= np.pi/180
    end_angle *= np.pi/180
    
    def get_radius(tree):

        """
        Associates to  each clade root its radius, equal to the distance from that clade to the tree root
        returns dict {clade: node_radius}
        """
        node_radius = tree.depths()
        
        if not np.count_nonzero(node_radius.values()):
            node_radius = tree.depths(unit_branch_lengths=True)
        return node_radius
   
    
    def get_vertical_position(tree):

        """
        returns a dict {clade: ycoord}, where y-coord is the cartesian y-coordinate 
        of a  clade root in a rectangular phylogram
        
        """
        n_leafs = tree.count_terminals()
        
        if start_leaf == 'first':
            node_ycoord = dict((leaf, k) for k, leaf in enumerate(tree.get_terminals()))
        elif start_leaf == 'last':
            node_ycoord = dict((leaf, k) for k, leaf in enumerate(reversed(tree.get_terminals())))
        else:
            raise ValueError("start leaf can be only 'first' or 'last'")
            
        def assign_ycoord(clade):
            for subclade in clade:
                if subclade not in node_ycoord:
                    assign_ycoord(subclade)
            node_ycoord[clade] = 0.5 * (node_ycoord[clade.clades[0]] + node_ycoord[clade.clades[-1]])

        if tree.root.clades:
            assign_ycoord(tree.root)
        return node_ycoord

    node_radius = get_radius(tree)
    node_ycoord = get_vertical_position(tree)
    y_vals = node_ycoord.values()
    ymin, ymax = min(y_vals), max(y_vals)
    ymin -= dist
                
    def ycoord2theta(y):      
        return start_angle + (end_angle - start_angle) * (y-ymin) / float(ymax-ymin)

    
        

    def get_points_on_lines(linetype='radial', x_left=0, x_right=0, y_right=0,  y_bot=0, y_top=0):
        """
        - define the points that generate a radial branch and the circular arcs, perpendicular to that branch
         
        - a circular arc (angular linetype) is defined by 10 points on the segment of ends
        (x_bot, y_bot), (x_top, y_top) in the rectangular layout,
         mapped by the polar transformation into 10 points that are spline interpolated
        - returns for each linetype the lists X, Y, containing the x-coords, resp y-coords of the
        line representative points
        """
       
        if linetype == 'radial':
            theta = ycoord2theta(y_right) 
            X = [x_left*np.cos(theta), x_right*np.cos(theta), None]
            Y = [x_left*np.sin(theta), x_right*np.sin(theta), None]
        
        elif linetype == 'angular':
            theta_b = ycoord2theta(y_bot)
            theta_t = ycoord2theta(y_top)
            t = np.linspace(0,1, 10)
            theta = (1-t) * theta_b + t * theta_t
            X = list(x_right * np.cos(theta)) + [None]
            Y = list(x_right * np.sin(theta)) + [None]
        
        else:
            raise ValueError("linetype can be only 'radial' or 'angular'")
       
        return X,Y   
        
    

    def get_line_lists(clade,  x_left,  xlines, ylines, xarc, yarc):

        """
        Recursively compute the lists of points that span the tree branches
        """        
    
        x_right = node_radius[clade]
        y_right = node_ycoord[clade]   
        X,Y = get_points_on_lines(linetype='radial', x_left=x_left, x_right=x_right, y_right=y_right)   
        xlines.extend(X)
        ylines.extend(Y)   
        if clade.clades:           
            y_top = node_ycoord[clade.clades[0]]
            y_bot = node_ycoord[clade.clades[-1]]       
            X,Y = get_points_on_lines(linetype='angular',  x_right=x_right, y_bot=y_bot, y_top=y_top)
            xarc.extend(X)
            yarc.extend(Y)      
            for child in clade:
                get_line_lists(child, x_right, xlines, ylines, xarc, yarc)

    xlines = []
    ylines = []
    xarc = []
    yarc = []
    get_line_lists(tree.root,  0, xlines, ylines, xarc, yarc)  
    xnodes = []
    ynodes = []

    for clade in tree.find_clades(order='preorder'):
        theta = ycoord2theta(node_ycoord[clade])
        xnodes.append(node_radius[clade]*np.cos(theta))
        ynodes.append(node_radius[clade]*np.sin(theta))
        
    return xnodes, ynodes,  xlines, ylines, xarc, yarc


def phylo_number_to_color(list_of_numbers):                   
    color_list = [str(i) for i in list_of_numbers]
    color_list = list(map(lambda x: x.replace('0', 'black'), color_list))
    color_list = list(map(lambda x: x.replace('1', 'red'), color_list))
    color_list = list(map(lambda x: x.replace('2', 'lime'), color_list))
    color_list = list(map(lambda x: x.replace('3', 'cyan'), color_list))
    color_list = list(map(lambda x: x.replace('4', 'purple'), color_list))
    color_list = list(map(lambda x: x.replace('5', 'orange'), color_list))
    color_list = list(map(lambda x: x.replace('6', 'green'), color_list))
    color_list = list(map(lambda x: x.replace('7', 'blue'), color_list))
    color_list = list(map(lambda x: x.replace('8', 'magenta'), color_list))
    color_list = list(map(lambda x: x.replace('9', 'grey'), color_list))
    color_list = list(map(lambda x: x.replace('10', 'yellow'), color_list))
    return color_list


def phylo_create_circular_phylogram(phyloXML_file):
    """
    Plot circular phylogram of lipid levels, a radial tree
    Input: phyloXML file, simple scheme http://www.phyloxml.org/1.00/phyloxml.xsd
    Output: plotly figure    
    """ 
    
    tree = Phylo.read(phyloXML_file, 'phyloxml')
    traverse_order = 'preorder'

    all_clades=list(tree.find_clades(order=traverse_order))
    for k in range(len((all_clades))):
        all_clades[k].id=k
        all_clades[k].property=5

    inner_clades=list(tree.get_nonterminals(order=traverse_order))
    for k in range(len((inner_clades))):        
        inner_clades[k].property=2

    xnodes, ynodes, xlines, ylines, xarc, yarc = phylo_get_circular_tree_data(tree, order=traverse_order, start_leaf='last')

    tooltip=[]
    node_color=[]
    node_size=[]
    node_name=[]
    line_width=[]
    arc_color=[]
    arc_line_width=[]

    for clade in tree.find_clades(order=traverse_order):
        node_color.append(int(clade.confidence.value))
        node_size.append(int(clade.property))
        if clade.branch_length:
            if clade.branch_length==0.15 or clade.branch_length==0.6:
                node_name.append(clade.name)
                line_width.append(1)
            else:
                node_name.append('')
                line_width.append(0.2)
        else:
            node_name.append('')
            line_width.append(0.2)
        if clade.property==2:
            arc_color.append(int(clade.confidence.value))
            if (clade.branch_length==0.15 or clade.branch_length==0.6):
                arc_line_width.append(1)
            else:
                arc_line_width.append(0.2)
    
    tooltip_levels = {
        0.15:'CATEGORY',
        0.6:'CLASS',
        0.2:'SPECIES',
        0.0501:'MOLECULAR_SPECIES',
        0.0502:'SN_POSITION',
        0.0503:'STRUCTURE_DEFINED',
        0.0504:'FULL_STRUCTURE',
        0.0505:'COMPLETE_STRUCTURE'
        }
    for clade in tree.find_clades(order=traverse_order):
        if clade.name and clade.confidence and clade.branch_length:
            clade_tooltip_level = tooltip_levels.get(clade.branch_length)
            tooltip.append(f"<extra>Node name: {clade.name}<br>Level: {clade_tooltip_level}</extra>")
        else: 
            tooltip.append('')
    
    node_color = phylo_number_to_color(node_color)
    arc_color = phylo_number_to_color(arc_color)
    size=2
    
    fig = go.Figure()

    trace_nodes=dict(type='scatter',
           x=xnodes,
           y= ynodes, 
           mode='markers',
           marker=dict(color=node_color, size=node_size, line=dict(width=0.1,color='black') ),
           text=node_name,
           hovertemplate = tooltip,
           hoverinfo='text',
           opacity=0.9)
    fig.add_trace(trace_nodes)

    for i in range(0,len(xlines),3):
        one_x = []
        one_y = []
        one_x.append(xlines[i])
        one_x.append(xlines[i+1])
        one_y.append(ylines[i])
        one_y.append(ylines[i+1])                  
        if i>0:
            oneline = int(i/3)
        else:
            oneline = 0
        onetrace=dict(type='scatter',            
            x=one_x,
            y=one_y, 
            mode='lines',
            line=dict(color=node_color[oneline], width=line_width[oneline]),                       
            hoverinfo='none')
        fig.add_trace(onetrace)
    
    xarc_list = [list(group) for x, group in groupby(xarc, lambda x: x==None) if not x]
    yarc_list = [list(group) for x, group in groupby(yarc, lambda x: x==None) if not x]
    for i in range(0,len(xarc_list),1):
        onetrace=dict(type='scatter',            
            x=xarc_list[i],
            y=yarc_list[i], 
            mode='lines',
            line=dict(color=arc_color[i], width=arc_line_width[i], shape='spline'),                
            hoverinfo='none')
        fig.add_trace(onetrace)   
    
    layout=dict(
            font=dict(family='Arial',size=14),
            width=880,
            height=880,
            autosize=False,
            showlegend=False,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False), 
            hovermode='closest',
            plot_bgcolor='rgb(245,245,245)',
           )
    fig.update_layout(layout)
    fig.update_layout(paper_bgcolor='rgb(245, 245, 245)')

    for i in range(0,len(node_name),1):
        if len(node_name[i])>0:       
            fig.add_annotation(text=node_name[i], bgcolor="white", opacity=0.85, x=xnodes[i], y=ynodes[i], showarrow=False)

    return fig