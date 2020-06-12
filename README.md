# API Endpoints for M2 module

Port: 8082

## Calc m2 value, given workers, hotdesking and collaborate grade 

**URL** : `/api/m2`

**Required Body** : 
```json
{
    "hotdesking_level": 75, //Integer between 70 and 100
    "colaboration_level": 40, //Integer between 30 and 50
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
