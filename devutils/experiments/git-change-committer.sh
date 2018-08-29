#!/bin/sh


# From https://help.github.com/articles/changing-author-info/

git filter-branch --env-filter '

OLD_EMAIL="ecrire@actuino.com"
CORRECT_NAME="EggPool"
CORRECT_EMAIL="dev@eggpool.net"

if [ "$GIT_COMMITTER_EMAIL" = "$OLD_EMAIL" ]
then
    export GIT_COMMITTER_NAME="$CORRECT_NAME"
    export GIT_COMMITTER_EMAIL="$CORRECT_EMAIL"
fi
if [ "$GIT_AUTHOR_EMAIL" = "$OLD_EMAIL" ]
then
    export GIT_AUTHOR_NAME="$CORRECT_NAME"
    export GIT_AUTHOR_EMAIL="$CORRECT_EMAIL"
fi
' --tag-name-filter cat -- --branches --tags

# git push -f finish the magic
