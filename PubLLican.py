import sys, time, os
import openai
import pandas as pd
import traceback
import types
import pickle
import json, re
vb_cache_file = "vdb.pickle"
from chatGPTModel import call_gpt_chat_api
from GetSummary import get_summary, get_genes_full, trim_genes, MAX_GENES, reply_to_list
from CallJsonAPI import get_go_description, check_gene


species_prompt = "From the following summary, identify any Eukaryotic or prokaryotic species or genus that are the subject of study." + \
"Reply in JSON format, with no other commentary.for example: [\"Aspergillus brasiliensis\", \"Plasmodium malariae\"].  The summary text follows:  "

vbdata = {}

def load_vuepath():
    global vbdata
    if os.path.exists(vb_cache_file):
        with open(vb_cache_file, 'rb') as file:
            vbdata = pickle.load(file)

        return
    #The full data from VuePathdb is very large, so the data and code is not included
    #the only data included is the list of species and genes





def get_species(summary):
    prompt = species_prompt + summary
    res = call_gpt_chat_api(prompt)
    text = res.get_completion_text(res)

    words = text.split(",")
    db_words = []
    try:
        gene_json = json.loads(text)
        for g in gene_json:
            db_words.append(g)

    except ValueError:

        for word in words:
            found = 0
            for x in vbdata["organism"]:
                found = found + (word in x)

            if found > 0:
                db_words.append(word)

    return db_words


def get_abstract(filename):
    test_file = open(filename,"r")
    abstract = ""

    for line in test_file:
        abstract =  abstract + line.rstrip()+" "

    return abstract



#print(models)


def confirm_gpt_go_terms(abstract, gos, gene):
    results = []
    for go in gos:
        desc = get_go_description(go)
        label = get_go_description(go,"label")
        result = types.SimpleNamespace()

        if len(desc) > 10:


            result.ok = True
            prompt = "Give a one-word answer from [ None/ Low / Medium / High / Certain ] for how likely the gene "+gene+" is involved with "+desc +\
                     ". Based on this summary: " + abstract + \
                     " "
            #res = call_gpt_api(prompt)

            res = call_gpt_chat_api(prompt)


            result = types.SimpleNamespace()
            result.res = res



            result.term = go
            result.prompt = prompt
            result.label = label
            result.desc = desc
            results.append(result)

    return (results)


#not used
def confirm_gpt_text(abstract,desc, gene):
    descriptions = ",".join(desc)
    prompt = "input: Give a rating of low, medium, or high for each of these gene ontology descriptions : '" + descriptions + "' according to how likely it is to be related to the Gene "+gene+", based on this abstract: " + abstract + \
            " "
    return(call_gpt_chat_api(prompt))


#merge results from different prompts
def get_gpt_text(abstract, gene):
    prompt="Give the answer in JSON format with no other commentary.  What are the the most likely Gene Ontology terms,  such as [\"Apoptotic Process (GO:0006915)\",\"Pseudokinase Activity (GO:0017076)\"]  that are most likely to be related to the genes "+gene+" based on the following abstract: " + abstract+"  . Return the answer as a JSON object."


    return (call_gpt_chat_api(prompt))

def get_gpt_text_v2(abstract, gene):
    prompt = "Give the answer in JSON format with no other commentary.  What Gene Ontology terms,  such as [\"Apoptotic Process (GO:0006915)\",\"Pseudokinase Activity (GO:0017076)\"]  that are most likely to be related to the genes " + gene + " based on the following abstract: " + abstract + "  . Return the answer as a JSON object."


    return (call_gpt_chat_api(prompt))

def get_gpt_text_v3(abstract, gene):
    prompt = "Give the answer in JSON format  with no other commentary.  Name all of the Gene Ontology terms,  such as [\"Apoptotic Process (GO:0006915)\",\"Pseudokinase Activity (GO:0017076)\"]  that are most likely to be related to the Gene " + gene + " based on the following abstract: " + abstract + "  . Return the answer as a JSON object."
    #prompt=" Give all Gene Ontology terms,  such as [\"Apoptotic Process (GO:0006915)\",\"Pseudokinase Activity (GO:0017076)\"] that could have a function related to the Gene "+gene+" ,  based on the following summary: " + abstract+"  . Return the answer as a JSON object."
    return (call_gpt_chat_api(prompt))



