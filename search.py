# https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
from sentence_transformers import SentenceTransformer, util
import params
from pymongo import MongoClient
import argparse

# Process arguments
parser = argparse.ArgumentParser(description='Atlas Vector Search Demo')
parser.add_argument('-q', '--question', help="The question to ask")
args = parser.parse_args()

if args.question is None:
    # Some questions to try...
    query = "When was Automatic Payrolls founded?"
    query = "Who did Henry Taub found Automatic Payrolls with"
    query = "When did ADP for public?"
    query = "What happened in 1985?"
    query = "How many clients did ADP have in 1961?"
    query = "Where is ADP ranked on Fortune 500?"
else:
    query = args.question

# Load the model
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Show the default question if one wasn't provided:
if args.question is None:
    print("\nYour question:")
    print("--------------")
    print(query)

# Establish connections to MongoDB
mongo_client = MongoClient(params.mongodb_conn_string)
result_collection = mongo_client[params.database][params.collectionVector]

# Encode our question
query_vector = model.encode(query).tolist()

pipeline = []

results = result_collection.aggregate(pipeline)

for result in results:
    print("\nAtlas Search's Answer:")
    print("----------------------")
    print(result['sentence'], "\n")

