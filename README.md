# Git Deployments

A minimal Django app to handle GitHub webhooks and start deployments on self-hosted applications.

## Usage

On your server, start by creating a directory to install the **gitd** utility:

```
mkdir /opt/gitd
```

Inside the **/opt/gitd** directory, clone the repository using git:

```
git clone https://github.com/vitorfs/gitd.git
```

Create a virtualenv to install the dependencies using Python 3:

```
virtualenv venv -p python3
```

Activate the venv:

```
source venv/bin/activate
```

Go to the git repository directory:

```
cd /opt/gitd/gitd
```

Install the dependencies:

```
pip install -r requirements.txt
```

Migrate the SQLite database:

```
python manage.py migrate
```

Create a .env file to add your configuration:

**.env**

```
SECRET_KEY=CREATE_A_LONG_AND_RANDOM_STRING
DEBUG=False
ALLOWED_HOSTS=.example.com
TIME_ZONE=UTC
LANGUAGE_CODE=en-us
GITHUB_WEBHOOK_KEY=YOUR_SECRET_GITHUB_KEY_HERE
GITHUB_REPOSITORY=example/hello-world
GITHUB_BRANCH=refs/heads/main
GITD_DEPLOYMENT_COMMAND=/opt/gitd/deploy
```

Inside the **/opt/gitd** directory, add a **run** and **logs** directory:

```
mkdir run logs
```

Initialize a log file for the Gunicorn worker:

```
touch logs/gitd-worker.log
```

Add a **gunicorn_start** script inside **/opt/gitd**:

```
touch gunicorn_start
```

Add the commands to start the Gunicorn worker:

```
#!/bin/bash

NAME="gitd"
DIR=/opt/gitd/gitd
USER=ubuntu
GROUP=ubuntu
WORKERS=3
BIND=unix:/opt/gitd/run/gunicorn.sock
DJANGO_SETTINGS_MODULE=gitd.settings
DJANGO_WSGI_MODULE=gitd.wsgi
LOG_LEVEL=error

source /opt/gitd/venv/bin/activate

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DIR:$PYTHONPATH

exec /opt/gitd/venv/bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $WORKERS \
  --user=$USER \
  --group=$GROUP \
  --bind=$BIND \
  --log-level=$LOG_LEVEL \
  --log-file=-
```

Note that you may need to change the `USER` and `GROUP` but it needs to have higher privilege as the worker may need to execute commands on the machine to start the deployment.

Make it executable:

```
chmod u+x gunicorn_start
```

Add your deployment script:

```
touch deploy
```

```
#!/bin/bash

su - example_user -c "git -C ~/example_app pull origin master"
su - example_user -c "~/venv/bin/pip install -r ~/example_app/requirements.txt"
su - example_user -c "~/venv/bin/python ~/example_app/manage.py migrate"
su - example_user -c "~/venv/bin/python ~/example_app/manage.py collectstatic --noinput"

sudo supervisorctl restart example_app

exit 0
```

Make it executable:

```
chmod u+x deploy
```

The contents of the `deploy` script really depends on what kind of app you are running, what routines you must run upon a new deploy. So it is up to you to create this file. The example above is a script for deploying a Django application.

Update your NGINX/Apache conf to handle requests to `__gitd__` path, the example below it is a configuration for NGINX:

```
upstream gitd_app_server {
    server unix:/opt/gitd/run/gunicorn.sock fail_timeout=0;
}

server {
    ...

    location /__gitd__/ {
        proxy_set_header Host $http_host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_redirect off;
        proxy_pass http://gitd_app_server;
    }

    ...
}
```

Here we are making use for the apps own IP address or domain.

Now we can use supervisor to monitor and start the `gunicorn_start` command if the server reboots.

```
sudo apt-get -y install supervisor
sudo systemctl enable supervisor
sudo systemctl start supervisor
```

Create a supervisor conf file:

**/etc/supervisor/conf.d/gitd.conf**

```
[program:gitd]
command=/opt/gitd/gunicorn_start
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/gitd/logs/gitd-worker.log
```

Run the supervisor commands to discover the new app:

```
supervisorctl reread
sudo supervisorctl update
```

Restart the web server (NGINX in our example):

```
sudo service nginx restart
```

Now your server is ready to receive webhooks to initialize a deployment.

By now you may have realised that perhaps this is not the easiest solution to automate deploys. But I can't help, I like writing stuff with Django.

## License

The source code is released under the [MIT License](https://github.com/vitorfs/gitd/blob/master/LICENSE).
