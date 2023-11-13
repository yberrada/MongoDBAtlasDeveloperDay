# WORKSHOP: MongoDB for Text and Semantic Search

The goal of this lab is to get you familiar with some of the MongoDB Atlas Search features and the MongoDB Python Driver.

Answers for the exercises can be found in the `answers/` folder.  

## Exercise 0: Prerequisites
### Step 1: Access MongoDB Atlas cluster  

   - Login to the attendee portal https://www.atlas-labs.cloud/ using your **email** as a username.
   - Gain access to your dedicated cluster by clicking on <b>Atlas Cluster</b> in the top left corner.
   - The e-mail will be pre-populated. To login use the following password: "***AtlasW0rkshop!*** "

>Great! By default, Atlas cluters are not reachable from the internet. Therefore, all the clusters have been pre-configured for both Network Security and User Authentication and Authorization. All clusters share the same credentials: <br />
*username:* **adpadmin** <br />
*password:* **adpadminpass**<br />

## Exercise 1 : Load Data in Atlas
#### Explanation and How-to
Within this repo folder, you will find a [`corpus.txt`](https://github.com/yberrada/MongoDBAtlasDeveloperDay/blob/main/corpus.txt) file containing the **History** section of ADP's page on wikipedia https://en.wikipedia.org/wiki/ADP_(company).This is the dataset that will be used throughout the Workshop

#### Exercise
### Step 1 - Clone Github Repo
We're going to start by setting up our project. Start by creating a folder for the workshop content. 
- Execute the commands below in your terminal: 
  ```
  mkdir mongodb-devday
  cd mongodb-devday
  ```
- Now, clone the git repo:
  ```
  git clone https://github.com/yberrada/MongoDBAtlasDeveloperDay.git
  ```

### Step 2 - Load Data into Atlas

- Open the project in your favorite IDE and update your connection string in the`./MongoDBAtlasDeveloperDay/params.py`. To do so:
  - Go to the **Data Services** Tab. 
  - Under the cluster view, Click on **Connect**
  ![alt text](https://github.com/yberrada/MongoDBAtlasDeveloperDay/blob/main/public/readme/connect.png) 

  - Select **Connect your application**
  - Make sure the python driver is selected and Copy the connection string. 
  - Update the connection string in the `params.py` file.

- Now, install the pre-requisites:
  ```
  pip3 install -r requirements.txt
  ```
- Run the `load.py` to start loading chunks of the the `corpus.txt`:
  ```
  python3 load.py
  ```


The paragraph in the file was split to multiple sentences, each loaded in your MongoDB Atlas Cluster as a document. Go to Atlas, click on Collections and explore the data under the `devday` database and collection name `wikipedia`.
Below is a snippet of what the records look like:
![wikipedia file snippet as seen from Atlas](https://github.com/yberrada/MongoDBAtlasDeveloperDay/blob/main/public/readme/previewcollection.png)

## Exercise 2 : Create an Atlas Search Index and Search

#### Explanation and How-to
[Atlas Search](https://www.mongodb.com/docs/atlas/atlas-search/) is an embedded full-text search capability in MongoDB Atlas that gives you a seamless, scalable experience for building relevance-based app features. Built on Apache Lucene, Atlas Search eliminates the need to run a separate search system alongside your database.

In short, fulltext search queries typically deliver a wider range of records than regular database queries, and those records are returned sorted by `relevancy`. 

Moreover, fulltext search also delivers capabilities such as typo tolerance through fuzzy matching, highlighting of result snippets matching the query, and more. Feel free to explore some of the capabilities on [this documentation page](https://www.mongodb.com/atlas/search).

#### Exercise
We will be creating search indexes on top of the new `wikipedia` collection. 

#### Exercise
Please follow the instructions below to create a new search, optimized search index:
1. In the **Atlas UI**, go to the **Search** page. There is a link called `Search` on the left-hand panel.
2. Select your cluster and hit the `Go to Atlas Search` button. You should see the search index you previously made here. 
3. Hit the `CREATE INDEX` button in the upper-right-hand side. 
4. Keep `Visual Editor` selected and hit the `Next` button.
5. Set the index name to `default` and select the `wikipedia` collection in the `devday` database. Hit `Next`.
6.  Hit `Create Search Index` to create your new `default` index.

It will take a couple of minutes for the index to be built. The Atlas UI shows the state of the index as it changes. 

---
>Note that, for the free-tier M0 cluster, only 3 search indexes can be built. This is not a limitation for any other cluster tier.
---

This default index configuration will capture all indexable fields and make them all available for search. This is called `dynamic indexing`, which is useful for collections within which documents' schemas change. However, this approach typically results in a larger index size. Atlas allows you to select specific fields to be indexed but that's out of scope for today.

Once the index is ready, go back to Atlas. Select the `wikipedia` collection and go to the `Aggregations` tab like before. Hit `Add Stage` and enter `$search` for the first stage. Atlas should provide you with the syntax. Try running the following query in the search stage:  
```
{
  index: 'default',
  text: {
    query: 'Storteler',
    path: 'title',
    fuzzy:{
      maxEdits: 2,
  	  prefixLength: 0
    }
  }
}
```
Note that `fuzzy` is enabled which means that our search query is typo tolerant.

To see the `relevancy score`, add a subsequent `$project` stage to the pipeline:
```
score: {
    $meta: "searchScore",
  },
```
Here is a full aggregation pipeline:
```bash
[
  {
    $search: {
      index: "default",
      text: {
        query: "werewolves",
        path: "title",
      },
    },
  },
  {
    $project:
      /**
       * specifications: The fields to
       *   include or exclude.
       */
      {
        title: 1,
        text: 1,
        score: {
          $meta: "searchScore",
        }
      },
  },
]
```


Next, play around compound queries (Search queries on multiple fields). Below is an example that you could try.

[Compound search](https://www.mongodb.com/docs/atlas/atlas-search/compound/#definition):
```
{
  index: "default",
  compound: {
    should: {
      text: {
        path: "fullplot",
        query: "werewolves",
        fuzzy: {
          maxEdits: 2,
        },
      },
    },
    mustNot: {
      text: {
        path: "fullplot",
        query: "vampires",
      },
    },
  },
}
```

## Exercise 3 : Semantic Search

#### Explanation and How-to
You can perform semantic search on data in your Atlas cluster running MongoDB v6.0.11 or later using Atlas Vector Search. You can store vector embeddings for any kind of data along with other data in your collection on the Atlas cluster. Atlas Vector Search supports embeddings that are less than and equal to 2048 dimensions in width.

When you define an Atlas Vector Search index on your collection, you can seamlessly index vector data along with your other data and then perform semantic search against the indexed fields.

Atlas Vector Search uses the [Hierarchical Navigable Small Worlds](https://arxiv.org/abs/1603.09320) algorithm to perform the semantic search. You can use Atlas Vector Search support for approximate nearest neighbord (aNN) queries to search for results similar to a selected product, search for images, etc.

#### Exercise
Let's start by loading the vectorized documents in Atlas under the `wiki_embeddings` collection. To do so, go back to your terminal and run the `load.py` with the `vector` argument to start loading chunks of the the `corpus.txt`:
  ```
  python3 load.py -a vector
  ```

Let's create a search index using the embeddings already available for the `wikipedia` collection's docs. 

1. Back in the **Atlas web UI**, go to the **Search** page. There is a link called `Search` on the left-hand panel.
2. Select your cluster and hit the `Go to Atlas Search` button. You should see the search index you previously made here. 
3. Hit the `CREATE INDEX` button in the upper-right-hand side.
4. This time, select `JSON Editor` and hit `Next`.
5. Name this index `vector` and replace the default definition with this one:
```JSON
{
  "mappings": {
    "dynamic": false,
    "fields": {
      "docVector": {
        "dimensions": 384,
        "similarity": "cosine",
        "type": "knnVector"
      }
    }
  }
}
```
1. Select the `devday` database's `wikipedia` collection to build this index on and hit `Next`.
2. Hit `Create Search Index`.
It should take only a couple of minutes for this index to be created and reach `ACTIVE` status, meaning that it is searchable.

## Exercise 4 : Test Query in Atlas

Once the index is ready, go back to Compass. Select the `wikipedia` collection and go to the `Aggregations` tab like before. Hit `Add Stage` and enter `$search` for the first stage. Compass should provide you with sample syntax. To run a vector search query,  
We now can test our Search Index through the aggregation pipeline builder. 
- Go back to ‘**Browse Collections**’ and select the '**sample-mflix.movies**' collection.
![alt text](./public/readme/aggregate.png) 

- Click on the '**Aggregation**' tab 
- Select the '**$search**' aggregation pipeline stage in the dropdown menu.
![alt text](./public/readme/search-stage.png) 

- Try running the following query in the search stage:  
```
{
  index: 'default',
  text: {
    query: 'Storteler',
    path: 'title',
    fuzzy:{}
  }
}
```
> The search stage should match a movie titled: *The Storyteller*. Notice that our query string is *Storteler*.


## Exercise 5 : Test Query in Code

- From the Atlas Aggregation builder, export the pipeline to Python syntax by clicking on **EXPORT TO LANGUAGE**.
- Make sure to copy the pipeline code.
- Go back to the python project and locate `search.py` file. 
- The python code is only missing the aggregation pipeline. Paste it and test your code: 
```python3 search.py -q "When was automated processing founded"```
- Other Questions to test your code with can be: 
  

---
>Congratulations on completing the lab!
---