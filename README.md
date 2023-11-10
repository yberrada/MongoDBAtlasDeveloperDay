# WORKSHOP: MongoDB as a Vector Database

The following is a plaintext version of the exercises in the PDF presentation. It is meant to guide workshop participants through the process by providing code snippets that can be easily copy/pasted into [MongoDB Atlas](https://cloud.mongodb.com/).

Please also refer to [the PDF of the presentation](https://github.com/nickgogan/MongoDBAtlasDeveloperDay/blob/main/DevDayPresentation_Full.pdf) to see helpful screenshots to aid in completing the exercises. Answers for both the Compass GUI approach and shell approach are in the PDF, but plaintext versions can be found in the `answers/` folder.  

## Checkpoint 0: Prerequisites
1. As a workshop attendee/participants, please ensure that you have followed all of the [list of prerequisites](https://github.com/nickgogan/MongoDBAtlasDeveloperDay/tree/main#prerequisites). Then, please [install MongoDB Compass](https://www.mongodb.com/try/download/compass) and copy this repository to have access to the `wikipedia_tiny.json` file in `data/`.


## Atlas Search
### **Exercise 9**: Import Data Using Compass GUI
#### Explanation and How-to
Within this repo's `data/` folder, you will find a [`wikipedia_tiny.json`](https://github.com/nickgogan/MongoDBAtlasDeveloperDay/blob/main/data/wikipedia_tiny.json) file containing 5,000 documents. These documents are cleaned wikipedia articles that, among some other metadata, contain the article title, body in plaintext, and a 384-dimension vector representation of plaintext body. Below is a snippet of what the records look like:
![wikipedia file snippet as seen from Compass](https://github.com/nickgogan/MongoDBAtlasDeveloperDay/blob/main/compass%20and%20shell/images/Compass_WikpediaSchema.png)
#### Exercise
Create a new collection with database name `devday` and collection name `wikipedia`. Then, import the `wikipedia_tiny.json` tile into it. [Please refer to this guide on how to import data files using the Compass GUI](https://www.mongodb.com/docs/compass/current/import-export/#import-data-into-a-collection)

### **Exercise 1**: Create an Atlas Search Index and Search
#### Explanation and How-to
[Atlas Search](https://www.mongodb.com/docs/atlas/atlas-search/) is an embedded full-text search capability in MongoDB Atlas that gives you a seamless, scalable experience for building relevance-based app features. Built on Apache Lucene, Atlas Search eliminates the need to run a separate search system alongside your database.

In short, fulltext search queries typically deliver a wider range of records than regular database queries, and those records are returned sorted by `relevancy`. This means that top answers to those queries are computed to be more meaningful to the user. This is in opposition to database queries, where each record in the result set has equal weight to any other in the result set. 

Moreover, fulltext search also delivers capabilities such as typo tolerance through fuzzy matching, highlighting of result snippets matching the query, and more. Feel free to explore some of the capabilities on [this documentation page](https://www.mongodb.com/atlas/search).

#### Exercise
We will be creating search indexes on top of the new `wikipedia` collection. 

[Follow the guidelines here](https://www.mongodb.com/docs/atlas/atlas-search/tutorial/create-index/) to create a new search index **via the Atlas UI**, keeping all configuration at default. Use the **Visual Editor** to create this index. It will take a couple of minutes for the index to be built. The Atlas UI shows the state of the index as it changes. 

---
>Note that, for the free-tier M0 cluster, only 3 search indexes can be built. This is not a limitation for any other cluster tier.
---

This default index configuration will capture all indexable fields and make them all available for search. This is called `dynamic indexing`, which is useful for collections within which documents' schemas change. However, this approach typically results in a larger index size. We will see how we can optimize this in the next exercise. 

Once the index is ready, go back to Compass. Select the `wikipedia` collection and go to the `Aggregations` tab like before. Hit `Add Stage` and enter `$search` for the first stage. Compass should provide you with the syntax, which should look something like this:
```
/**
 * index: The name of the Search index.
 * text: Analyzed search, with required fields of query and path, the analyzed field(s) to search.
 * compound: Combines ops.
 * span: Find in text field regions.
 * exists: Test for presence of a field.
 * near: Find near number or date.
 * range: Find in numeric or date range.
 */
{
  index: 'string',
  text: {
    query: 'string',
    path: 'string'
  }
}
```

Play around with search queries, using [this documentation root](https://www.mongodb.com/docs/atlas/atlas-search/searching/) as a guide and the examples below.

[Fuzzy search/typo tolerance](https://www.mongodb.com/docs/atlas/atlas-search/text/):
```
{
  index: '<indexName>',
  text: {
	  query: ‘<queryText>’,
	  path: '<indexedFieldName(s)>',
	  fuzzy: {
  	  maxEdits: 2,
  	  prefixLength: 0
	  }
  }
}
```
[Highlighting](https://www.mongodb.com/docs/atlas/atlas-search/highlighting/):
```
{
  index: '<indexName>',
  text: {
	  query: ‘<queryText>’,
	  path: '<indexedFieldName(s)>',
	  fuzzy: {
  	  maxEdits: 2,
  	  prefixLength: 0
	  }
  },
  highlight: {
	  path: "<indexedFieldName>"
  }
}
```
[Compound search](https://www.mongodb.com/docs/atlas/atlas-search/compound/#definition):
```
{
  index: "<indexName",
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
To see the `relevancy score` and `highlights`, add a subsequent `$project` stage to the pipeline:
```
score: {
    $meta: "searchScore",
  },
  highlights: {
    $meta: "searchHighlights",
  },
```
Here is a full aggregation pipeline that can be run via the embedded shell:
```bash
let pipeline = [
  {
    $search: {
      index: "optimized",
      text: {
        query: "test",
        path: "text",
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
        },
        highlights: {
          $meta: "searchHighlights",
        },
      },
  },
]
```
then:
```bash
db.wikipedia.aggregate(pipeline)
```

---
>Fun fact: The pipeline above was [exported directly out of Compass](https://www.mongodb.com/docs/compass/current/agg-pipeline-builder/export-pipeline-results/) after I built & validated it via the GUI!
---

### **Exercise 2**: Create an *Optimized* Atlas Search Index
#### Explanation & How-to
In our case, we only care to search on the `title` and `text` fields of each document in the `wikipedia` collection. Moreover, our users exclusively search in English, so we will want title and text to be indexed by an analyzer intelligent enough to apply English grammar to the information. For example, if I search for the word `dog`, I should get back documents mentioning `dog` or `dogs`. If we were to index the information in French or German, the analyzer should be intelligent to understand gendered words and deal with various accent marks. There is [a wide and interesting world of analyzers](https://www.mongodb.com/docs/atlas/atlas-search/analyzers/) out there that are worth exploring!

#### Exercise
Please follow the instructions below to create a new search, optimized search index:
1. In the **Atlas UI**, go to the **Search** page. There is a link called `Search` on the left-hand panel.
2. Select your cluster and hit the `Go to Atlas Search` button. You should see the search index you previously made here. 
3. Hit the `CREATE INDEX` button in the upper-right-hand side. 
4. Keep `Visual Editor` selected and hit the `Next` button.
5. Set the index name to `optimized` and select the `wikipedia` collection in the `devday` database. Hit `Next`.
6. Click `Refine Your Index`.
7. At the top of the page, for the `Index Analyzer` dropdown, select `lucene.english`.
8. Disable `Dynamic Mapping`. We will specific the fields we want to index this time.
9. Click `Add Field Mapping`. Enter `title` for the first field name and keep everything else the same. Hit `Add`.
10. Repeat step 9 for the `text` field.
11. Scroll down and hit `Save Changes`.
12. Hit `Create Search Index` to create your new `optimized` index.

Since this index is scoped to a subset of the fields, it should build a little faster than the first one. Once it's built and has a status of `ACTIVE` like the first one, notice the size difference between the two indexes. For reference, here is a screenshot of mine:
![optimized vs default index size difference](https://github.com/nickgogan/MongoDBAtlasDeveloperDay/blob/main/compass%20and%20shell/images/Atlas_SearchIndexSizeComparison.png)

### **Exercise 3**: Semantic Search
#### Explanation and How-to
You can perform semantic search on data in your Atlas cluster running MongoDB v6.0.11 or later using Atlas Vector Search. You can store vector embeddings for any kind of data along with other data in your collection on the Atlas cluster. Atlas Vector Search supports embeddings that are less than and equal to 2048 dimensions in width.

When you define an Atlas Vector Search index on your collection, you can seamlessly index vector data along with your other data and then perform semantic search against the indexed fields.

Atlas Vector Search uses the [Hierarchical Navigable Small Worlds](https://arxiv.org/abs/1603.09320) algorithm to perform the semantic search. You can use Atlas Vector Search support for approximate nearest neighbord (aNN) queries to search for results similar to a selected product, search for images, etc.

#### Exercise
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
      "language": [{
        "type": "token",          
        "normalizer": "lowercase"
        },
        {
          "type": "string"
        }
      ],
      "vector": {
        "dimensions": 384,
        "similarity": "cosine",
        "type": "knnVector"
      }
    }
  }
}
```
6. Select the `devday` database's `wikipedia` collection to build this index on and hit `Next`.
7. Hit `Create Search Index`.
It should take only a couple of minutes for this index to be created and reach `ACTIVE` status, meaning that it is searchable.


# Vectorize Query

1. Set up your python environment (if not done already):

```
python3 -m venv .ENV
```

```
source .ENV/bin/activate
```

```
pip install -r requirements.txt
```

2. Open a terminal session where you activated your ENV. 

3. Start python interpreter: ```python3```

4. Import HuggingFace transformers library: ```from sentence_transformers import SentenceTransformer```

5. Get handle on the ```all-MiniLM-L6-v2``` model: ```encoder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')```

6. Encode query text into vector representation: ```encoder.encode(<yourquery>).tolist()```
   
Once ready, try [running a vector search query](https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-stage/) (see the Basic Example on that page) using the following query vector:
```
[0.011573508381843567, 0.025136180222034454, -0.03670182079076767, 0.05932481214404106, -0.007148992270231247, -0.04119409620761871, 0.07708732038736343, 0.037442516535520554, 0.012449102476239204, -0.006117624696344137, 0.017034228891134262, -0.07701531797647476, -0.0003942555340472609, 0.027909113094210625, -0.01598912477493286, -0.06827528774738312, 0.008884701877832413, -0.02028072066605091, -0.08035992830991745, -0.013074136339128017, -0.041099902242422104, -0.025898128747940063, -0.02653864212334156, 0.033052392303943634, -0.022079147398471832, 0.02104610949754715, -0.05792201682925224, 0.03294873610138893, 0.02970735915005207, -0.062248315662145615, 0.03878805413842201, 0.03199061006307602, 0.015330723486840725, 0.0453069768846035, 0.053149424493312836, 0.013360598124563694, 0.041224874556064606, 0.028142929077148438, 0.019398396834731102, -0.00325228413566947, -0.0036123981699347496, -0.1428602933883667, 0.03807120770215988, -0.010916270315647125, 0.026093879714608192, 0.0413699708878994, -0.01601581461727619, 0.053560156375169754, -0.05685950815677643, 0.012246794067323208, -0.03499656170606613, -0.039754077792167664, -0.0461430549621582, -0.03911232948303223, -0.018003594130277634, 0.021634189411997795, -0.006461430341005325, -0.026569517329335213, 0.048728764057159424, 0.0434005968272686, 0.0461999736726284, -0.03447902575135231, -0.024219239130616188, 0.05564909800887108, 0.0246245376765728, 0.019485577940940857, 0.011352903209626675, -0.02576233446598053, -0.032244496047496796, -0.03265222907066345, -0.014595886692404747, 0.014690297655761242, 0.010304473340511322, 0.07407968491315842, 0.08006174117326736, -0.004143617581576109, 0.00271422928199172, -0.07674671709537506, 0.05881533399224281, -0.0048391674645245075, -0.08736331015825272, -0.046462029218673706, -0.039625417441129684, 0.05249401181936264, 0.024801554158329964, 0.08080150187015533, 0.11981362849473953, 0.03177151083946228, -0.11397252231836319, 0.010673915036022663, 0.019723784178495407, 0.03871838375926018, -0.034542348235845566, -0.006243137642741203, -0.04255080223083496, 0.022628607228398323, 0.008293558843433857, -0.019443700090050697, -0.02325102873146534, 0.24533754587173462, 0.0494421161711216, 0.029147367924451828, -0.005753751378506422, -0.020419558510184288, -0.07761149108409882, -0.042979128658771515, 0.000430352461989969, -0.06692603975534439, 0.07076043635606766, 0.0065070209093391895, -0.05844531208276749, -0.005057237576693296, 0.030943823978304863, 0.02757960371673107, 0.027111126109957695, -0.06818623095750809, -0.0657687559723854, 0.059077661484479904, -0.031894147396087646, 0.040606047958135605, 0.05710184574127197, 0.006903495639562607, 0.006207591388374567, -0.013271572068333626, 0.031240442767739296, -0.04029695689678192, 0.07085219770669937, -4.846278151060217e-33, 0.021934309974312782, -0.10270478576421738, 0.056213222444057465, 0.09758369624614716, -0.05268492549657822, 0.01909760572016239, -0.010507515631616116, 0.07035727053880692, -0.009123305790126324, 0.05957060679793358, 0.00933860708028078, -0.015523107722401619, -0.023274024948477745, 0.02397681400179863, 0.10208837687969208, 0.09320352226495743, -0.033136047422885895, 0.011721508577466011, -0.06560060381889343, 0.031464774161577225, -0.023807885125279427, -0.04873918741941452, 0.012257843278348446, -0.04001425951719284, -0.07650823146104813, -0.0355532206594944, -0.0013623012928292155, -0.016429129987955093, 0.016882436349987984, -0.0003748629824258387, -0.0527249313890934, 0.02988101728260517, -0.07291106879711151, 0.06912258267402649, -0.017607856541872025, -0.005510199815034866, 0.012954692356288433, -0.022701852023601532, 0.026741325855255127, -0.02584582194685936, -0.0402020700275898, -0.013495105318725109, 0.0007998105720616877, 0.028601255267858505, 0.03194248303771019, -0.031607117503881454, -0.029549837112426758, -0.020251324400305748, 0.04817793890833855, -0.001307600294239819, -0.013747215270996094, 0.02003014087677002, -0.06870562583208084, -0.021960847079753876, -0.0313321091234684, 0.04928041622042656, 0.012094753794372082, -0.05886812508106232, -0.026465734466910362, 0.0598900131881237, 0.06764866411685944, 0.03401561081409454, -0.05288434773683548, 0.059719402343034744, -0.02548256516456604, -0.02072996273636818, -0.05382559821009636, -0.09741072356700897, 0.047928232699632645, 0.05239959806203842, -0.023259567096829414, -0.06907135248184204, 0.01665687747299671, 0.028476417064666748, -0.029204869642853737, -0.035486698150634766, -0.012644220143556595, 0.07333991676568985, -0.01943499781191349, -0.0632789134979248, 0.09606631845235825, -0.07743873447179794, 0.01593952625989914, -0.04480088874697685, 0.016302691772580147, -0.0007481018546968699, -0.008702695369720459, -0.09881407767534256, 0.0057428390718996525, -0.07192353904247284, -0.032677676528692245, 0.0198945552110672, 0.003859780030325055, -0.02555113658308983, 0.0823836699128151, 4.08626411524599e-33, -0.02948819287121296, 0.02555151656270027, -0.05106087401509285, 0.15531231462955475, 0.05231142044067383, -0.03454818204045296, 0.13314682245254517, -0.019209740683436394, -0.059767063707113266, 0.12289652973413467, 0.01020291168242693, -0.04967312142252922, 0.058467213064432144, 0.012732676230370998, -0.01658635586500168, 0.012795528396964073, 0.045758169144392014, -0.06982148438692093, -0.04852410778403282, -0.004963504150509834, -0.09043655544519424, 0.06992126256227493, 0.009389102458953857, -0.006744624115526676, -0.10609240084886551, 0.03109489008784294, 0.049425847828388214, -0.04487113282084465, -0.007371764630079269, -0.033561088144779205, 0.07605833560228348, 0.007239122409373522, -0.042201463133096695, 0.07079152762889862, 0.047472018748521805, 0.02078300341963768, 0.15331053733825684, -0.0083940289914608, -0.025880761444568634, 0.060799166560173035, 0.06681564450263977, 0.064722940325737, 0.049820322543382645, 0.08878500759601593, -0.03294115141034126, 0.07035744190216064, 0.017195409163832664, -0.030185343697667122, 0.03854382038116455, 0.04846976324915886, -0.06051008775830269, 0.03053232468664646, 0.015603967942297459, -0.030421309173107147, -0.009440446272492409, -0.04105139151215553, -0.06789780408143997, 0.01019960455596447, -0.025656629353761673, 0.021715648472309113, -0.06997868418693542, 0.09247464686632156, -0.035719819366931915, 0.0701378807425499, -0.06342041492462158, -0.03294041380286217, -0.04619632288813591, 0.05414000153541565, 0.05172339454293251, 0.042922209948301315, 0.01347502414137125, 0.016596682369709015, -0.04410717636346817, -0.01972007192671299, 0.03620152175426483, -0.01966143399477005, -0.11567908525466919, 0.00595499761402607, 0.0045669060200452805, -0.04494287446141243, -0.06840218603610992, -0.08530446887016296, -0.0709521472454071, 0.08038382977247238, -0.05798294395208359, 0.057827211916446686, 0.05022648721933365, 0.059423044323921204, -0.03655630350112915, 0.00926964357495308, 0.05252375826239586, 0.027989575639367104, -0.03336919844150543, -0.05078495666384697, -0.012864768505096436, -1.4297850903233211e-08, -0.04052522033452988, -0.08579083532094955, 0.04516823962330818, 0.021677006036043167, -0.022338498383760452, 0.012207704596221447, -0.032489120960235596, -0.01695290580391884, -0.027171028777956963, 0.006002899259328842, 0.0402761772274971, 0.026962704956531525, -0.035624682903289795, 0.07408847659826279, 0.03237416222691536, -0.09056803584098816, -0.031741589307785034, 0.040925294160842896, -0.009956026449799538, 0.030688408762216568, -0.0769139751791954, 0.04158458486199379, 0.00019602153042797, 0.06277656555175781, -0.03609062731266022, 0.04884403944015503, 0.05422690138220787, 0.1266198605298996, -0.003848724765703082, 0.0008294433355331421, 0.06961402297019958, 0.04400506243109703, -0.03208089992403984, -0.08523827791213989, 0.013769851997494698, 0.022801866754889488, -0.0028472745325416327, -0.00678517809137702, 0.03758794814348221, 0.035276927053928375, -0.06678414344787598, 0.021526463329792023, 0.037526607513427734, -0.04542553797364235, -0.051031675189733505, -0.06799469143152237, -0.030867084860801697, -0.03639031946659088, -0.014874979853630066, -0.0936829149723053, -0.03157731890678406, 0.010241780430078506, 0.015077218413352966, -0.0023830991704016924, 0.024135461077094078, -0.01328529603779316, 0.00658379215747118, 0.024441566318273544, -0.13713598251342773, 0.06391417235136032, 0.19671830534934998, -0.006029617041349411, 0.0531940758228302, -0.055225953459739685]
```
### **Exercise 4**: Semantic Search with Pre-Filter
#### Explanation
Atlas's `$vectorSearch` stage has an optional `filter` parameter that can be used to pre-filter documents before performing the semantic search on the remainder. This typically leads to faster AND more accurate searches - win win!

#### Exercise
Run the same `$vectorSearch` query, but add a `filter` to the query to only target a specific `language` (english, french, german, italian, or frisian). Refer to the Filter Example on [this documentation page](https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-stage/#examples).


---
> Fun fact: The shell is actually a javascript interpreter! This means you can do fun stuff like declare variables and loop through records directly in the shell, using modern javascript syntax. 
---