import pandas as pd
import dataframe_image as dfi

import os, shutil
from os.path import basename
import base64
import zipfile
from datetime import datetime

from fpdf import FPDF
from pages.layout import get_header_version


class PDF(FPDF):
    def __init__(self):
        super().__init__()
    def header(self):
        self.set_font('Arial', '', 10)
        self.cell(0, 8, 'LORA report', 0, 1, 'C')
        self.image('assets/parrot.png', x = 10, y = 8, w = 5, h = 5, type = 'PNG')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', '', 10)
        self.cell(0, 8, f'Page {self.page_no()}', 0, 0, 'C')


def reporter_store_zip_in_cache(zip_package, session_id, cache, report_path):
    with open(zip_package, "rb") as f:
        bytes = f.read()
        encoded = base64.b64encode(bytes)
    print(session_id+"_report")     
    cache.set(session_id+"_report", encoded) 
    #shutil.rmtree(report_path, ignore_errors=True, onerror=None)
    os.remove(zip_package)


def reporter_save_img_in_cache(figure, file_id, file_format, session_id, cache):
    img_bytes = figure.to_image(format=file_format, engine="kaleido")
    img_name = session_id+"_"+file_id+"_"+file_format
    cache.set(img_name, img_bytes)


def reporter_get_img_from_cache(file_id, file_format, session_id, cache):   
    figure = cache.get(session_id+"_"+file_id+"_"+file_format)      
    if cache.get(session_id+"_"+file_id+"_"+file_format) is not None:
        plot_bytes_encode = str(base64.b64encode(figure))
        plot_bytes_encode = plot_bytes_encode[0:-1]
        plot_bytes_encode_fin = plot_bytes_encode[2:]
        stringpic = "data:image/"+file_format+"+xml;base64," + plot_bytes_encode_fin        
        return stringpic
    else:
        print('Alert, image error')


def reporter_image_from_df(img_df, session_id):
    pd.set_option("display.max_column", None)
    pd.set_option("display.max_colwidth", 60)
    pd.set_option('display.max_rows', None)

    dfi.export(img_df, 'assets/'+session_id+'/VIL_table.png', table_conversion='matplotlib')
    

def get_jar_file():
    assets_dir = 'assets'
    files = os.listdir(assets_dir)
    jar_files = [f for f in files if os.path.splitext(f)[1] == '.jar']

    if len(jar_files) == 0:
        print('Error: No .jar files found in the assets directory.')
        jar_file='No .jar files found'
    else:
        jar_file = jar_files[0]

    return jar_file


def get_statistical_method_name(statistical_method):
    if statistical_method == 'fdr_bh':
        return 'False Discovery Rate (FDR; Benjamini/Hochberg)'
    elif statistical_method == 'bonferroni':
        return 'Bonferroni Correction (one-step correction)'
    elif statistical_method == 'holm':
        return 'Holm Correction (using Bonferroni adjustments)'
    else:
        return 'Unknown Statistical Method'


