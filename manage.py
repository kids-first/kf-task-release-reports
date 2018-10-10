#!python
import os
import boto3
from reports import create_app
from schema import task_schema

app = create_app()

@app.cli.command()
def migrate():
    endpoint_url = app.config['DYNAMO_ENDPOINT']
    db = boto3.client('dynamodb', endpoint_url=endpoint_url)

    try:
        response = db.describe_table(TableName=app.config['TASK_TABLE'])
    except:
        pass
    else:
        print('Table already exists')
        return

    print('Making table')
    response = db.create_table(TableName=app.config['TASK_TABLE'],
                               **task_schema)


if __name__ == '__main__':
    app.run()
