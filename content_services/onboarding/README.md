# Codebase Onboarding

This repository contains ported functionality from `codebase-onboarding-lambda` to unpack, reupload and create appropriate database entries when a codebase is uploaded.

New functionality added beyond the porting of the old onboarding logic includes:
* Detection of binary/unprocessable files
* Reencoding of all processable files into UTF-8, if needed
* Analysis of all files (size and sloc)

To install the environment:
```
poetry install
```

## Running Sample
```
modal run --env-dev src/codebase_onboarding.py
```

Currently works for zips under the `codebases` folder of the `modal-dev-inspector-1234442` bucket.

## Analysis and Onboarding Flow
1. Download zip from S3
2. Identify root structure and unpack zip
3. (TODO) Create codebase record in db
4. For each file:
    * Identify if the file is binary/processable
    * Reencode the file to UTF-8
    * Do the file analysis (size, SLOC)
    * Upload the file to S3
    * (TODO) Create source content record in db
5. (TODO) Create source contet record for each directory
