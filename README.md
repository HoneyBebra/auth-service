# Auth service

## Deploy
1) Create ```.env```-file like ```.env.example```

2) Build
    ```shell
    docker compose up -d --build
    ```

3) Apply migrations:
    ```commandline
    docker exec -it auth /bin/sh
    ```
    ```commandline
    alembic upgrade head
    ```

## API documentation:
http://127.0.0.1/auth/api/v1/openapi

## To perform a basic check of the service
You need to test in `Google Chrome`, because the code sets cookies with the 
`httponly=True` setting. With this setting, Chrome considers the 
http://localhost connection secure, while `Safari`, for example, 
requires a https connection.
1) signup
2) login
3) me
4) refresh
5) me
6) logout
7) me

## PostgreSQL schema:
```
    ┌──────────────────────────────────────────────────────────────────────────────────┐
    │  (users)                                                                         │
    │----------------------------------------------------------------------------------│
    │ name                   │ type     │ key         │ is unique │ is null  │ default │
    │----------------------------------------------------------------------------------│
    │ id                     │ UUID     │ primary key │ unique    │ not null │         │  
    │ login                  │ string   │             │           │ not null │         │
    │ password               │ string   │             │           │ not null │         │
    │ encrypted_phone_number │ string   │             │ unique    │ nullable │         │
    │ phone_number_hash      │ string   │             │ unique    │ nullable │         │
    │ encrypted_email        │ string   │             │ unique    │ nullable │         │
    │ email_hash             │ string   │             │ unique    │ nullable │         │
    │ created_at             │ datetime │             │           │ not null │         │
    │ updated_at             │ datetime │             │           │ not null │         │
    └──────────────────────────────────────────────────────────────────────────────────┘
```

## Redis schema:
```
    ┌──────────────────┬──────────────────────────────────────────────┬──────────────┬────────────────────────────────────────────────────────────────────────────┐
    │ prefix           │ key pattern                                  │ value        │ TTL                                                                        │
    ├──────────────────┼──────────────────────────────────────────────┼──────────────┼────────────────────────────────────────────────────────────────────────────┤
    │ auth:jwt:bl      │ auth:jwt:bl:{jwt_token}                      │ "none"       │ settings.jwt.access_token_expire / settings.jwt.refresh_token_expire       │
    │ auth:rl          │ auth:rl:login:fail:{identifier_hash}         │ int (count)  │ settings.rate_limit.login_failed_window_seconds                            │
    │ auth:rl          │ auth:rl:login:lock:{identifier_hash}         │ "none"       │ settings.rate_limit.login_lock_duration_seconds                            │
    └──────────────────┴──────────────────────────────────────────────┴──────────────┴────────────────────────────────────────────────────────────────────────────┘
```

## Architecture contracts

See [docs/contracts.md](docs/contracts.md).
