# API concerns

## Response envelopes 
The vast majority of enterprise APIs return POJOs directly and do not use wrappers. This makes the Crunch API different and not in a positive way. 
Even experienced api developers will have a learning curve ahead of them before they can write to our api.  

## Inconsistent wrappers
Even in the very rare instances of enterprise APIs that do wrap POJOs do so [in a consistent way](https://jsonapi.org/) 
where the POJO is always located at `response.data`. Crunch envelopes are different - you have to look for the POJO in a different
place depending on which endpoint you call and what shoji element type gets returned.

## Trailing slashes
Crunch endpoints do not follow industry standards regarding trailing slashes. Specifically, Crunch endpoint urls require trailing slashes when most documented enterprise APIs and API best practice guides prohibit them. 
As such, many oas editors give you error messages (best case) or try to automatically strip trailing slashes (worst case).

## IDs or urls?
Once in a while, an id field will just be an id but most of the time it will be a url. Confusing?

Example: dataset 69ec37de2efe483fb81e910ec360b97c
```javascript
{
    "https://app.crunch.io/api/datasets/69ec37de2efe483fb81e910ec360b97c/": {
      "owner_id": "https://app.crunch.io/api/projects/70bc37797d734a868fb9bb641cbbcd80/",
      "id": "69ec37de2efe483fb81e910ec360b97c",
    }
}
```

## Arrays expressed as objects
When an api returns an array of objects, everyone immediately knows it's an array of objects and can iterate over that array.
When the Crunch api represents one array with 10 elements as one object with 10 properties, it's not immediately obvious that it's an array
and can be iterated. 

Example: object that isn't an array:
```javascript
"body": {
    "modification_time": "2020-04-07T21:50:10.029000",
    "name": "Shared",
    "owner": "https://app.crunch.io/api/users/1168fb80e331419e9e0b2695714b32b3/",
    "access_time": "2020-04-02T14:18:20.032000",
    "permissions": {
      "edit": false,
      "view": true
    },
    "owner_id": "https://app.crunch.io/api/users/1168fb80e331419e9e0b2695714b32b3/",
    "description": "Items that other users have shared with you"
  }
```
Example: object that is supposed to be an array but not constructed as an array:
```javascript
 "index": {
    "https://app.crunch.io/api/datasets/69ec37de2efe483fb81e910ec360b97c/": {
      "size": {
        "rows": 10596,
        "unfiltered_rows": 10596,
        "columns": 6364
      },
      "is_published": true,
      "type": "dataset",
      "id": "69ec37de2efe483fb81e910ec360b97c",
      "description": ""
    },
    "https://app.crunch.io/api/datasets/9f1f51ac5b70492c9e573288e9e6bed6/": {
      "size": {
        "rows": 1500,
        "unfiltered_rows": 1866,
        "columns": 949
      },

      "is_published": true,
      "type": "dataset",
      "id": "9f1f51ac5b70492c9e573288e9e6bed6",
      "description": ""
    }
  }
```

## Color palette object design is really bad
Analysis is an array of color palette objects but instead of each color palette objects being defined as

Good:
```javascript
{
    "name": "my palette name",
    "default": false,
    "palette": [
      "#9d7dc9",
      "#7f0a00",
      "#0074bf",
    ]
}
```

Bad: Single-property object with embedded object
```javascript
{
    "my palette name": {
        "default": false,
        "palette": [
          "#9d7dc9",
          "#7f0a00",
          "#0074bf",
        ]
    }
}
```

Real-life example:
```javascript
"palette": {
      "analysis": [
        {
          "Black Hats are black": {
            "default": false,
            "palette": [
              "#ffa299",
              "#9100bf",
              "#ff6f00",
              "#7f6702"
            ]
          }
        },
        {
          "White Hats are LAME": {
            "default": false,
            "palette": [
              "#9d7dc9",
              "#7f0a00",
              "#0074bf",
              "#005283",
              "#bf1001",
              "#ffac7f",
              "#ffac7f",
              "#bf1001"
            ]
          }
        },
```

## snake_case and camelCase inconsistencies
We mix snake-case and camel-case properties in the same object
```javascript
"preferences": {
  "search_settings": {},
  "features": {},
  "displaySettings": {},
  "datasetDisplaySettings": {},
  "projectId": "https://alpha.crunch.io/api/projects/d22b37e0258a4986b29598fc79ccc24f/",
  "notificationsReadDate": "2020-04-16T20:04:05.281Z",
  "openedDecks": {      },
  "varCardSettings": {},
  "dsVisibleProps": {},
  "notificationsSnoozeDate": null,
  "projectBrowser": {}
}
```

## POST query string no body
https://docs.crunch.io/endpoint-reference/endpoint-public.html#preview

This endpoint requires post + query string parameter. RapiDoc forces you to pass content type in post body which breaks the endpoint. Not possible to test this endpoint
in documentation, only via curl.

## Inconsistent plurals
PATCH /account/templates/ - only removes one template. To be fair, only one template exists now but we might add more template types later.

PATCH /account/logo/ - Removes one, two, or three logos.

## Bad documentation
Wrong url https://docs.crunch.io/endpoint-reference/endpoint-public.html#share

Wrong url https://docs.crunch.io/endpoint-reference/endpoint-public.html#preview
