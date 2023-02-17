# Advanced User Interface - Stress@Work

## Build Setup
You need to have python3-dev installed as pre-requisites.

First of all you need to create a virtualenv for the project, to do so we will
use [python3.10](https://www.python.org/downloads/) and [virtualenv](https://pypi.org/project/virtualenv/).

```bash
# Create the virtual env and use it
$ virtualenv .venv
$ source .venv/bin/activate

#Install the project requirements
$ pip install -r requirements.txt --no-cache-dir
```

You will also need to set up the database, go in /stressWork/stressWork/settings.py and adjust your settings based on the database you will use.

Then create and run the migrations and seeder in order to create the tables and populate your database.

```bash
# Navigate inside the project
$ cd stressWork

# Make and apply migrations
$ python manage.py makemigrations
$ python manage.py migrate

# Apply seeders
$ python manage.py loaddata */fixtures/*.json

```

Finally, you need to set up the env with the [Openface](https://github.com/TadasBaltrusaitis/OpenFace) and the [pre-trained model](https://www.dropbox.com/s/abiyfxo2c3a9jcu/pretrained-model.zip). You can refer to [this](https://zenodo.org/record/6569824#.Y-FLG-zML0r) work of Fabio Catania to understand how to save the model.

```bash
OPEN_FACE_EXEC_PATH=<path_to_FeatureExtraction_executable>
MODEL_PATH=<path_to_pretrained_model_folder>

# An example for mac users
# OPEN_FACE_EXEC_PATH=/Users/alessioferrara/git/stressWorkBack/OpenFace/build/bin/FeatureExtraction
# MODEL_PATH=/Users/alessioferrara/git/stressWorkBack/stressWork/content/model/pretrained-model
```

You can now start the backend server by running the command

```bash
# Starting using --noreload to avoid repetition on scheduler
$ python manage.py runserver --noreload
```

## Documentation

Further documentation can be found in the following pdf [file]()