def get_go_terms(summary):
    # this assumes the ids  always start with (GO:
    # line breaks or commas inside an id will break things

    paragraph = summary.split("\n")
    go_terms = {}
    for line in paragraph:
        parts = line.split(",")

        for part in parts:

            key = None
            while True:
                s = part.find("(GO:")

                if s > -1:
                    value = set()
                    term = part[:s]
                    options = term.split(" or ")
                    for term in options:
                        term = term.strip().lower()
                        value.add(term)

                    part = part[s+1:]
                    e = part.find(")")
                    if e > -1:
                        term = part[ :e]

                        key = term.strip().lower()

                        if key not in go_terms:
                            go_terms[key] = set()
                        for v in value:
                            val1 = v.strip().lower()

                            parts = val1.split(".")
                            if (len(parts) == 2):
                                if len(parts[0]) < 4:
                                    val1 = parts[1]

                            go_terms[key].add(val1)

                else:
                    break



    return go_terms

def maxword_match(string1, string2):
    words1 = string1.split(" ")
    words2 = string2.split(" ")
    match = True
    for w in words1:
        if not w in words2:
            match = False;
    if match == False:
        match = True
        for w in words2:
            if not w in words1:
                match = False;
    return match

def check_genes_ids(genes):
    #check if the abstract contains the protein ids
    #return true if it does
    #return false if it does not
    #return false


    examples_list = ["PF3D7_1409300", "PRCDC_1109500", "PCHAS_0206700", "PY17X_0209700"]
    examples_text = " ".join(examples_list)
    genes_text = ", ".join(genes)
    prompt = " A gene identifier is a canonical id allocated by a central database to uniquely identify a single gene. They are typically in the format "+\
    examples_text+" etc. Give answer as JSON format with no other commentary. Which of the following terms appear to be gene identifiers? "+genes_text +". Reminder, Give answer as JSON format with no other commentary."




    res = call_gpt_chat_api(prompt)
    text = res.get_completion_text(res)
    words = reply_to_list(text)


    fwords = []

    try:
        for word in words:
            if word not in examples_list:
                if word.count("_") == 1:
                    if sum(c.isdigit() for c in word) > 1:
                        fwords.append(word)
    except:
        print("error in check_genes_ids",words)

    return fwords



def get_go_terms_from_text(abstract,genes, full_text):

    #use of vuepathdb terms has been removed
#    terms_data = load_terms()
#    terms = terms_data["lower_terms"]
#    matches = terms_data["matches"]

#trying some varitions, as we often get different results

    gene=", ".join(genes)
    completions = get_gpt_text(abstract,gene)
    terms_text = completions.get_completion_list(completions)

    #completions = get_gpt_text_v2(abstract, gene)
    #terms_text = terms_text + completions.get_completion_list(completions)
    #completions = get_gpt_text_v3(abstract, gene)
    #terms_text = terms_text + completions.get_completion_list(completions)

    go_terms = get_go_terms(terms_text)

    all_descriptions = set()
    bad_terms = set()
    for go in go_terms:
        go_desc = get_go_description(go)
        go_label = get_go_description(go,"label")

        descriptions = go_terms[go]


        for desc in descriptions:
            match = False
            matchreason = "term is sound"
            go_db_desc = get_go_description(go, "label")

            if (maxword_match(desc,go_db_desc)):
                    matchreason = "word match to db"
                    match = True
               # all_descriptions.add(desc)

            if desc.strip().lower() == go_label.strip().lower():
                match = True
                matchreason = "term is identical"


            if match == False:
                prompt = " Does the term " + desc + " mean the same thing as " + go_label+". Please give the answer are Yes or No."

                res = call_gpt_chat_api(prompt)
                text = res.get_completion_text(res)
                if text.lower()[:3]== "yes":
                    match = True
                    matchreason = "GPT matched terms"


            #these are only the descriptions for the go termms
            if match:
                all_descriptions.add(go+" ("+desc+")")
                #print(go, "matches", desc, matchreason)
            else:
                #print(go, "discarded ",desc)
                bad_terms.add(go)

    #remove the terms that did not match their description
    for b in bad_terms:
        go_terms.pop(b)

