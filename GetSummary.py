
import openai
import json
import time, traceback, sys
import re
from io import StringIO
import pypandoc
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from chatGPTModel import call_gpt_chat_api
from CallJsonAPI import check_gene
import os

MAX_GENES = 5
base_prompt = "Re-write any results or conclusions from the following extract, in technical terms, and in no more than 500 words.  Make sure to include all discussed Gene names or identifiers and gene functions, gene ontology terms, or any protein related words, species or tissue types.  Describe any statistical results or biological conclusions in detail. The text is: "
base_prompt_final = "Describe in no more than 2000 words the results and conclusions of the following paper.  Make sure to include all gene names or identifiers and gene functions, gene ontology terms, or any protein related words, or any species or tissue types.    The text is: "
base_prompt_genes = " Give the answer as JSON  with no other commentary.  Which  biological Genes or genomic sequences are most relevant in the following summary.  The  summary follows: %s.   Give the answer as JSON  with no other commentary. Give a maximum of  "+str(MAX_GENES)+" genes."
base_prompt_genes2 = " Give the answer as a JSON list of names, with no other commentary.  Which  biological Genes or genomic sequences are most relevant in the following summary.  The  summary follows: %s.   Give the answer as JSON  with no other commentary. Give a maximum of  "+str(MAX_GENES)+" genes."
base_prompt_genes_full = "Give the answer as JSON  with no other commentary. Which  biological Genes or genomic sequences are most relevant to %s in the following article.  The article follows: %s  Give the answer as JSON  with no other commentary. Give a maximum of  "+str(MAX_GENES)+" genes."


USE_LARGE_TEXT = False

def get_genes_full(ftext,species):


    words = ftext.split(" ")


    genes = []

    while len(words) > 0:
        text = words[:3000]
        words=words[2500:]

        text = " ".join(text)
        bgenes = get_genes_part(text,species)
        for g in bgenes:
            if g not in genes:
                genes.append(g)

    #if len(genes) > MAX_GENES:
    genes = trim_genes(genes,ftext)

    return genes

def get_genes_part(text,species):


    species_text = ", ".join(species)
    prompt = base_prompt_genes_full.replace("%s",species_text)+" " + text

  #  print(prompt)

    genes = call_gpt_chat_api(prompt)


    genes_text = genes.get_completion_text(genes)


    genes = []
    try:
        gene_json = json.loads(genes_text)

        if (isinstance(gene_json , dict)) == False:
            gene_json = {"genes":gene_json}

        for ls in gene_json:
            for g in gene_json[ls]:
                genes.append(g)

    except ValueError:
        print("NOT JSON",genes_text)
        poss_genes = re.split("(,|\s|\.)", genes_text)


        for g in poss_genes:
            if len(g) > 2:
                genes.append(g)




    return genes

def get_genes(text,oprompt=None):

    prompt = base_prompt_genes.replace("%s", text)
    if oprompt != None:
        prompt = oprompt



    genes = call_gpt_chat_api(prompt)
    genes_text = genes.get_completion_text(genes)


    genes = []

    try:
        gene_json = json.loads(genes_text)
        if (isinstance(gene_json, dict)) == False:
            gene_json = {"genes": gene_json}

        for ls in gene_json:
            for g in gene_json[ls]:
                if (isinstance(g, dict)):
                    if oprompt == None:
                        prompt2 = base_prompt_genes2.replace("%s", text)
                        result = get_genes(text, prompt2)

                        return result
                    print("JSON FORMAT ERROR",g)
                    exit(1)
                genes.append(g)

    except ValueError:
        print("wasn't JSON",genes_text)
        poss_genes = re.split("(,|\s|\.)", genes_text)




        for g in poss_genes:
            if len(g) > 2:
                genes.append(g)
 #   genes.append("NRP1")
    return genes


def trim_references_text(text):
    words = text.split(" ")
    words = trim_references(words)
    text = " ".join(words)
    return text

