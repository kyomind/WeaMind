# Redis ACL for production

`docker-compose.prod.yml` starts Redis with `--aclfile /usr/local/etc/redis/users.acl`. The aclfile lives on the data host at `/etc/weamind/redis/users.acl`, outside the repo, and is bind-mounted read-only. If the host file is missing, the container fails to start instead of running without it (`create_host_path: false`).

Local development (`docker-compose.yml` alone, or with `docker-compose.dev.yml`) does not use the aclfile and needs no password.

## File format

See `users.acl.example`:

- `user default off ...` disables the default user. Redis creates `default` with `nopass` when the aclfile does not mention it, so this line is required.
- `user weamind on #<sha256> ...` is the account the app uses. The password is stored as the SHA-256 hex digest of the password, prefixed with `#`.

The app connects with `REDIS_URL=redis://weamind:<password>@<host>:6379/0`. Use a hex password (for example from `openssl rand -hex 32`) so it needs no URL encoding.

## Creating the aclfile

Keep the password in a file and never pass it as a command argument, so it does not show up in the terminal, shell history, or process list:

```bash
umask 077
openssl rand -hex 32 | tr -d '\n' > redis-weamind.pw

hash=$(sha256sum < redis-weamind.pw | cut -d' ' -f1)
{
  echo "user default off resetpass resetkeys resetchannels -@all"
  printf 'user weamind on #%s ~* &* +@all\n' "$hash"
} > users.acl
unset hash
```

On the data host, install it readable only by the container's `redis` user (uid 999):

```bash
sudo install -d -m 0755 /etc/weamind/redis
sudo install -m 0400 -o 999 -g 999 users.acl /etc/weamind/redis/users.acl
```

Then recreate only the Redis service:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d redis
```

## Changing users

The aclfile is mounted read-only, so `ACL SAVE` does not work. Edit the host file and either restart the container or run `ACL LOAD`.
