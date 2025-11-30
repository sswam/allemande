NOTE: Apache-2.0 License: https://github.com/civitai/civitai?tab=Apache-2.0-1-ov-file#readme

# Introduction

This article describes how to use the Civitai REST API, including HTTP methods, paths, and parameters for each operation. The API returns response status codes, headers, and a body.

> This is still in active development and will be updated once more endpoints are made available for the public

## Civitai API v1

- [Authorization](#authorization)

### Creators
- [GET /api/v1/creators](#get-apiv1creators)

### Images
- [GET /api/v1/images](#get-apiv1images)

### Models
- [GET /api/v1/models](#get-apiv1models)

### Model
- [GET /api/v1/models/:modelId](#get-apiv1modelsmodelid)

### Model Version
- [GET /api/v1/model-versions/:modelVersionId](#get-apiv1models-versionsmodelversionid)
- [GET /api/v1/model-versions/by-hash/:hash](#get-apiv1models-versionsby-hashhash)

### Tags
- [GET /api/v1/tags](#get-apiv1tags)

## Authorization

To make authorized requests as a user you must use an API Key, generated from your [User Account Settings](https://civitai.com/user/account).

You can authenticate with either an Authorization Header or Query String.

Creators can require that people be logged in to download their resources. Please see [the Guide to Downloading via API](https://education.civitai.com/civitais-guide-to-downloading-via-api/) for more details.

### Authorization Header

Pass the API token as a Bearer token using the `Authorization` header:

```
GET https://civitai.com/api/v1/models
Content-Type: application/json
Authorization: Bearer {api_key}
```

### Query String

Pass the API token as a query parameter using the `?token=` parameter:

```
GET https://civitai.com/api/v1/models?token={api_key}
Content-Type: application/json
```

### GET /api/v1/creators

#### Endpoint URL

`https://civitai.com/api/v1/creators`

#### Query Parameters

| Name | Type | Description |
|---|---|---|
| limit `(OPTIONAL)` | number | The number of results to be returned per page. This can be a number between 0 and 200. By default, each page will return 20 results. If set to 0, it'll return all the creators |
| page `(OPTIONAL)` | number | The page from which to start fetching creators |
| query `(OPTIONAL)` | string | Search query to filter creators by username |

#### Response Fields

| Name | Type | Description |
|---|---|---|
| username | string | The username of the creator |
| modelCount | number | The amount of models linked to this user |
| link | string | Url to get all models from this user |
| metadata.totalItems | string | The total number of items available |
| metadata.currentPage | string | The the current page you are at |
| metadata.pageSize | string | The the size of the batch |
| metadata.totalPages | string | The total number of pages |
| metadata.nextPage | string | The url to get the next batch of items |
| metadata.prevPage | string | The url to get the previous batch of items |

#### Example

```sh
curl https://civitai.com/api/v1/creators?limit=1 \
-H "Content-Type: application/json" \
-X GET
```

This would yield the following response:
```json
{
  "items": [
    {
      "username": "Civitai",
      "modelCount": 848,
      "link": "https://civitai.com/api/v1/models?username=Civitai"
    }
  ],
  "metadata": {
    "totalItems": 46,
    "currentPage": 1,
    "pageSize": 1,
    "totalPages": 46,
    "nextPage": "https://civitai.com/api/v1/creators?limit=1&page=2"
  }
}
```

### GET /api/v1/images

#### Endpoint URL

`https://civitai.com/api/v1/images`

#### Query Parameters

| Name | Type | Description |
|---|---|---|
| limit `(OPTIONAL)` | number | The number of results to be returned per page. This can be a number between 0 and 200. By default, each page will return 100 results. |
| postId `(OPTIONAL)` | number | The ID of a post to get images from |
| modelId `(OPTIONAL)` | number | The ID of a model to get images from (model gallery) |
| modelVersionId `(OPTIONAL)` | number | The ID of a model version to get images from (model gallery filtered to version) |
| username `(OPTIONAL)` | string | Filter to images from a specific user |
| nsfw `(OPTIONAL)` | boolean \| enum `(None, Soft, Mature, X)` | Filter to images that contain mature content flags or not (undefined returns all) |
| sort `(OPTIONAL)` | enum `(Most Reactions, Most Comments, Newest)` | The order in which you wish to sort the results |
| period `(OPTIONAL)`| enum `(AllTime, Year, Month, Week, Day)` | The time frame in which the images will be sorted |
| page `(OPTIONAL)` | number | The page from which to start fetching creators |

#### Response Fields

| Name | Type | Description |
|---|---|---|
| id | number | The id of the image |
| url | string | The url of the image at it's source resolution |
| hash | string | The blurhash of the image |
| width | number | The width of the image |
| height | number | The height of the image |
| nsfw | boolean | If the image has any mature content labels |
| nsfwLevel | enum `(None, Soft, Mature, X)` | The NSFW level of the image |
| createdAt | date | The date the image was posted |
| postId | number | The ID of the post the image belongs to |
| postId | number | The ID of the post the image belongs to |
| modelVersionIds | number[] | The IDs of the model version resources we could identify in this image |
| stats.cryCount | number | The number of cry reactions |
| stats.laughCount | number | The number of laugh reactions |
| stats.likeCount | number | The number of like reactions |
| stats.heartCount | number | The number of heart reactions |
| stats.commentCount | number | The number of comment reactions |
| meta | object | The generation parameters parsed or input for the image |
| username | string | The username of the creator |
| metadata.nextCursor | number | The id of the first image in the next batch |
| metadata.currentPage | number | The the current page you are at (if paging) |
| metadata.pageSize | number | The the size of the batch (if paging) |
| metadata.nextPage | string | The url to get the next batch of items |

#### Example

```sh
curl https://civitai.com/api/v1/images?limit=1 \
-H "Content-Type: application/json" \
-X GET
```

This would yield the following response:
```json
{
  "items": [
    {
      "id": 469632,
      "url": "https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/cc5caabb-e05f-4976-ff3c-7058598c4e00/width=1024/cc5caabb-e05f-4976-ff3c-7058598c4e00.jpeg",
      "hash": "UKHU@6H?_ND*_3M{t84o^+%MD%xuXSxasAt7",
      "width": 1024,
      "height": 1536,
      "nsfw": false,
      "nsfwLevel": "None",
      "createdAt": "2023-04-11T15:33:12.500Z",
      "postId": 138779,
      "stats": {
        "cryCount": 0,
        "laughCount": 0,
        "likeCount": 0,
        "dislikeCount": 0,
        "heartCount": 0,
        "commentCount": 0
      },
      "meta": {
        "Size": "512x768",
        "seed": 234871805,
        "Model": "Meina",
        "steps": 35,
        "prompt": "<lora:setsunaTokage_v10:0.6>, green hair, long hair, standing, (ribbed dress), zettai ryouiki, choker, (black eyes), looking at viewer, adjusting hair, hand in own hair, street, grin, sharp teeth, high ponytail, [Style of boku no hero academia]",
        "sampler": "DPM++ SDE Karras",
        "cfgScale": 7,
        "Clip skip": "2",
        "Hires upscale": "2",
        "Hires upscaler": "4x-AnimeSharp",
        "negativePrompt": "(worst quality, low quality, extra digits:1.3), easynegative,",
        "Denoising strength": "0.4"
      },
      "username": "Cooler_Rider"
    }
  ],
  "metadata": {
    "nextCursor": 101,
    "currentPage": 1,
    "pageSize": 100,
    "nextPage": "https://civitai.com/api/v1/images?page=2"
  }
}
```

**Notes:**
- On July 2, 2023 we switch from a paging system to a cursor based system due to the volume of data and requests for this endpoint.
- Whether you use paging or cursors, you can use `metadata.nextPage` to get the next page of results

### GET /api/v1/models

#### Endpoint URL

`https://civitai.com/api/v1/models`

#### Query Parameters

| Name | Type | Description |
|---|---|---|
| limit `(OPTIONAL)` | number | The number of results to be returned per page. This can be a number between 1 and 100. By default, each page will return 100 results |
| page `(OPTIONAL)` | number | The page from which to start fetching models |
| query `(OPTIONAL)` | string | Search query to filter models by name |
| tag `(OPTIONAL)` | string | Search query to filter models by tag |
| username `(OPTIONAL)` | string | Search query to filter models by user |
| types `(OPTIONAL)` | enum[] `(Checkpoint, TextualInversion, Hypernetwork, AestheticGradient, LORA, Controlnet, Poses)` | The type of model you want to filter with. If none is specified, it will return all types |
| sort `(OPTIONAL)` | enum `(Highest Rated, Most Downloaded, Newest)` | The order in which you wish to sort the results |
| period `(OPTIONAL)`| enum `(AllTime, Year, Month, Week, Day)` | The time frame in which the models will be sorted |
| rating `(OPTIONAL)` (Deprecated) | number | The rating you wish to filter the models with. If none is specified, it will return models with any rating |
| favorites `(OPTIONAL)` `(AUTHED)` | boolean | Filter to favorites of the authenticated user (this requires an API token or session cookie) |
| hidden `(OPTIONAL)` `(AUTHED)` | boolean | Filter to hidden models of the authenticated user (this requires an API token or session cookie) |
| primaryFileOnly `(OPTIONAL)` | boolean | Only include the primary file for each model (This will use your preferred format options if you use an API token or session cookie) |
| allowNoCredit `(OPTIONAL)` | boolean | Filter to models that require or don't require crediting the creator |
| allowDerivatives `(OPTIONAL)` | boolean | Filter to models that allow or don't allow creating derivatives |
| allowDifferentLicenses `(OPTIONAL)` | boolean | Filter to models that allow or don't allow derivatives to have a different license |
| allowCommercialUse `(OPTIONAL)` | enum `(None, Image, Rent, Sell)` | Filter to models based on their commercial permissions |
| nsfw `(OPTIONAL)` | boolean | If false, will return safer images and hide models that don't have safe images  |
| supportsGeneration `(OPTIONAL)` | boolean | If true, will return models that support generation |
| ids `(OPTIONAL)` | number[] | If provided will only return the provided ids. Ignored if a query is provided. |
| baseModels `(OPTIONAL)` | string[] | If provided will only return models of the provided base model types. |



#### Response Fields

| Name | Type | Description |
|---|---|---|
| id | number | The identifier for the model |
| name | string | The name of the model |
| description | string | The description of the model (HTML) |
| type | enum `(Checkpoint, TextualInversion, Hypernetwork, AestheticGradient, LORA, Controlnet, Poses)` | The model type |
| nsfw | boolean | Whether the model is NSFW or not |
| tags | string[] | The tags associated with the model |
| mode | enum `(Archived, TakenDown)` \| null | The mode in which the model is currently on. If `Archived`, files field will be empty. If `TakenDown`, images field will be empty |
| creator.username | string | The name of the creator |
| creator.image | string \| null | The url of the creators avatar |
| stats.downloadCount | number | The number of downloads the model has |
| stats.favoriteCount | number | The number of favorites the model has |
| stats.commentCount | number | The number of comments the model has |
| stats.ratingCount | number | The number of ratings the model has |
| stats.rating | number | The average rating of the model |
| modelVersions.id | number | The identifier for the model version |
| modelVersions.name | string | The name of the model version |
| modelVersions.description| string | The description of the model version (usually a changelog) |
| modelVersions.createdAt | Date | The date in which the version was created |
| modelVersions.downloadUrl | string | The download url to get the model file for this specific version |
| modelVersions.trainedWords | string[] | The words used to trigger the model |
| modelVersions.files.sizeKb | number | The size of the model file |
| modelVersions.files.pickleScanResult | string | Status of the pickle scan ('Pending', 'Success', 'Danger', 'Error') |
| modelVersions.files.virusScanResult | string | Status of the virus scan ('Pending', 'Success', 'Danger', 'Error') |
| modelVersions.files.scannedAt | Date \| null | The date in which the file was scanned |
| modelVersions.files.primary | boolean \| undefined | If the file is the primary file for the model version |
| modelVersions.files.metadata.fp | enum (`fp16`, `fp32`) \| undefined | The specified floating point for the file |
| modelVersions.files.metadata.size | enum (`full`, `pruned`) \| undefined | The specified model size for the file |
| modelVersions.files.metadata.format | enum (`SafeTensor`, `PickleTensor`, `Other`) \| undefined | The specified model format for the file |
| modelVersions.images.id | string | The id for the image |
| modelVersions.images.url | string | The url for the image |
| modelVersions.images.nsfw | string | Whether or not the image is NSFW (note: if the model is NSFW, treat all images on the model as NSFW) |
| modelVersions.images.width | number | The original width of the image |
| modelVersions.images.height | number | The original height of the image |
| modelVersions.images.hash | string | The [blurhash](https://blurha.sh/) of the image |
| modelVersions.images.meta | object \| null | The generation params of the image |
| modelVersions.stats.downloadCount | number | The number of downloads the model has |
| modelVersions.stats.ratingCount | number | The number of ratings the model has |
| modelVersions.stats.rating | number | The average rating of the model |
| metadata.totalItems | string | The total number of items available |
| metadata.currentPage | string | The the current page you are at |
| metadata.pageSize | string | The the size of the batch |
| metadata.totalPages | string | The total number of pages |
| metadata.nextPage | string | The url to get the next batch of items |
| metadata.prevPage | string | The url to get the previous batch of items |

**Note:** The download url uses a `content-disposition` header to set the filename correctly. Be sure to enable that header when fetching the download. For example, with `wget`:
```
wget https://civitai.com/api/download/models/{modelVersionId} --content-disposition
```

If the creator of the asset that you are trying to download requires authentication, then you will need an API Key to download it:
```
wget https://civitai.com/api/download/models/{modelVersionId}?token={api_key} --content-disposition
```

#### Example

```sh
curl https://civitai.com/api/v1/models?limit=1&types=TextualInversion \
-H "Content-Type: application/json" \
-X GET
```

This would yield the following response:
```json
{
  "items":[
    {
      "id":3036,
      "name":"CharTurner - Character Turnaround helper for 1.5 AND 2.1!",
      "description":"<h1>CharTurner</h1><p>Edit: <strong>controlNet</strong> works <strong>great </strong>with this. Charturner keeps the outfit consistent, controlNet openPose keeps the turns under control. </p><p><strong>Three versions,</strong> scroll down to pick the right one for you.</p><p>If you're unsure of what version you are running, it's <em>probably</em> 1.5, as it is more popular, but 2.1 is newer and gaining ground fast.</p><p><strong>Version 2, for 2.0 and 2.1 models<br />Version 2, for 1.5 models<br />Version 1, for 1.5 models</strong></p><p>BONUS: <a target=\"_blank\" rel=\"ugc\" href=\"https://civitai.com/models/7252/charturnerbeta-lora-experimental\">Experimental </a>LORA released<br />used at your own risk. :D (mixes well tho)</p><p>Hey there! I'm a working artist, and I loathe doing character turnarounds, I find it the least fun part of character design. I've been working on an embedding that helps with this process, and, though it's not where I want it to be, I was encouraged to release it under the <a target=\"_blank\" rel=\"ugc\" href=\"https://en.wikipedia.org/wiki/Minimum_viable_product\"><u>MVP</u></a> principle.</p><p>I'm also working on a few more character embeddings, including a head turn around and an expression sheet. They're still way too raw to release tho.</p><p>Is there some type of embedding that would be useful for you? Let me know, i'm having fun making tools to fix all the stuff I hate doing by hand.</p><p>v1 is still a little bit... fiddly.</p><ul><li><p>Sampler: I use DPM++ 2m Karras or DDIM most often.</p></li><li><p>Highres. fix ON for best results</p></li><li><p>landscape orientation will get you more 'turns'; square images tend toward just front and back.</p></li><li><p>I like <a target=\"_blank\" rel=\"ugc\" href=\"https://civitai.com/models/2540/elldreths-stolendreams-mix\"><u>https://civitai.com/models/2540/elldreths-stolendreams-mix</u></a> to make characters in.</p></li><li><p>I use an embedding trained on my own art (smoose) that I will release if people want it? But it's an aesthetic thing, just my own vibe.</p></li><li><p>I didn't really test this in any of the waifu/NAI type models, as I don't usually use them. Looks like it works but it probably has its own special dance.</p></li></ul><p>Things I'm working on for v2: EDIT: <strong>V2 out, see below! (also v2 2.1)</strong></p><ul><li><p>It fights you on style sometimes. I'm adding more various types of art styles to the dataset to combat this. -<strong> V2 has much better styles</strong></p></li><li><p>Open front coats and such tend to be open 'back' on the back view. Adding more types of clothing to the dataset to combat this. - <strong>Still has this problem</strong></p></li><li><p>Tends toward white and 'fit' characters, which isn't useful. Adding more diversity in body and skin tone to the dataset to combat this. - <strong>v2 Much more body and racial diversity added to the set, easier to get different results.</strong></p></li></ul><p>Helps create multiple full body views of a character. The intention is to get at least a front and back, and ideally, a front, 3/4, profile, 1/4 and back versions, in the same outfit.</p><p></p>",
      "type":"TextualInversion",
      "poi":false,
      "nsfw":false,
      "allowNoCredit":true,
      "allowCommercialUse":"Rent",
      "allowDerivatives":true,
      "allowDifferentLicense":true,
      "stats":{
        "downloadCount":56206,
        "favoriteCount":7433,
        "commentCount":236,
        "ratingCount":56,
        "rating":4.63
      },
      "creator":{
        "username":"mousewrites",
        "image":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/bdfe115f-4430-4ee7-31bc-eff38f86c500/width=96/mousewrites.jpeg"
      },
      "tags":[
        "character",
        "consistent character",
        "turnaround",
        "model sheet"
      ],
      "modelVersions":[
        {
          "id":9857,
          "modelId":3036,
          "name":"CharTurner V2 - For 2.1",
          "createdAt":"2023-02-12T22:44:01.442Z",
          "updatedAt":"2023-03-15T18:58:13.476Z",
          "trainedWords":[
            "21charturnerv2"
          ],
          "baseModel":"SD 2.1",
          "earlyAccessTimeFrame":0,
          "description":"<p>I'm not great at prompting for 2.1 yet, so I\"m sure your prompts will work better with it. Works fantastic with negative embeds. (still collecting links)</p><p><a target=\"_blank\" rel=\"ugc\" href=\"https://civitai.com/models/7728/negativemutation\">https://civitai.com/models/7728/negativemutation</a></p>",
          "stats":{
            "downloadCount":25874,
            "ratingCount":7,
            "rating":4.29
          },
          "files":[
            {
              "name":"21charturnerv2.pt",
              "id":9500,
              "sizeKB":17.017578125,
              "type":"Model",
              "metadata":{
                "fp":"fp16",
                "size":"full",
                "format":"PickleTensor"
              },
              "pickleScanResult":"Success",
              "pickleScanMessage":"No Pickle imports",
              "virusScanResult":"Success",
              "scannedAt":"2023-02-12T22:45:53.210Z",
              "hashes":{
                "AutoV2":"F253ABB016",
                "SHA256":"F253ABB016C22DD426D6E482F4F8C3960766DE6E4C02F151478BFB98F6985383",
                "CRC32":"F500AADD",
                "BLAKE3":"E7163C1A3F6B135A3E473CDD749BC1E6F4ED2D1AB43FEB1ACC4BEB1E5C205260"
              },
              "downloadUrl":"https://civitai.com/api/download/models/9857",
              "primary":true
            }
          ],
          "images":[
            {
              "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/d197481b-1c21-4c14-c7fd-708f838a1000/width=450/96744.jpeg",
              "nsfw":false,
              "width":1238,
              "height":1293,
              "hash":"UAEVA;?]JoR6+^OaNxxC^jXSWXjF?G$~s.WY",
              "meta":null
            }
          ],
          "downloadUrl":"https://civitai.com/api/download/models/9857"
        }
      ]
    }
  ],
  "metadata":{
    "totalItems":1676,
    "currentPage":1,
    "pageSize":1,
    "totalPages":1676,
    "nextPage":"https://civitai.com/api/v1/models?limit=1&types=TextualInversion&page=2"
  }
}
```


### GET /api/v1/models/:modelId

#### Endpoint URL

`https://civitai.com/api/v1/models/:modelId`

#### Response Fields

| Name | Type | Description |
|---|---|---|
| id | number | The identifier for the model |
| name | string | The name of the model |
| description | string | The description of the model (HTML) |
| type | enum `(Checkpoint, TextualInversion, Hypernetwork, AestheticGradient, LORA, Controlnet, Poses)` | The model type |
| nsfw | boolean | Whether the model is NSFW or not |
| tags| string[] | The tags associated with the model |
| mode | enum `(Archived, TakenDown)` \| null | The mode in which the model is currently on. If `Archived`, files field will be empty. If `TakenDown`, images field will be empty |
| creator.username | string | The name of the creator |
| creator.image | string \| null | The url of the creators avatar |
| modelVersions.id | number | The identifier for the model version |
| modelVersions.name | string | The name of the model version |
| modelVersions.description| string | The description of the model version (usually a changelog) |
| modelVersions.createdAt | Date | The date in which the version was created |
| modelVersions.downloadUrl | string | The download url to get the model file for this specific version |
| modelVersions.trainedWords | string[] | The words used to trigger the model |
| modelVersions.files.sizeKb | number | The size of the model file |
| modelVersions.files.pickleScanResult | string | Status of the pickle scan ('Pending', 'Success', 'Danger', 'Error') |
| modelVersions.files.virusScanResult | string | Status of the virus scan ('Pending', 'Success', 'Danger', 'Error') |
| modelVersions.files.scannedAt | Date \| null | The date in which the file was scanned |
| modelVersions.files.metadata.fp | enum (`fp16`, `fp32`) \| undefined | The specified floating point for the file |
| modelVersions.files.metadata.size | enum (`full`, `pruned`) \| undefined | The specified model size for the file |
| modelVersions.files.metadata.format | enum (`SafeTensor`, `PickleTensor`, `Other`) \| undefined | The specified model format for the file |
| modelVersions.images.url | string | The url for the image |
| modelVersions.images.nsfw | string | Whether or not the image is NSFW (note: if the model is NSFW, treat all images on the model as NSFW) |
| modelVersions.images.width | number | The original width of the image |
| modelVersions.images.height | number | The original height of the image |
| modelVersions.images.hash | string | The [blurhash](https://blurha.sh/) of the image |
| modelVersions.images.meta | object \| null | The generation params of the image |

**Note:** The download url uses a `content-disposition` header to set the filename correctly. Be sure to enable that header when fetching the download. For example, with `wget`:
```
wget https://civitai.com/api/download/models/{modelVersionId} --content-disposition
```

#### Example

```sh
curl https://civitai.com/api/v1/models/1102 \
-H "Content-Type: application/json" \
-X GET
```

This would yield the following response:
```json
{
  "id":1102,
  "name":"SynthwavePunk",
  "description":"<p>This is a 50/50 Merge of <a target=\"_blank\" rel=\"ugc\" href=\"https://civitai.com/models/1061\">Synthwave</a> and <a target=\"_blank\" rel=\"ugc\" href=\"https://civitai.com/models/1087\">InkPunk</a> you can use both of their keywords and use prompt weighting to balance between these two cool and complimentary styles.</p><p><strong>I'm on the search for V3!</strong> Check out these <a rel=\"ugc\" href=\"https://civitai.com/models/2856/synthpunk-search\">potential candidates</a> and let me know which you prefer and if either of them are good enough to be the latest version of this model.</p>",
  "type":"Checkpoint",
  "poi":false,
  "nsfw":false,
  "allowNoCredit":true,
  "allowCommercialUse":"Sell",
  "allowDerivatives":true,
  "allowDifferentLicense":true,
  "stats":{
    "downloadCount":15347,
    "favoriteCount":2540,
    "commentCount":22,
    "ratingCount":27,
    "rating":4.93
  },
  "creator":{
    "username":"justmaier",
    "image":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/6046154e-6d32-4500-8772-602edb4a4600/width=96/justmaier.jpeg"
  },
  "tags":[
    {
      "name":"punk"
    }
  ],
  "modelVersions":[
    {
      "id":1144,
      "modelId":1102,
      "name":"V2",
      "createdAt":"2022-11-30T01:14:36.498Z",
      "updatedAt":"2023-02-18T23:08:24.115Z",
      "trainedWords":[
        "snthwve style",
        "nvinkpunk"
      ],
      "baseModel":"SD 1.5",
      "earlyAccessTimeFrame":0,
      "description":"<p>Upgraded to InkPunk V2.</p><p>This version definitely seems to have picked up more of the InkPunk side of things.</p>",
      "stats":{
        "downloadCount":14195,
        "ratingCount":19,
        "rating":4.89
      },
      "files":[
        {
          "name":"synthwavepunk_v2.ckpt",
          "id":196,
          "sizeKB":2082690.173828125,
          "type":"Model",
          "metadata":{
            "fp":"fp16",
            "size":"pruned",
            "format":"PickleTensor"
          },
          "pickleScanResult":"Success",
          "pickleScanMessage":"No Pickle imports",
          "virusScanResult":"Success",
          "scannedAt":"2022-12-07T10:52:53.433Z",
          "hashes":{
            "AutoV1":"27EA8C02",
            "AutoV2":"DC4C67171E",
            "SHA256":"DC4C67171E2EB64B1A79DA7FDE1CB3FCBEF65364B12C8F5E30A0141FD8C88233",
            "CRC32":"A72626DB",
            "BLAKE3":"02B54CF802A83AEE4DC531E13DA29EEA6DD26FAFFB73E706A0B073FA2304A8F9"
          },
          "downloadUrl":"https://civitai.com/api/download/models/1144",
          "primary":true
        }
      ],
      "images":[
        {
          "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/3cabeab1-a1c9-4a02-ac76-3a9ed69a1700/width=450/9304.jpeg",
          "nsfw":true,
          "width":512,
          "height":704,
          "hash":"UGH,Y~2o0Y=@5O||S=ENA7vy4.JC9#B-=|rx",
          "meta":{
            "Size":"512x704",
            "seed":785137026,
            "steps":30,
            "prompt":"snthwve style nvinkpunk drunken beautiful woman as delirium from sandman, (hallucinating colorful soap bubbles), by jeremy mann, by sandra chevrier, by dave mckean and richard avedon and maciej kuciara, punk rock, tank girl, high detailed, 8k",
            "sampler":"Euler a",
            "cfgScale":7,
            "Model hash":"27ea8c02",
            "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
          }
        },
        {
          "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/12016264-9e99-457b-d50c-8f262706e000/width=450/9417.jpeg",
          "nsfw":false,
          "width":512,
          "height":704,
          "hash":"UhHVPLO=PCxt?@XAFYs9--w|r?wJt3busmSM",
          "meta":{
            "Size":"512x704",
            "seed":2296294451,
            "steps":30,
            "prompt":"(snthwve style:1) (nvinkpunk:0.7) drunken beautiful woman as delirium from sandman, (hallucinating colorful soap bubbles), by jeremy mann, by sandra chevrier, by dave mckean and richard avedon and maciej kuciara, punk rock, tank girl, high detailed, 8k,\nsharp focus, natural lighting, subsurface scattering, f2, 35mm, film grain",
            "sampler":"DPM++ 2M Karras",
            "cfgScale":7,
            "Batch pos":"0",
            "Batch size":"4",
            "Model hash":"27ea8c02",
            "negativePrompt":"cartoon, 3d, (illustration:1.2), ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
          }
        }
      ],
      "downloadUrl":"https://civitai.com/api/download/models/1144"
    },
    {
      "id":1292,
      "modelId":1102,
      "name":"V3 Alpha",
      "createdAt":"2022-12-07T10:40:26.799Z",
      "updatedAt":"2023-02-18T23:08:24.115Z",
      "trainedWords":[
        "nvinkpunk",
        "snthwve style",
        "style of joemadureira"
      ],
      "baseModel":"SD 1.5",
      "earlyAccessTimeFrame":0,
      "description":"<p>I wanted something that gave characters a little more depth so I've been experimenting with merging in some other models. This one is the new <a href=\"https://civitai.com/models/1223/jomad-diffusion\" rel=\"ugc\" target=\"_blank\">JoMad model</a> with SynthwavePunk V2 added as a difference.</p><p><strong>Warning:</strong> The JoeMad model makes it nearly impossible to get things other than people...</p>",
      "stats":{
        "downloadCount":761,
        "ratingCount":5,
        "rating":5
      },
      "files":[
        {
          "name":"synthwavepunk_v3Alpha.ckpt",
          "id":5149,
          "sizeKB":2082918.40625,
          "type":"Model",
          "metadata":{
            "fp":"fp16",
            "size":"full",
            "format":"PickleTensor"
          },
          "pickleScanResult":"Success",
          "pickleScanMessage":"**Detected Pickle imports (5)**\n```\ncollections.OrderedDict\ntorch._utils._rebuild_tensor_v2\ntorch.HalfStorage\ntorch.IntStorage\ntorch.FloatStorage\n```",
          "virusScanResult":"Success",
          "scannedAt":"2023-01-14T03:05:15.488Z",
          "hashes":{
            "AutoV1":"9CE5CEA2",
            "AutoV2":"76F3EED071",
            "SHA256":"76F3EED071327C9075053368D6997CD613AF949D10B2D3034CEF30A1D1D9FEBA",
            "CRC32":"F15BA0A8",
            "BLAKE3":"F83958C6BD911A59456186EA466C2C17B1827178324CF03CC6C427FB064FFFF9"
          },
          "downloadUrl":"https://civitai.com/api/download/models/1292?type=Model&format=PickleTensor"
        }
      ],
      "images":[
        {
          "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/e82adceb-cae1-45c5-ab39-74850d027200/width=450/10650.jpeg",
          "nsfw":true,
          "width":512,
          "height":704,
          "hash":"USI=DS+|?^V[7z55K#X-DkV[IVtQR*$%V?In",
          "meta":{
            "ENSD":"31337",
            "Size":"512x704",
            "seed":107073939,
            "Model":"joMad+synth-ink-25",
            "steps":24,
            "prompt":"style of joemadureira (nvinkpunk:1.3) (snthwve style:1.4) award winning half body portrait of a woman in a croptop and cargo pants with ombre navy blue teal hairstyle with head in motion and hair flying, paint splashes, splatter, outrun, vaporware, shaded flat illustration, digital art, trending on artstation, highly detailed, fine detail, intricate",
            "sampler":"DPM++ 2M Karras",
            "cfgScale":7,
            "Batch pos":"2",
            "Batch size":"4",
            "Model hash":"5d83b27c",
            "negativePrompt":"cartoon, 3d, ((disfigured)), ((deformed)), ((poorly drawn)), ((extra limbs)), blurry"
          }
        },
        {
          "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/f1471530-4263-4424-d298-ecc484470d00/width=450/10649.jpeg",
          "nsfw":false,
          "width":512,
          "height":704,
          "hash":"UHGuXg~U?bM|NeNwIU-BEkr]=xbE9~NK-oE1",
          "meta":{
            "ENSD":"31337",
            "Size":"512x704",
            "seed":107073947,
            "Model":"joMad+synth-ink-25",
            "steps":24,
            "prompt":"style of joemadureira (nvinkpunk:1.3) (snthwve style:1.4) award winning half body portrait of a woman in a croptop and cargo pants with ombre navy blue teal hairstyle with head in motion and hair flying, paint splashes, splatter, outrun, vaporware, shaded flat illustration, digital art, trending on artstation, highly detailed, fine detail, intricate",
            "sampler":"DPM++ 2M Karras",
            "cfgScale":7,
            "Batch pos":"2",
            "Batch size":"4",
            "Model hash":"5d83b27c",
            "negativePrompt":"cartoon, 3d, ((disfigured)), ((deformed)), ((poorly drawn)), ((extra limbs)), blurry"
          }
        }
      ],
      "downloadUrl":"https://civitai.com/api/download/models/1292"
    },
    {
      "id":1105,
      "modelId":1102,
      "name":"V1",
      "createdAt":"2022-11-27T22:29:29.401Z",
      "updatedAt":"2023-02-18T23:08:24.115Z",
      "trainedWords":[
        "snthwve style",
        "nvinkpunk"
      ],
      "baseModel":"SD 1.5",
      "earlyAccessTimeFrame":0,
      "description":"<p>A 50/50 Merge of <a href=\"https://civitai.com/models/1061\" rel=\"ugc\" target=\"_blank\">Synthwave</a> and <a href=\"https://civitai.com/models/1087\" rel=\"ugc\" target=\"_blank\">InkPunk</a></p>",
      "stats":{
        "downloadCount":390,
        "ratingCount":3,
        "rating":5
      },
      "files":[
        {
          "name":"synthwavepunk_v1.ckpt",
          "id":951,
          "sizeKB":2082867.794921875,
          "type":"Model",
          "metadata":{
            "fp":"fp16",
            "size":"full",
            "format":"PickleTensor"
          },
          "pickleScanResult":"Success",
          "pickleScanMessage":"No Pickle imports",
          "virusScanResult":"Success",
          "scannedAt":"2022-11-27T23:25:17.557Z",
          "hashes":{
            "AutoV1":"C0E7C884",
            "AutoV2":"D7C4EB223D",
            "SHA256":"D7C4EB223DDD4C89D76D2A9A17E32A135CC9E0ADD0D96D196C95F3E3813FBF88",
            "CRC32":"1F103FDD",
            "BLAKE3":"B2DD8EED7EEAA7E5E13321F64B1077B0828F83384BB4FC3180D737F75AAC0A4B"
          },
          "downloadUrl":"https://civitai.com/api/download/models/1105",
          "primary":true
        }
      ],
      "images":[
        {
          "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/c78c9dab-284a-4268-f12d-db66bb0cc700/width=450/9040.jpeg",
          "nsfw":true,
          "width":512,
          "height":704,
          "hash":"UPJs^hPW~oIc@2AEZokW0=Nb5WW=%B$_TAV?",
          "meta":{
            "Size":"512x704",
            "seed":785137024,
            "steps":30,
            "prompt":"snthwve style nvinkpunk drunken beautiful woman as delirium from sandman, (hallucinating colorful soap bubbles), by jeremy mann, by sandra chevrier, by dave mckean and richard avedon and maciej kuciara, punk rock, tank girl, high detailed, 8k",
            "sampler":"Euler a",
            "cfgScale":7,
            "Batch pos":"0",
            "Batch size":"4",
            "Model hash":"c0e7c884",
            "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
          }
        },
        {
          "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/849364cf-1707-40bf-1432-e95fe4f4fb00/width=450/9048.jpeg",
          "nsfw":false,
          "width":512,
          "height":704,
          "hash":"UFHv$62U0=~756}GP2IA5hZg9bo}E,B-tK#G",
          "meta":{
            "Size":"512x704",
            "seed":785137026,
            "steps":30,
            "prompt":"snthwve style nvinkpunk drunken beautiful woman as delirium from sandman, (hallucinating colorful soap bubbles), by jeremy mann, by sandra chevrier, by dave mckean and richard avedon and maciej kuciara, punk rock, tank girl, high detailed, 8k",
            "sampler":"Euler a",
            "cfgScale":7,
            "Batch pos":"2",
            "Batch size":"4",
            "Model hash":"c0e7c884",
            "negativePrompt":"cartoon, 3d, ((disfigured)), ((bad art)), ((deformed)), ((poorly drawn)), ((extra limbs)), ((close up)), ((b&w)), weird colors, blurry"
          }
        }
      ],
      "downloadUrl":"https://civitai.com/api/download/models/1105"
    }
  ]
}
```

### GET /api/v1/models-versions/:modelVersionId

#### Endpoint URL

`https://civitai.com/api/v1/model-versions/:id`

#### Response Fields

| Name | Type | Description |
|---|---|---|
| id | number | The identifier for the model version |
| name | string | The name of the model version |
| description| string | The description of the model version (usually a changelog) |
| model.name | string | The name of the model |
| model.type | enum `(Checkpoint, TextualInversion, Hypernetwork, AestheticGradient, LORA, Controlnet, Poses)` | The model type |
| model.nsfw | boolean | Whether the model is NSFW or not |
| model.poi | boolean | Whether the model is of a person of interest or not |
| model.mode | enum `(Archived, TakenDown)` \| null | The mode in which the model is currently on. If `Archived`, files field will be empty. If `TakenDown`, images field will be empty |
| modelId | number | The identifier for the model |
| createdAt | Date | The date in which the version was created |
| downloadUrl | string | The download url to get the model file for this specific version |
| trainedWords | string[] | The words used to trigger the model |
| files.sizeKb | number | The size of the model file |
| files.pickleScanResult | string | Status of the pickle scan ('Pending', 'Success', 'Danger', 'Error') |
| files.virusScanResult | string | Status of the virus scan ('Pending', 'Success', 'Danger', 'Error') |
| files.scannedAt | Date \| null | The date in which the file was scanned |
| files.metadata.fp | enum (`fp16`, `fp32`) \| undefined | The specified floating point for the file |
| files.metadata.size | enum (`full`, `pruned`) \| undefined | The specified model size for the file |
| files.metadata.format | enum (`SafeTensor`, `PickleTensor`, `Other`) \| undefined | The specified model format for the file |
| stats.downloadCount | number | The number of downloads the model has |
| stats.ratingCount | number | The number of ratings the model has |
| stats.rating | number | The average rating of the model |
| images.url | string | The url for the image |
| images.nsfw | string | Whether or not the image is NSFW (note: if the model is NSFW, treat all images on the model as NSFW) |
| images.width | number | The original width of the image |
| images.height | number | The original height of the image |
| images.hash | string | The [blurhash](https://blurha.sh/) of the image |
| images.meta | object \| null | The generation params of the image |

**Note:** The download url uses a `content-disposition` header to set the filename correctly. Be sure to enable that header when fetching the download. For example, with `wget`:
```
wget https://civitai.com/api/download/models/{modelVersionId} --content-disposition
```

#### Example

The following example shows a request to get a model version from our database:
```sh
curl https://civitai.com/api/v1/model-versions/1318 \
-H "Content-Type: application/json" \
-X GET
```

This would yield the following response:
<details>
<summary>Click to expand</summary>

```json
{
  "id":1318,
  "modelId":1244,
  "name":"toad",
  "createdAt":"2022-12-08T19:58:49.765Z",
  "updatedAt":"2022-12-08T20:24:50.330Z",
  "trainedWords":[
  "ttdddd"
  ],
  "baseModel":"SD 1.5",
  "earlyAccessTimeFrame":0,
  "description":null,
  "stats":{
  "downloadCount":438,
  "ratingCount":1,
  "rating":5
  },
  "model":{
  "name":"froggy style",
  "type":"Checkpoint",
  "nsfw":false,
  "poi":false
  },
  "files":[
  {
    "name":"froggyStyle_toad.ckpt",
    "id":289,
    "sizeKB":2546414.971679688,
    "type":"Model",
    "metadata":{
    "fp":"fp16",
    "size":"full",
    "format":"PickleTensor"
    },
    "pickleScanResult":"Success",
    "pickleScanMessage":"**Detected Pickle imports (3)**\n```\ncollections.OrderedDict\ntorch.HalfStorage\ntorch._utils._rebuild_tensor_v2\n```",
    "virusScanResult":"Success",
    "scannedAt":"2022-12-08T20:15:36.133Z",
    "hashes":{
    "AutoV1":"5F06AA6F",
    "AutoV2":"0DF040C8CD",
    "SHA256":"0DF040C8CD48125174B54C251A87822E8ED61D529A92C42C1FA1BEF483B10B0D",
    "CRC32":"32AEB036",
    "BLAKE3":"7E2030574C35F33545951E6588A19E41D88CEBB30598C17805A87EFFD0DB0A99"
    },
    "primary":true,
    "downloadUrl":"https://civitai.com/api/download/models/1318"
  }
  ],
  "images":[
  {
    "url":"https://imagecache.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/c6ed4a9d-ae75-463b-7762-da0455cc5700/width=450/10852.jpeg",
    "nsfw":false,
    "width":832,
    "height":832,
    "hash":"U8Civ__MTeSP?utJ9IDj?^Ek=}RQyEE1-Vr=",
    "meta":null
  }
  ],
  "downloadUrl":"https://civitai.com/api/download/models/1318"
}
```
</details>

### GET /api/v1/models-versions/by-hash/:hash

#### Endpoint URL

`https://civitai.com/api/v1/model-versions/by-hash/:hash`

#### Response Fields

[Same as standard model-versions endpoint](#response-fields-5)

**Note:** We support the following hash algorithms: AutoV1, AutoV2, SHA256, CRC32, and Blake3

**Note 2:** We are still in the process of hashing older files, so these results are incomplete

### GET /api/v1/tags

#### Endpoint URL

`https://civitai.com/api/v1/tags`

#### Query Parameters

| Name | Type | Description |
|---|---|---|
| limit `(OPTIONAL)` | number | The number of results to be returned per page. This can be a number between 1 and 200. By default, each page will return 20 results. If set to 0, it'll return all the tags |
| page `(OPTIONAL)` | number | The page from which to start fetching tags |
| query `(OPTIONAL)` | string | Search query to filter tags by name |

#### Response Fields

| Name | Type | Description |
|---|---|---|
| name | string | The name of the tag |
| modelCount | number | The amount of models linked to this tag |
| link | string | Url to get all models from this tag |
| metadata.totalItems | string | The total number of items available |
| metadata.currentPage | string | The the current page you are at |
| metadata.pageSize | string | The the size of the batch |
| metadata.totalPages | string | The total number of pages |
| metadata.nextPage | string | The url to get the next batch of items |
| metadata.prevPage | string | The url to get the previous batch of items |

#### Example

The following example shows a request to get the first 3 model tags from our database:
```sh
curl https://civitai.com/api/v1/tags?limit=3 \
-H "Content-Type: application/json" \
-X GET
```

This would yield the following response:
```json
{
  "items": [
    {
    "name": "Pepe Larraz",
    "modelCount": 1,
    "link": "https://civitai.com/api/v1/models?tag=Pepe Larraz"
    }
  ],
  "metadata": {
    "totalItems": 200,
    "currentPage": 1,
    "pageSize": 3,
    "totalPages": 67,
    "nextPage": "https://civitai.com/api/v1/tags?limit=3&page=2"
  }
}
```

# Possible Issues with this Document and/or the API itself:

1. Duplicate "postId" entry in GET /api/v1/images response fields table.
2. Incorrect type descriptions in response fields tables (e.g., "totalItems"
as string but actually number in examples; "tags" as string[] but JSON shows
array of objects).
3. Missing "dislikeCount" field in GET /api/v1/images response fields for
stats (present in JSON example).
4. Typos in endpoint headers: "models-versions" should be "model-versions".
5. Inconsistent parameter names in endpoint URLs (e.g., ":id" vs
":modelVersionId").
