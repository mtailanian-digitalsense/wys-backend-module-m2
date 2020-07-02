# API Endpoints for M2 module

Port: 8082

## Calc m2 value, given workers, hotdesking and collaborate grade 

**URL** : `/api/m2`

**Required Body** : 
```json
{
    "hotdesking_level": 75, //Integer between 70 and 100
    "collaboration_level": 40, //Integer between 30 and 50
    "num_of_workers": 100 //Integer grather than 0.
} 
```
**Method** : `POST`

**Auth required** : YES

### Success Response

**Code** : `200 OK`

**Content example**

For a project with ID 123 in the local database where that project, the backend return the estimated_area

```json
{
    "area": 123.0 //Decimal value
}
```

### Error Responses

**Condition** :  If server has some error.

**Code** : `500 Internal Error Server`

**Content** : `Error: mesg -> {error_message}`

### Or

**Condition**: Missing data in the body request

**Code** : `400 Bad Request`

**Content** : `Error: mesg -> Missing data in the body request`

## Generate workspaces with quantity and observation values for each subcategory, given workers, hotdesking, collaborate level and calculated area.

**URL** : `/api/m2/generate`

**Required Body** : 
```json
{
    "hotdesking_level": 75, //Integer between 70 and 100
    "collaboration_level": 40, //Integer between 30 and 50
    "num_of_workers": 100, //Integer grather than 0.
    "area": 516.5305429864253 //Float: Calculated area
} 
```
**Method** : `POST`

**Auth required** : YES

### Success Response

**Code** : `200 OK`

**Content example**

For a values in the **Required Body** example, the backend return this data with the quantity and observation for each subcategory. In addition, for each subcategory, its respective category and the ID's of its associated spaces are returned.

```json
{
    
  "area": 516.5305429864253, //Generated area value
  "collaboration_level": 40, //Collaboration level previously entered by the user.
  "hotdesking_level": 75, //Hotdesking level previously entered by the user.
  "num_of_workers": 100, //Workers number previously entered by the user.
  "workspaces": [ //Array of workspaces (Categories->Subcategories->Spaces)
    {
      "id": 1,
      "name": "Sala Reunión", //Category name
      "subcategories": [
        {
          "area": 8.64, //Float: Subcategory area value
          "category_id": 1, //Parent Category id
          "id": 1, //Subcategory id
          "name": "Pequeña", //Subcategory name
          "observation": 16,    //Integer: Observation value generated
          "people_capacity": 5.0, //Float: Subcategory people capacity value
          "quantity": 3, //Integer: Quantity value generated
          "spaces": [ //Array of associated spaces to subcategory
            {
              "id": 15 //Space ID
            }
          ],
          "unit_area": 1.73, //Float: Subcategory unit area value
          "usage_percentage": 0.45 //Float: Subcategory usage percentage value (in decimal)
        },
        {
          "area": 17.29,
          "category_id": 1,
          "id": 2,
          "name": "Mediana",
          "observation": 12,
          "people_capacity": 8.0,
          "quantity": 2,
          "spaces": [
            {
              "id": 16
            }
          ],
          "unit_area": 2.16,
          "usage_percentage": 0.35
        },
        ...
      ]
    },
    {
      "id": 2,
      "name": "Privado",
      "subcategories": [
        {
          "area": 11.93,
          "category_id": 2,
          "id": 4,
          "name": "Pequeño",
          "observation": null,
          "people_capacity": 1.0,
          "quantity": 0,
          "spaces": [
            {
              "id": 17
            },
            {
              "id": 18
            }
          ],
          "unit_area": 11.93,
          "usage_percentage": null
        },
        ...
      ]
    },
    ...
  ]
}
```

### Error Responses

**Condition** :  If server has some error.

**Code** : `500 Internal Error Server`

**Content** : `Error: mesg -> {error_message}`

### Or

**Condition**: Missing data in the body request

**Code** : `400 Bad Request`

**Content** : `Error: mesg -> Missing data in the body request`

## Save and update generated workspaces

**URL** : `/api/m2/save`

**Required Body** : 

**IMPORTANT**: The required body must contain only the subcategories for which the user established **a value of quantity greater than 0**, in addition to only the ID's of the **selected spaces**.

```json
{
  "project_id": 3, //Project ID must be added.
  "area": 516.5305429864253,
  "collaboration_level": 40,
  "hotdesking_level": 75,
  "num_of_workers": 100,
  "workspaces": [
    {
      "id": 1,
      "name": "Sala Reunión",
      "subcategories": [
        {
          "area": 8.64,
          "category_id": 1,
          "id": 1,
          "name": "Pequeña",
          "observation": 16,
          "people_capacity": 5.0,
          "quantity": 3,
          "spaces": [
            {
              "id": 15
            }
          ],
          "unit_area": 1.73,
          "usage_percentage": 0.45
        },
          {
          "area": 17.29,
          "category_id": 1,
          "id": 2,
          "name": "Mediana",
          "observation": 12,
          "people_capacity": 8.0,
          "quantity": 2,
          "spaces": [
            {
              "id": 16
            }
          ],
          "unit_area": 2.16,
          "usage_percentage": 0.35
        }
      ]
    },
    {
      "id": 2,
      "name": "Privado",
      "subcategories": [
        {
          "area": 11.93,
          "category_id": 2,
          "id": 4,
          "name": "Pequeño",
          "observation": null,
          "people_capacity": 1.0,
          "quantity": 5,
          "spaces": [
            {
              "id": 17
            }
          ],
          "unit_area": 11.93,
          "usage_percentage": null
        }
      ]
    }
  ]
}
```
**Method** : `POST`

