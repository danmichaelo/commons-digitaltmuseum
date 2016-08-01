
## Setup

```
virtualenv ENV
. ENV/bin/activate
pip install -U -e .
crontab < crontab
```

## Development server:

```
uwsgi --http :5000 \
    --venv ENV \
    --manage-script-name
    --mount /digitaltmuseum=digitaltmuseum.wsgi:app
```