def reporter_create_pdf(session_id, parameters, statistical_test, alternative, statistical_method, alpha_level):

    report_filename='assets/'+session_id+'/LORA_report.pdf'

    ch = 8

    pdf = PDF()
    pdf.add_font("Arial", "", "assets/arial.ttf", uni=True)
    pdf.set_author('LORA https://lora.metabolomics.fgu.cas.cz')
    pdf.add_page()
    pdf.set_font('Arial', '', 24)
    pdf.cell(w=0, h=20, txt="Lipid Over-Representation Analysis (LORA) report", ln=1)
    
    pdf.set_font('Arial', '', 14)
    pdf.cell(w=40, h=ch, txt="Date: ", ln=0)
    pdf.cell(w=80, h=ch, txt=str(datetime.now().strftime('%Y-%m-%d-%H-%M-%S')), ln=1)
    pdf.cell(w=40, h=ch, txt="LORA version: ", ln=0)
    pdf.cell(w=80, h=ch, txt=get_header_version(), ln=1)
    pdf.cell(w=40, h=ch, txt="Goslin version: ", ln=0)
    pdf.cell(w=80, h=ch, txt=get_jar_file(), ln=1)    
    pdf.ln(ch)
    pdf.set_font('Arial', '', 10)

    ## add calculation parameters
    pdf.multi_cell(w=0, h=5, txt='Parameters used for the calculations: ' + str(parameters))
    pdf.ln(ch)

    ## add predefined terms    
    pdf.cell(w=0, h=ch, txt="Pre-defined structural terms:", ln=1)
    pdf.cell(w=80, h=ch, txt="Saturated chains", ln=0)
    pdf.cell(w=80, h=ch, txt="0 double bond", ln=1)
    pdf.cell(w=80, h=ch, txt="Monounsaturated chains", ln=0)
    pdf.cell(w=80, h=ch, txt="1 double bond", ln=1) 
    pdf.cell(w=80, h=ch, txt="Polyunsaturated chains", ln=0)
    pdf.cell(w=80, h=ch, txt="2 and more double bonds", ln=1) 
    pdf.ln(ch)
    pdf.cell(w=80, h=ch, txt="Chain with less than 16 carabon atoms", ln=0)
    pdf.cell(w=40, h=ch, txt="#C < 16", ln=1)
    pdf.cell(w=80, h=ch, txt="Chains with 16 to 18 carbon atoms", ln=0)
    pdf.cell(w=40, h=ch, txt="16 <= #C <=18", ln=1) 
    pdf.cell(w=80, h=ch, txt="Chains with more than 18 carbon atoms", ln=0)
    pdf.cell(w=40, h=ch, txt="#C > 18", ln=1)
    pdf.ln(ch)

    ## add test type and additional parameters
    pdf.cell(w=80, h=ch, txt="ORA test:", ln=0)
    pdf.cell(w=80, h=ch, txt=statistical_test, ln=1)
    pdf.cell(w=80, h=ch, txt="Alternative:", ln=0)
    pdf.cell(w=80, h=ch, txt=alternative, ln=1)
    pdf.cell(w=80, h=ch, txt="Multiple hypothesis testing:", ln=0)
    pdf.cell(w=80, h=ch, txt=get_statistical_method_name(statistical_method), ln=1)
    pdf.cell(w=80, h=ch, txt="Alpha-level:", ln=0)
    pdf.cell(w=80, h=ch, txt=alpha_level, ln=1)
    
    ## add VIL table
    pdf.add_page('L')
    pdf.set_font('Arial', '', 16)
    pdf.cell(40, 10, 'Very Important Lipid (VIL) table')
    pdf.ln(ch)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(w=0, h=5, txt='Lipid(s) that are present in most over-represented terms are defined as VIL(s).')
    pdf.ln(ch)
    pdf.image('assets/'+session_id+'/VIL_table.png', x = 10, y = None, w = 280, h = 0, type = 'png')
    pdf.ln(ch)
    pdf.multi_cell(w=0, h=5, txt='VIL table is included in the UpSet_intersection_tables.xlsx file.')
        
    ## add UpSet plot image
    pdf.add_page()
    pdf.set_font('Arial', '', 16)
    pdf.cell(40, 10, 'UpSet plot')
    pdf.ln(ch)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(w=0, h=5, txt='For the interactive version of the plot, use UpSet_plot_interactive.html from the report.')
    pdf.image('assets/'+session_id+'/UpSet_plot.jpg', x = 10, y = None, w = 180, h = 0, type = 'JPG')
    pdf.multi_cell(w=0, h=5, txt='► The UpSet plot can be used to identify the main structural features of enriched lipids and highlight the VILs in graphical representation.')
    pdf.multi_cell(w=0, h=5, txt='► Connected black dots represent the intersection of the terms labeled on top. The term intersection size (cardinality bar plot) represents the number of lipids that have this specific set of structural features. The p-value(s) belong to the particular lipids within individual terms (n lipids × m terms). The bar graph at the bottom shows how many lipids fit within the specified term.')
    pdf.multi_cell(w=0, h=5, txt='► The UpSet plot is sorted by the number of intersections and the term intersection size. Empty groups are omitted to reduce the figure size.')
    pdf.multi_cell(w=0, h=5, txt='► The plot is responsive. Click on the bar in the Cardinality bar plot to generate a table of lipids that belong to this specific term intersection.')
    pdf.multi_cell(w=0, h=5, txt='► The calculation limit is set to 13 terms as above for the VIL table.')
    pdf.ln(ch)
 
    ## add Cytoscape plot image
    pdf.add_page()
    pdf.set_font('Arial', '', 16)
    pdf.cell(40, 10, 'Lipid network')
    pdf.ln(ch)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(w=0, h=5, txt='For the interactive version of the plot, use te LORA application')
    pdf.multi_cell(w=0, h=5, txt='Network file cytoscape_network_json.cyjs from report zip file can be imported into Cytoscape for further evaluation.')
    pdf.multi_cell(w=0, h=5, txt='► File > Import > Network from File...')
    pdf.multi_cell(w=0, h=5, txt='► Select cytoscape_network_json.cyjs')
    pdf.multi_cell(w=0, h=5, txt='► Layout > Apply Preferred Layout (fCoSE, fast Compound Spring Embedder)')
    pdf.multi_cell(w=0, h=5, txt='► Style: Node and Edge Properties > select from lipidome data columns...')

    ## add Lipid tree image
    pdf.add_page()
    pdf.set_font('Arial', '', 16)
    pdf.cell(40, 10, 'Lipidome tree')
    pdf.ln(ch)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(w=0, h=5, txt='For the interactive version of the plot, use Lipid_tree_interactive.html from the report.')
    pdf.image('assets/'+session_id+'/Lipid_tree_plot.jpg', x = 10, y = None, w = 180, h = 0, type = 'JPG')       ## accepts only jpg and png
    pdf.multi_cell(w=0, h=5, txt='Use phylo_lipids.xml from zip report file for further eexploration of the lipidome.')
 
    ## add literature and links
    pdf.add_page()
    pdf.set_font('Arial', '', 16)
    pdf.cell(40, 10, 'Literature')
    pdf.set_font('Arial', '', 12)
    pdf.ln(ch)
    pdf.multi_cell(w=0, h=5, txt='► Kopczynski, D., Hoffmann, N., Peng, B., Liebisch, G., Spener, F., and Ahrends, R. (2022). Goslin 2.0 Implements the Recent Lipid Shorthand Nomenclature for MS-Derived Lipid Structures. Analytical Chemistry, 94(16), 6097–6101. https://doi.org/10.1021/acs.analchem.1c05430')       
    pdf.ln(ch)
    pdf.multi_cell(w=0, h=5, txt='► Kopczynski, D., Hoffmann, N., Peng, B., Ahrends, R. (2020). Goslin: A Grammar of Succinct Lipid Nomenclature. Analytical Chemistry, 92(16), 10957–10960. https://doi.org/10.1021/acs.analchem.0c01690')       
    pdf.ln(ch) 
    pdf.multi_cell(w=0, h=5, txt='Contact: ondrej.kuda@fgu.cas.cz')
    
    pdf.output(report_filename,'F')         ## save PDF locally     
    return pdf


def reporter_create_zip(session_id, report_path):
    with zipfile.ZipFile('assets/'+session_id+'_LORA_report.zip', "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zip_dir = report_path
        for root, dirs, files in os.walk(zip_dir):
            for filename in files:
                zf.write(os.path.join(root, filename), basename(os.path.join(root, filename)))


## create temp export directory, will be deleted soon
def create_dir(session_id):
    new_dir = str(session_id)
    parent_dir = 'assets/'
    report_path = os.path.join(parent_dir, new_dir)
    
    path_exists = os.path.exists(report_path)
    if(path_exists==True):
        print('')
    else:
        os.mkdir(report_path)
    return report_path


