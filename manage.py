#!python
import os
import boto3
from reports import create_app
from schema import task_schema, release_summary_schema, study_summary_schema

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

    print('Making task table')
    response = db.create_table(TableName=app.config['TASK_TABLE'],
                               **task_schema)

    print('Making release summary table')
    try:
        response = db.describe_table(
            TableName=app.config['RELEASE_SUMMARY_TABLE'])
    except:
        pass
    else:
        print('Table already exists')
        return
    response = db.create_table(TableName=app.config['RELEASE_SUMMARY_TABLE'],
                               **release_summary_schema)

    print('Making study summary table')
    try:
        response = db.describe_table(
            TableName=app.config['STUDY_SUMMARY_TABLE'])
    except:
        pass
    else:
        print('Table already exists')
        return
    response = db.create_table(TableName=app.config['STUDY_SUMMARY_TABLE'],
                               **study_summary_schema)


if __name__ == '__main__':
    app.run()
