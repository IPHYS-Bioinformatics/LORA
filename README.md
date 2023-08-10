# LORA
LORA is the **L**ipid **O**ver-**R**epresentation **A**nalysis tool based on GOSLIN grammars

![LORA](/src/assets/TOC.jpg)

[LORA online](http://lora.metabolomics.fgu.cas.cz) webapplication
 
## Requirements
- Python 3.10+
- Java 17+

## Installation

### Linux

    $ git clone https://github.com/IPHYS-Bioinformatics/LORA.git
    $ cd LORA

Set up a Python virtual environment to isolate dependencies:

    $ python -m venv .LORA-venv

Enter the virtual environment:

    $ source .LORA-venv/bin/activate

Install LORA dependencies:
    
    $ pip install -r requirements-linux.txt

Change into the main source directory to run LORA:

    $ cd src/
    $ python index.py
    
and visit https://localhost:8050


### Windows

    git clone https://github.com/IPHYS-Bioinformatics/LORA.git
    cd LORA

Set up a Python virtual environment to isolate dependencies:

    python -m venv LORA-venv

Enter the virtual environment:

    LORA-venv\Scripts\activate

Install LORA dependencies:
    
    pip install -r requirements.txt

Change into the main source directory to run LORA:

    cd src
    python index.py
    
and visit [https://localhost:8050](http://127.0.0.1:8050)

## Test data

1. DEMO 1: src/data/demo_janovska_query.csv & demo_janovska_universe.csv - [Janovska et al. 2020](https://doi.org/10.1002/jcsm.12631), Figure 5D
2. DEMO 2: src/data/adipoatlas_query.csv & adipotlas_universe.csv - [Lange et al. 2021](https://doi.org/10.1016/j.xcrm.2021.100407), Figure 4A
3. DEMO 3: src/data/Query_Human_Lung_Endothelial_Cells.txt & Universe_Human_Lung_Endothelial_Cells.txt - [Clair et al. 2019](https://doi.org/10.1093/bioinformatics/btz250), LipidMiniOn test data
4. DEMO 4: src/data/Goslin_oxPE.txt & Goslin_oxPEq.txt - [Kopczynski et al. 2020](https://doi.org/10.1021/acs.analchem.0c01690), [Goslin test file](http://github.com/lifs-tools/goslin) and [Lauder et al. 2017](https://doi.org/10.1126/scisignal.aan2787), Figure 7A

## Using Docker

You can build the LORA Docker container by running

    $ docker build . -t lora

The container exposes port 8050 for the webapplication, you can run it as follows:

    $ docker run -it --rm --name lora -p 8050:8050 lora

Once the container has started, open your browser and open it at http://127.0.0.1:8050

You can stop the container with CTRL+c from the command line where you started it.

## Citation
LORA, Lipid Over-Representation Analysis Based on Structural Information. 
Michaela Vondrackova, Dominik Kopczynski, Nils Hoffmann, Ondrej Kuda
Analytical Chemistry 2023
[https://doi.org/10.1021/acs.analchem.3c02039]
## Related Projects
- [GOSLIN](http://github.com/lifs-tools/goslin), ([Goslin paper](https://doi.org/10.1021/acs.analchem.0c01690), [Goslin 2.0 paper](https://doi.org/10.1021/acs.analchem.1c05430))
- [GOSLIN Webapplication and REST API](https://github.com/lifs-tools/goslin-webapp)
- [LipidMiniOn](https://github.com/PNNL-Comp-Mass-Spec/LipidMiniOn)
- [LION](https://github.com/martijnmolenaar/lipidontology.com)
- [LipidLynxX](http://www.lipidmaps.org/lipidlynxx/), lipid ID converter and equalizer
- [LINEX2](https://exbio.wzw.tum.de/linex/)
- [lipidr](https://www.lipidr.org/index.html)
- [LipidSig](http://chenglab.cmu.edu.tw/lipidsig/)

## License
- LORA is licensed under the terms of the MIT license (see [LICENSE](LICENSE)).
- The Goslin grammars are licensed under the terms of the MIT license (see licenses).
- jgoslin Java Implementation is licensed under the terms of the Apache License v2 (see licenses).
