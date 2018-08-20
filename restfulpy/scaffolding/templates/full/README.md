# ${project_name.capitalize()}
A single sign-on application

![${project_name.capitalize()}](http://tadalafilforsale.net/data/media/1/51830280.jpg)

## Branches

### master


Setting up development Environment on Linux
----------------------------------

### Install Project (edit mode)

#### Working copy
    
    $ cd /path/to/workspace
    $ git clone git@github.com:Carrene/${project_name}.git
    $ cd ${project_name}
    $ pip install -e .
 
### Setup Database

#### Configuration

```yaml

db:
  url: postgresql://postgres:postgres@localhost/${project_name}_dev
  test_url: postgresql://postgres:postgres@localhost/${project_name}_test
  administrative_url: postgresql://postgres:postgres@localhost/postgres

messaging:
  default_messenger: restfulpy.messaging.SmtpProvider

smtp:
  host: mail.carrene.com
  port: 587
  username: nc@carrene.com
  password: <smtp-password>
  local_hostname: carrene.com
   
```

#### Remove old abd create a new database **TAKE CARE ABOUT USING THAT**

    $ ${project_name} db create --drop --mockup

And or

    $ ${project_name} db create --drop --basedata 

#### Drop old database: **TAKE CARE ABOUT USING THAT**

    $ ${project_name} [-c path/to/config.yml] db --drop

#### Create database

    $ ${project_name} [-c path/to/config.yml] db --create

Or, you can add `--drop` to drop the previously created database: **TAKE CARE ABOUT USING THAT**

    $ ${project_name} [-c path/to/config.yml] db create --drop

