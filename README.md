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

