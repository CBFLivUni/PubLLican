import os,hashlib,pickle,requests


def check_gene(gene):

    if gene == "None":
        return False
    if gene.isnumeric():
        return False

    link = "https://www.ebi.ac.uk/proteins/api/proteins?offset=0&size=1&exact_gene="+ gene.upper().strip()

    data = get_from_json_api(link)
    if (len(data)) < 1:
        return False

    return True


def get_from_json_api(link):
    key = link+"v2"
    encoded = key.encode('utf-8')
    m = hashlib.md5()
    m.update(encoded)

    filename = m.hexdigest()

    filename = "./cache/" + filename
    if os.path.exists(filename):
        with open(filename, 'rb') as file:
            data = pickle.load(file)


    else:
        headers = {"Accept": "application/json"}
        data = requests.get(link, headers=headers).json()
        with open(filename, 'wb') as file:
            pickle.dump(data, file)

    return data


def get_go_description(go, returnType="definition"):
    link ="https://api.geneontology.cloud/go/"+go.upper()
    hlink = "https://api.geneontology.cloud/go/" + go.upper()+"/hierarchy"


    data = get_from_json_api(link)
    hdata = get_from_json_api(hlink)
    data["hierarchy"] = hdata

    desc = ""


    if (returnType in data):
        desc = data[returnType]



    return desc


