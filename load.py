# https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
from sentence_transformers import SentenceTransformer, util
import params
from pymongo import MongoClient
import argparse

# https://stackoverflow.com/questions/4576077/how-can-i-split-a-text-into-sentences
import re
alphabets= "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov)"
digits = "([0-9])"

def split_into_sentences(text):
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    text = re.sub(digits + "[.]" + digits,"\\1<prd>\\2",text)
    if "..." in text: text = text.replace("...","<prd><prd><prd>")
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    if "Bros." in text: text = text.replace("Bros.","Bros<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences

# Establish connections to MongoDB
mongo_client = MongoClient(params.mongodb_conn_string)

# set corpos from Background on WBD Wikipedia page (https://en.wikipedia.org/wiki/ADP_(company))
fp = open("corpus.txt")
corpus = fp.read()

# turn it into an array of sentences
docs = split_into_sentences(corpus)

# A placeholder for the result doc
result_doc = {}

# Process arguments
parser = argparse.ArgumentParser()
parser.add_argument('-a', '--action', help="load strings or vectors")
args = parser.parse_args()

if args.action is None:
    result_collection = mongo_client[params.database][params.collection]
    for doc in docs:
        result_doc['sentence'] = doc
        result_doc['company'] = 'ADP'
        result_doc['url'] = 'https://en.wikipedia.org/wiki/ADP_(company)'
        result = result_collection.insert_one(result_doc.copy())
        print(result)
elif args.action == 'vector':
    # Load the model
    result_collection = mongo_client[params.database][params.collectionVector]
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    for doc in docs:
        doc_vector = model.encode(doc).tolist()
        result_doc['sentence'] = doc
        result_doc['company'] = 'ADP'
        result_doc['url'] = 'https://en.wikipedia.org/wiki/ADP_(company)'
        result_doc['docVector'] = doc_vector
        result = result_collection.insert_one(result_doc.copy())
        print(result)
else:
    print("Wrong action specified. Please use the following format: python3 load.py or python3 load.py -a vector")
