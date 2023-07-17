import openai
import json
import pickle
import hashlib
import os

chat_model_engine = "gpt-3.5-turbo-16k"

# you must  get your own key from openai.com

with open('apikey.txt') as f:
    key = f.readlines()
key = key[0].strip()

openai.api_key = key
api_calls = 0

def load_gpt_text(filename):

    with open(filename, 'rb') as file:
        completions = pickle.load(file)
    return completions


def get_completion_text(completions):
    if completions.choices[0].message:
        summary = completions.choices[0].message.content
    else:
        summary = completions.choices[0].text
    return summary


def get_completion_list(completions):
    if completions.choices[0].message:
        summary = completions.choices[0].message.content
    else:
        summary = completions.choices[0].text

    try:

        summary = json.loads(summary)
        if type(summary) is dict:
            key0 = list(summary.keys())[0]
            summary = summary[key0]
        if type(summary) is dict:
            key0 = list(summary.keys())[0]
            summary = summary[key0]

        summary = "\n".join(summary)

    except ValueError:
        summary = summary
    return summary

def save_gpt_text(completions, filename):
#    print("save gpt",filename)
    with open(filename, 'wb') as file:
        pickle.dump(completions, file)

    return filename

def call_gpt_chat_api(prompt):
    global api_calls
    max_tokens = 3000
    # Set the temperature for sampling
    temperature = 0

    key = prompt+"_"+chat_model_engine+"_"+str(temperature)+"_"+str(max_tokens)

    encoded = key.encode('utf-8')
    m = hashlib.md5()
    m.update(encoded)

    filename = m.hexdigest()


   # return

    filename = "./cache/" + filename
    if os.path.exists(filename):
        completions = load_gpt_text(filename)

    else:
        if api_calls ==0:
            print("API CALLED")
        else:
            print(".",end="")
        api_calls = api_calls+1

#        exit(1)
        completions = openai.ChatCompletion.create(
            model=chat_model_engine,
            messages= [{"role":"user","content":prompt},],
            max_tokens=max_tokens,
            temperature=temperature,

        )
        save_gpt_text(completions,filename)

    completions.get_completion_text = get_completion_text
    completions.get_completion_list = get_completion_list

    return completions