def trim_references(words):
    numdoi = 0
    curpos = len(words)-1
    while (curpos > 0):
        curword = words[curpos].lower().strip()

        if curword.startswith("doi") and words[curpos+1].strip().startswith("org"):
            numdoi = numdoi + 1

        curpos = curpos - 1

        if len(curword) < 4:
            if curword.endswith("."):
                if curword[0].isdigit():
                    numdoi = numdoi + 1
        if ("crossref" in curword):
            numdoi = numdoi + 1
        if ("medline" in curword):
            numdoi = numdoi + 1
        if ("doi.org/" in curword):
            numdoi = numdoi + 1
        if ("references" in curword):
            if numdoi > 5:
                break



    if True:
     if curpos > 1:
        if curpos > len(words)/2:
            words = words[:curpos]

    return words
def reply_to_list(reply):
    words = []
    try:
        gene_json = json.loads(reply)

        if (isinstance(gene_json , dict)) == False:
            gene_json = {"genes":gene_json}

        for ls in gene_json:
            if (isinstance(gene_json, dict)):
                row = gene_json[ls]
                if (isinstance(row, list)):
                    for g in row:
                        words.append(g)
                else:
                    words.append(row)


            if (isinstance(gene_json, list)):
                for g in gene_json[ls]:
                    words.append(g)


    except ValueError:
        print("NOT JSON",reply)
        poss_genes = re.split("(,|\s|\.)", reply)


        for g in poss_genes:
            if len(g) > 2:
                words.append(g)
    return words

def trim_genes(ingenes, summary):



    validgenes = []
    for g in ingenes:
        if check_gene(g):
            validgenes.append(g)

    genes_text = ", ".join(validgenes)


    prompt = "Give the answer in JSON format with no other commentary. Which genes, from this list " + genes_text+" is the most important in influencing the results of the following article.  The article is: <code>"+summary+"</code> .  List at most "+str(MAX_GENES)+" genes"
    new_genes = call_gpt_chat_api(prompt)

    prompt = "Give the answer in JSON format with no other commentary. Which of the following genes: " + genes_text+" are not very relevant in influencing the results of the following article.  The article is: <code>"+summary+"</code> .  List at most "+str(MAX_GENES-1)+" genes"
    new_genes_out = call_gpt_chat_api(prompt)
    genes_out_text = new_genes_out.get_completion_text(new_genes_out)
    genes_text = new_genes.get_completion_text(new_genes)



    pgenes = reply_to_list(genes_text)
    out_genes = reply_to_list(genes_out_text)
    genes = []
    for g in pgenes:
        if g in out_genes:
            g = g
            #print("REMOVING",g)
        else:
            genes.append(g)


    genes = list(set(genes))
    genes.sort()

    return genes

def get_text_docx(file):
    out_file = file + ".as.txt"
    output = pypandoc.convert_file(file, 'plain')
    output = trim_references_text(output)
    with open(out_file, 'w', encoding='utf8') as outfile:
        outfile.write(output)


    return output



def get_text(pdf):

    out_file = pdf+".as.txt"



    if pdf.lower().endswith(".docx"):
        return get_text_docx(pdf)
    if pdf.lower().endswith(".doc"):
        return get_text_docx(pdf)

    #could read from saved file
    if os.path.exists(out_file):
        with open(out_file, 'r', encoding='utf8') as outfile:
            text = outfile.read()
            return text


    output_string = StringIO()
    with open(pdf, 'rb') as in_file:

        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)

        output = output_string.getvalue()
        output = trim_references_text(output)


        with open(out_file, 'w', encoding='utf8') as outfile:
             outfile.write(output)
        return output

def get_words(text):
    words = text.split(" ")
    return words

