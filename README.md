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

**Content** : `{error_message}`

## Generate workspaces with quantity and observation values for each subcategory, given workers, hotdesking, collaborate level and calculated area.

**URL** : `/api/m2/generate`

**Required Body** : 
```json
{
    "hotdesking_level": 75, //Integer between 70 and 100
    "colaboration_level": 40, //Integer between 30 and 50
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
  "colaboration_level": 40, //Colaboration level previously entered by the user.
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

**Content** : `{error_message}`
