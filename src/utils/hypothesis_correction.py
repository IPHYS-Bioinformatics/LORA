import statsmodels.stats.multitest as smt
import numpy as np


def hypothesis_correction(pvals, statistical_method, alpha_level):
    
    '''
    Calculate multiple hypothesis correction if the input array is not empty, otherwise returns N.D. (not defined)
     -> without this 'if' condition bonferroni and holm_bonferroni printed out error message: 'slice indices must be integers or none or have an __index__'

    Param
    -------
    pvals: numpy.ndarray
    statistical_method: string
    alpha_level: float

    Returns
    -------
    array_out: numpy.ndarray 
               
    '''

    if pvals != []:

        try:
            if statistical_method == 'fdr_bh':
                array_out = smt.multipletests(pvals=pvals, alpha=alpha_level, method=statistical_method, is_sorted=True)
            if statistical_method == 'bonferroni':
                array_out = smt.multipletests(pvals=pvals, alpha=alpha_level, method=statistical_method, is_sorted=True)
            if statistical_method == 'holm':
                array_out = smt.multipletests(pvals=pvals, alpha=alpha_level, method=statistical_method, is_sorted=True)
        except:
            print('Error in processing Hypothesis Correction')

    else:
        array_out = np.array([False])
    
    return array_out[0]