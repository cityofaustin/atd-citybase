# atd-citybase

## Development

In the `/root` directory, please:
* `docker-compose build` will build the task environment
* Edit `environment_variables.env` to contain the desired environment variables. See `environment_variables.env_template` for a template
* `docker-compose up -d` should start the app
* Edit files in place outside of the docker instance as usual when developing