overlap =200
chunk_size = 1200
def get_chunk(words, page):
    wlen = len(words)
    start = page*chunk_size - overlap
    if (start < 0):
        start = 0
    if (start >= wlen):
        return ""
    while (start > 1) and not words[start-1].endswith("."):
        start = start - 1


    end = page*chunk_size + overlap
    if (end >= wlen):
        end = wlen -1

    while end < wlen and not words[end].endswith("."):
        end = end + 1


    chunk_text = " ".join(words[start:end+1])
    return chunk_text




def summarise(pdf):






    text = get_text(pdf)
    full_text = text


    words = get_words(text)


    #not summarising, 16k tokens should be ok
    if USE_LARGE_TEXT:
        trimmed_text = " ".join(words)
        genes = []
        #genes = get_genes(trimmed_text)
        #genes are now found later on, after we have got the species

        genes = list(genes)
        genes.sort()
        return [trimmed_text, genes, full_text]




    chunk_text = " "
    page = 0
    summary = []
    genes = set()
    while len(chunk_text) > 0:

        chunk_text = get_chunk(words, page)
        page = page + 1
        prompt = base_prompt + chunk_text


        minisummary = call_gpt_chat_api(prompt)
        summary_text = minisummary.get_completion_text(minisummary)
        summary.append(summary_text)

        chunk_genes = []
        #not using this for now, will just get them from the summary instead
        #this generates too much noise
        chunk_genes = get_genes(chunk_text)


        for gene in chunk_genes:
                genes.add(gene)


    all_summaries = " ".join(summary)

#re-summarise the summary
    if True:
        prompt = base_prompt_final + all_summaries
        minisummary = call_gpt_chat_api(prompt)
        all_summaries = minisummary.get_completion_text(minisummary)


    words = all_summaries.split(" ")



#if the minisummary is too long, then keep cutting it into chunks and repeating
    loops = 0
    while len(words) > 3600:
        loops = loops + 1
        print("looping words", len(words))

        #just in case the summary isn't getting shorter, this could wipe out the budget...
        if loops > 10:
            break
        chunk_text = " "
        page = 0
        summary = []
        while len(chunk_text) > 0:
            chunk_text = get_chunk(words, page)
            page = page + 1
            prompt = base_prompt_final + chunk_text
            minisummary = call_gpt_chat_api(prompt)
            summary_text = minisummary.get_completion_text(minisummary)
            summary.append(summary_text)
        all_summaries = " ".join(summary)
        words = all_summaries.split(" ")


    prompt = base_prompt_final + " " + all_summaries


    final_summary = call_gpt_chat_api(prompt)
    final_text = final_summary.get_completion_text(final_summary)



    out_file = pdf + ".summary.txt"
    with open(out_file, 'w',  encoding='utf-8') as outfile:
        outfile.write(final_text)





    #  print("CHUNK", chunk_text)

    final_genes = get_genes(final_text)



    for gene in final_genes:
        genes.add(gene)

    genes=list(genes)
    genes.sort()

    genes_text = ",".join(genes)
    out_file = pdf + ".genes.txt"
    with open(out_file, 'w', encoding='utf-8' ) as outfile:
        outfile.write(genes_text)



    return [final_text,genes, full_text]


def get_summary(pdf):
    fallback = 15
    fails = 0
    result=[]
    while True:
        try:
            print("calling summarise",pdf)
            result = summarise(pdf)
            print("called summarise")
            fails = 0
            fallback = 15
            break
        except openai.error.RateLimitError as e:

         #   if e is not RateLimitError:
         #       fails = fails + 1
            print("api wait", fallback,file=sys.stderr)
            time.sleep(fallback)
            fallback = fallback *1.5
        except openai.error.ServiceUnavailableError as e:

            #   if e is not RateLimitError:
            #       fails = fails + 1
            print("api wait", fallback)
            time.sleep(fallback)
            fallback = fallback * 1.5


        except Exception as e:
            print("error", e)
            fails = fails + 1
            traceback.print_exc()
            time.sleep(fallback)
            fallback = fallback *1.15

        if fails > 10:
            return ["error", ["error"]]
    return result
