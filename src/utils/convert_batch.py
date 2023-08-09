import pandas as pd
import numpy as np
import subprocess
from subprocess import PIPE, Popen
from io import StringIO
import os


def convert_table(df, grammar, path):

    '''
    Receiving a df containing a list of lipid names and processing with jgoslin

    Param
    -------
    df: dataframe
        contains lipid names
    grammar: string
             the chosen grammar to be used for parsing

    Returns
    -------
    df_new: dataframe
    '''

    def clean_file_data(filedata):
            return filedata.replace('"', '')

    def run_jgoslin_cli(input_list, java_cli, grammar):
        if grammar == 'LIPID':
            process = Popen(['java', '-jar', java_cli, '-f', input_list], stdout=PIPE, stderr=PIPE)
        else:
            process = Popen(['java', '-jar', java_cli, '-f', input_list, '-g', grammar], stdout=PIPE, stderr=PIPE)

        return process.communicate()

    input_file = path + '/goslin_in_data.txt'

    folder_path = 'assets'
    file_list = os.listdir(folder_path)
    jar_list = [f for f in file_list if f.endswith('.jar')]

    if len(jar_list) == 1:
        java_cli = os.path.join(folder_path, jar_list[0])
    else:
        raise ValueError(f'No or multiple jar files, expected in {folder_path}, expected just one.')
    

    df.to_csv(input_file, header=None, index=None)

    with open(input_file, 'r') as file:
        filedata = file.read()

    with open(input_file, 'w') as file:
        file.write(clean_file_data(filedata))

    try:
        result = run_jgoslin_cli(input_file, java_cli, grammar)
        table_in = StringIO(result[0].decode('utf-8'))
        df_new = pd.read_csv(table_in, sep='\t')
    except Exception as e:
        print('Java cli error:', e)
        return None

    os.remove(input_file)

    for column in df_new.columns:
        if 'SN Position' in column:
            df_new[column] = df_new[column].where(lambda x: x > 0, np.nan)

    return df_new