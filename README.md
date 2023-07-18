# PubLLican
Publication GO term annotation using ChatGPT

To use:

    pip install -r requirements.txt

Get an openAI API key, from openAI.com 

Save it in a text file called apikey.txt

    python publican.py <inputfile.pdf>

Output produced:

A summary of species, genes, and GO terms is printed to the console  
<inputfile>.as.txt : a text representation of the pdf  
<inputfile>.summary.txt : a text file summarising the publication  
<inputfile>.genes.txt : a text list of possible gene names found in the pdf  
<inputfile>.go.json the species, genes, and GO terms in machine-readable format  

The cache folder stores the results of API requests, so that these are not repeated (potentially incurring costs)
chatGPT is non-deterministic - the results you get may be different even with the same input

The following example is generated from the paper
"PI4-kinase and PfCDPK7 signaling regulate phospholipid biosynthesis in Plasmodium falciparum"
[https://pubmed.ncbi.nlm.nih.gov/34866326/]
PDF here: [https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8811644/pdf/EMBR-23-e54022.pdf]

| PubLLican Generated                          | Manually curated                   |
|----------------------------------------------|------------------------------------|
| **Species: Plasmodium falciparum**           | **Species: Plasmodium falciparum** |
|                                              |                                    |
| **Gene names**                               | **Gene Id (name)**                 |
|                                              |                                    |
| EK                                           | PF3D7_1124600 (EK)                 |
| PI4-kinase                                   | PF3D7_1343000 (PMT)                |
| PMT                                          | PF3D7_1123100 (CDPK7)              |
| PfCDPK7                                      |                                    |
| PfPI4K                                       |                                    |
|                                              |                                    |
| **GO terms**                                 | **Go Terms:**                      |
| GO:0006468                                   | GO:0006468                         |
| GO:0006629                                   | GO:0006656                         |
| GO:0008104                                   | GO:0005515                         |
| GO:0008654 (Grandparent of GO:0006656 )      | GO:0004672                         |
| GO:0006650 (Grandparent of GO:0006656 )      |                                    |
| GO:0006644 (Parent of GO:0008654/GO:0006650) |                                    |
| GO:0006631                                   |                                    |
