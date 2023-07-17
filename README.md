# PubLLican
Publication GO term annotation using ChatGPT

#To use:
pip install -r requirements.txt

Get an openAI API key, from openAI.com 
Save it in a text file called apikey.txt

python publican.py <inputfile.pdf>

#Output produced:
A summary of species, genes, and GO terms is printed to the console
<inputfile>.as.txt : a text representation of the pdf
<inputfile>.summary.txt : a text file summarising the publication
<inputfile>.genes.txt : a text list of possible gene names found in the pdf
<inputfile>.go.json the species, genes, and GO terms in machine-readable format

The cache folder stores the results of API requests, so that these are not repeated (potentially incurring costs)
chatGPT is non-deterministic - the results you get may be different even with the same input