**Auth required** : YES

### Success Response

**Code** : `200 OK`

**Content example**

Complete information of the Project with its saved m2 configuration.

```json
{
  "id": 3,
  "location_gen_id": 1,
  "m2_generated_data": {
    "area": 516.531,
    "collaboration_level": 40,
    "density": 5.16531,
    "hot_desking_level": 75,
    "id": 5,
    "project_id": 3,
    "workers_number": 100,
    "workspaces": [
      {
        "id": 9,
        "m2_gen_id": 5,
        "observation": 16,
        "quantity": 3,
        "space_id": 15
      },
      {
        "id": 10,
        "m2_gen_id": 5,
        "observation": 12,
        "quantity": 2,
        "space_id": 16
      },
      {
        "id": 11,
        "m2_gen_id": 5,
        "observation": null,
        "quantity": 5,
        "space_id": 17
      }
    ]
  },
  "name": "TEST5",
  "user_id": 23
}
```

### Error Responses

**Condition** :  If server has some error.

**Code** : `500 Internal Error Server`

**Content** : `Error: mesg -> {error_message}`

### Or

**Condition**: Body isn't application/json

**Code** : `400 Bad Request`

**Content** : `Error: mesg -> Body isn't application/json`

## Get a latest m2 configuration of current project

**URL** : `/api/m2/{project_id}`

**Method** : `GET`

**Auth required** : YES

### Success Response

**Code** : `200 OK`

**Content example:**
If the project's id is 3, then the response will be: 
````json
{
  "id": 3,
  "location_gen_id": 1,
  "m2_generated_data": {
    "area": 516.531,
    "collaboration_level": 40,
    "density": 5.16531,
    "hot_desking_level": 75,
    "id": 5,
    "project_id": 3,
    "workers_number": 100,
    "workspaces": [
      {
        "id": 9,
        "m2_gen_id": 5,
        "observation": 16,
        "quantity": 3,
        "space_id": 15
      },
      {
        "id": 10,
        "m2_gen_id": 5,
        "observation": 12,
        "quantity": 2,
        "space_id": 16
      },
      {
        "id": 11,
        "m2_gen_id": 5,
        "observation": null,
        "quantity": 5,
        "space_id": 17
      }
    ]
  },
  "name": "TEST5",
  "user_id": 23
}
````

### Error Responses

**Condition** :  If server has some error.

**Code** : `500 Internal Error Server`

**Content** : `Error: mesg -> {error_message}`

### Or

**Condition** :  Project not found or the Proyect doesn't have a m2 configuration created.

**Code** : `404 Not Found`

**Content** : `Error: mesg -> {error_message}`

## Show all M2 constants

**URL** : `/api/m2/constants`

**Method** : `GET`

**Auth required** : YES

### Success Response

**Code** : `200 OK`

**Content example**

```json
[
    {
      "id": 1,
      "name": "PUESTO TRABAJO OPENPLAN",
      "value": 3.26
    },
    {
      "id": 2,
      "name": "SALA REUNION PEQUEÑA",
      "value": 1.73
    },
    ...
]
```

### Error Responses

**Condition** : If an error occurs with the database.

**Code** : `500 Internal Server Error`

**Content** : `{exception_message}`

## Update M2 constants values

**URL** : `/api/m2/constants`

**Required Body** : 

**IMPORTANT**: The names of the constants are not required and should not be included for now.

```json
[
    {
      "id": 1,
      "value": 3.14
    },
    {
      "id": 2,
      "value": 2.9
    },
    ...
]
```

**Method** : `PUT`

**Auth required** : YES

### Success Response

**Code** : `200 OK`

**Content example**

All constants info. and updated values:

```json
[
    {
      "id": 1,
      "name": "PUESTO TRABAJO OPENPLAN",
      "value": 3.14
    },
    {
      "id": 2,
      "name": "SALA REUNION PEQUEÑA",
      "value": 2.9
    },
    ...
]
```

### Error Responses

**Condition** :  If the body data is not included or the body data is not `application/json`.

**Code** : `404 Not Found`

**Content** : `Error: mesg -> {error_message}`

### Or

**Condition** : If an error occurs with the database.

**Code** : `500 Internal Server Error`

**Content** : `{exception_message}`