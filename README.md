# API Endpoints for M2 module

Port: 8082

## Calc m2 value, given workers, hotdesking and collaborate grade 

**URL** : `/api/m2/new/{project_id}`

**URL Parameters** : `{project_id}=[integer]` where `{project_id}` is the ID of the Project on the server.

**Required Body** : 
```json
{
    "hotdesking_level": "HIGH", //HIGH | MID | LOW
    "colaboration_level": "HIGH", //HIGH | MID | LOW
    "num_of_workers": 100 //Integer grather than 0.
} 
```
**Method** : `GET`

**Auth required** : -

**Permissions required** : -

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

**Condition** :  If Account does not exist with `id` of provided parameter.

**Code** : `404 NOT FOUND`

**Content** : `{}`

**Condition** :  If server has some error.

**Code** : `500 Internal Error Server`

**Content** : `{}`
