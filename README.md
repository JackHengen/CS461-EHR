To setup the necessary libraries for flaskapp and data generation:
```
python -m venv venv # create a virtual environment
source ./venv/bin/activate # depending on os you may have to source a different file extension in the same folder
pip install -r requirements.txt
```

To generate new mock database data:
```
echo "OPENAI_API_KEY=<<YOUR OPEN API KEY HERE" > .env
python data/data_gen_pipeline.py > insertions.sql
```

To create the database:
```
mysql < data/tables.sql
mysql < data/insertions.sql
mysql < data/user_setup.sql
```

To run the flask app:
```
flask --app app.app run
```
