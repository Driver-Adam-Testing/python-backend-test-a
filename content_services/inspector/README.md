# Inspector

This is a cloud-first version of inspector

To install the environment
```
poetry install --no-root
```

## Running from local computer (but executing in cloud)

Before running, edit main.py to point at your codebase of interest. Change the first path below and in the second, replace content-database with your codebase name. Obviously we'll pull code from s3 in production
```
LOCAL_CODEBASE_ROOT = Path("/Users/andrewmark/projects/content-database")
REMOTE_CODEBASE_ROOT = Path("/data/content-database")
```

From within the environment, you can run with
```
modal run --env=dev src/main.py codebase-id="<UUID>"
```

If you abort or crash, you can use the printed run ID and rerun
```
modal run --env=dev src/main.py resume-from-id="myuuid"
```

If you want to rerun parts of the tree, simply supply the path to the nodes. Any node that matches the path or is a child of the path will be rerun.
```
modal run --env=dev src/main.py --codebase-id="<UUID>" --rerun-paths="/path/1,/path/2"
```
## Deploying app service to cloud

```
modal deploy --env=dev src/main.py
```
