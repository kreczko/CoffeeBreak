Script to create groups and users from a YAIM users.conf file.

First, convert users.conf (this will create `groups.file` and `users.file`)
```
python usersconf2newusers.py users.conf
```
Next create groups and users
```
# groups
python create_groups.py groups.file
python create_users.py users.file
```

Done