# get the final confirmation, based on the description
    go_terms_confirm = confirm_gpt_go_terms(abstract, go_terms,gene)

    result_text = ""


    results = []

    for res in go_terms_confirm:

        result = res.res.get_completion_text(res.res)
        result = result.split(".")[0]
        result = result.strip().lower()

        res_obj = {}
        res_obj["go_gene"] = genes
        res_obj["go_id"] = res.term
        res_obj["go_label"] = res.label
        res_obj["class"] = result


        full_words = full_text.split(" ")



        results.append(res_obj)

        if (result != "none") and (result != "low"):
            result_text = result_text + result + "," + res.term + "," + res.label +"\n"



    return results


def check_gene_species(gene,species):
    gene_data = vbdata["genes"]
    if gene not in gene_data:
        return False
    spec_list = gene_data[gene]
    found = 0
    for vbspec in spec_list:
        if species in vbspec:
            found = found + 1


    if found == 0:
        return False

    return True
sys.stdout.reconfigure(encoding='utf-8')
def get_go_terms_from_pdf(pdf):
    print("START")
    output = {}
    load_vuepath()

    [summary_text,genes, full_text] = get_summary(pdf)

    print("GOT summary and genes: ", genes)

    output_text = ""

    species = get_species(summary_text)


    if (len(genes) < 1):
        genes   = get_genes_full(summary_text,species)


    print("Got Species: ", species)

    if  len(species) == 0:
        output_text = "No relevant species were identified"
    else:
        output_text = "Checking for species: "
        output["species"] = species
        for spec in species:
            output_text = output_text + spec +" "
        output_text = output_text + "\n\n"


    gene_ids = check_genes_ids(genes)
    #if len(genes) > MAX_GENES:

    genes = trim_genes(genes, summary_text)

    print("Possible genes: ", genes)
    output["possible_genes"] = genes
#will use ids if they are available
    use_ids = False
    if len(gene_ids) > 1:
        genes = gene_ids
        use_ids = True
        print("Possible gene ids: ", genes)
        output["gene_ids"] = genes

    spec_genes = []

    output["go_terms"] = []
    if len(genes) < 6:
     for gene in genes:
        # checks with EBI / Uniprot
        # if check_gene(gene)==False:
        #    continue
        if use_ids:
            spec_genes.append(gene)
        else:
            countspec = 0

            for spec in species:
                if check_gene_species(gene,spec):
                    countspec = countspec+1
            if countspec ==0:
                continue
            spec_genes.append(gene)


        result = get_go_terms_from_text(summary_text,gene, full_text)
        if (len(result))>0:
            output_text = output_text + "Summary for gene: " + gene +"\n"
            for r in result:
                output_text = output_text + r["go_id"] + "," + r["go_label"] + "," + r["class"] + "\n"

            for r in result:
                output["go_terms"].append(r)



    if len(spec_genes) ==0:
        result = get_go_terms_from_text(summary_text,"Unspecified")


        if (len(result))>0:
            output_text = output_text + "Summary\n"
            for r in result:
                output_text = output_text+r["go_id"]+","+r["go_label"]+","+r["class"]+"\n"
            for r in result:
                output["go_terms"].append(r)

    print(output_text)
    print("END")
    return output



def get_terms_wrapper(pdf,pmid):
    fallback = 16
    fails = 0
    result = ""


    #it retries on errors in case of a live system
    #api ratelimit errors are common, but others may occur due to connection problems
    while True:
        try:
            result = get_go_terms_from_pdf(pdf)
            fallback = 16
            fails = 0
            break
        except Exception as e:
            if type(e) == openai.error.RateLimitError:
                fails = fails + 1
                print("api wait", fallback)
            else:
                #some other error, may be fatal, but could be not available
                fails = fails + 4
                print("error wait", fallback, e)
                traceback.print_exc()
            time.sleep(fallback)
            fallback = fallback * 1.5

        # after 30 minutes, just give up
        #
        if fails > 10:
            return  []
    out_file =  pdf + ".go.json"

    result["file"] = pdf
    result["pmid"] = pmid

    result_json=json.dumps(result)
    with open(out_file, 'w') as outfile:
        outfile.write(result_json)


    return result



def process_paper(file):

    id=""
    if os.path.exists(file) == False:
        print("File not found: ", file)
        return None

    answer = get_terms_wrapper(file,id)
    return answer



if __name__ == "__main__":

    file = "test.pdf"
    if len( sys.argv ) > 1:
        file = sys.argv[1]

    data = process_paper(file)

# The data is also  written to json file for automated processing
# it can be viewed with :

    #json_formatted_str = json.dumps(data, indent=2)
    #print(json_formatted_str)


