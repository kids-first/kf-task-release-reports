<p align="center">
  <img src="docs/release_reports_logo.png" alt="Release Reports">
</p>
<p align="center">
  <a herf="https://github.com/kids-first/kf-task-release-reports/blob/master/LICENSE"><img src="https://img.shields.io/github/license/kids-first/kf-task-release-reports.svg?style=for-the-badge"></a>
  <a href="http://kids-first.github.io/kf-task-release-reports/"><img src="https://img.shields.io/readthedocs/pip.svg?style=for-the-badge"></a>
  <a href="https://circleci.com/gh/kids-first/kf-task-release-reports"><img src="https://img.shields.io/circleci/project/github/kids-first/kf-task-release-reports/master.svg?style=for-the-badge"></a>
  <a href="https://app.codacy.com/app/kids-first/kf-task-release-reports/dashboard"><img src="https://img.shields.io/codacy/grade/0de29994bc124aa98971d985aaadf5ea/master.svg?style=for-the-badge"></a>
</p>

# Kids First Release Report Task Service

The Release Report task service runs as part of a release to summarize the
release being made into a tidy report.


## Design

The Release Report Service follows the [Task Service spec](https://kids-first.github.io/kf-api-release-coordinator/docs/task.html)
outlined by the Release Coordinator.

### Tables

The Release Reports Service stores statistics about each report in various tables in dynamo. Below is the schema for each:

#### Task

The task table stores logistics information about each task.

| release_id | task_id | created_at | state |
|------------|---------|------------|-------|


#### Release Summary

The release summary stores information about aggregate counts for each entity

| release_id | task_id | created_at | version | state | studies | participants | ... |
|------------|---------|------------|---------|-------|---------|--------------|-----|


#### Study Summary

The study summary stores information about aggregate counts for each entity for a given study in a given release.

| study_id | release_id| release_id | task_id | created_at | version | state | participants | ... |
|----------|-----------|------------|---------|------------|---------|-------|--------------|-----|
