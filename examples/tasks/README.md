# Example tasks

[This](task-psutil.json) example task will collect metrics from **psutil** and publish 
them to file.  

## Running the example

### Requirements 
 * `docker` and `docker-compose` are **installed** and **configured** 

Running the sample is as *easy* as running the script `./run-mock-psutil.sh`. 

## Files

- [run-mock-psutil.sh](run-mock-psutil.sh) 
    - The example is launched with this script
- [mock-psutil.sh](mock-psutil.sh)
    - Downloads `snapd`, `snapctl`, `snap-plugin-collector-psutil`,
    `snap-plugin-publisher-mock-file`, `snap-plugin-processor-passthru` and starts the task
    [task-psutil.json](task-mpsutil.json).
- [task-psutil.json](task-psutil.json)
    - Snap task definition
- [.setup.sh](.setup.sh)
    - Verifies dependencies and starts the containers.  It's called 
    by [run-mock-psutil.sh](run-mock-psutil.sh).