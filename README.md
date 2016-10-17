# API calls
## General
### List
`GET {api-endpoint}/`: Returns a list of all objects

### Fetch
`GET {api-endpoint}/{numeric-key}/`: Returns a single object

### Create
`POST {api-endpoint}/`: Create a new object

### Update
`PUT {api-endpoint}/{numeric-key}/`: Update existing object

## Challenges (endpoint: `api/challenges`)
### Implemented
- [X] List
- [X] Fetch
- [ ] Create
- [ ] Update

## Tips (endpoint: `api/tips`)
### Implemented
- [X] List
- [X] Fetch
- [ ] Create
- [ ] Update

## Users (endpoint: `api/users`)
### Implemented
- [X] List
- [X] Fetch
- [X] Create
- [ ] Update

Post (trivial example):
```javascript
{
    "password": "Garfunkle",
    "profile": {
        "mobile": "5556667777"
    }
}
```
When no `username` is supplied, the `profile` object is checked for `mobile`
(a mobile number) and this is used as the username.

# Authentication

The REST service uses token authentication.

## Retrieving a token

To retrieve the user's token, `POST` the username and password to the token
endpoint.

`POST /api/token/`
```json
{
  "username" : "{username}",
  "password" : "{password}"
}
```

If the user's credentials are correct, the service will respond with HTTP status `200`.

```json
{
  "token" : "ef1595a6cc293e19cc46908ef9e5754598a922fd"
}
```

In subsequent requests to resource endpoints, the token must be included in the
HTTP `Authorization` header, prepended with the `Token` keyword and separated
with whitespace.

```
Authorization: Token ef1595a6cc293e19cc46908ef9e5754598a922fd
```

The token is created and stored in the service's database, and will stay the
same between subsequent requests to `/api/token/`. Changing the user's
password will clear the token, and a new token will have to be retrieved.

## Errors

At login, when the provided username and/or password is incorrect, or the user
is disabled.

`400 Bad Request`
```json
{
  "non_field_errors": [
    "Unable to log in with provided credentials."
  ]
}
```

When the provided token does not match the token in the database.

`401 Unauthorized`
```json
{
  "detail": "Invalid token."
}
```

When attempting to access a protected endpoint with no `Authorization` header set.

`401 Unauthorized`
```json
{
  "detail": "Authentication credentials were not provided."
}
```
