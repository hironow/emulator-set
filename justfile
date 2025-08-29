# https://just.systems

default:
    echo 'Hello, world!'

update:
    @echo 'Updating...'
    uv lock --upgrade
    uv sync
    @echo 'Updated.'