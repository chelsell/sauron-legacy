# Goldberry installation

## Table of Contents 
* [Setting up Airflow](#setup_airflow)
  * [Creating the Conda Environment ](#conda_env)
  * [Setting up the Airflow Database](#airflow_db)
  * [Setting up the correct DB configurations](#db_config)
  * [Add the Dags_to_create table](#dags_to_create)
  * [Set Airflow configs for use with Goldberry](#goldberry)

<a name="setup_airflow"/>

## Setting up Airflow

Goldberry relies on [Airflow](https://airflow.apache.org/) to schedule its tasks. Follow these instructions to set up Airflow for use on a machine (e.g: Valinor/Celebrant). 

<a name="conda_env"/>

### Creating the Conda Environment 
1. Create a conda environment named airflow. 
```conda create --name airflow python=3.7```
2. Run `sudo apt-get install python-dev` ,`sudo apt-get install gcc`,`sudo apt-get install libmysqlclient-dev`, `sudo apt-get install p7zip-full`, `sudo apt-get install ffmpeg` so that you have the necessary dependencies to install `airflow`. 
3. Switch to the airflow environment and then install airflow and slackclient with pip.
    ```
    conda activate airflow 
    pip install apache-airflow 
    pip install slackclient==1.3.1
    pip install mysqlclient

    ```
4. Create/export an environment variable that specifies where the airflow home (e.g: /var/airflow) will be.
    ```
    export AIRFLOW_HOME = /path_where_you_want_airflow_home_to_be
    ```
    With the above command, the environment variable isn't permanent so I recommend adding this to the `.bash_profile` so      that you don't have to repeat the command for every terminal instance. 

<a name="airflow_db"/>

### Setting up the Airflow Database

1. Create the `airflow` database that will be used. 
    ```
    mysql -u root
    mysql> CREATE DATABASE airflow CHARACTER SET utf8 COLLATE utf8_unicode_ci;
    mysql> create user 'airflow'@'localhost' identified by 'INSERT_PASSWORD_HERE';
    mysql> grant all privileges on airflow.* to 'airflow'@'localhost';
    mysql> flush privileges;
    ```
    This creates a database user `airflow` with the password `INSERT_PASSWORD_HERE`. 
2. Activate the `airflow` environment and then run the `initdb` command. This will instantiate some airflow files (e.g: `airflow.cfg`) and set up the default Airflow DB which uses `sqlite`. We can't use `sqlite` as it prevents the processing of multiple dags (e.g: submissions) at the same time. 
    ```
    conda activate airflow
    airflow initdb
    ```
3. Open up the `$AIRFLOW_HOME/airflow.cfg` file on a text editor and change the executor from `CeleryExecutor` to `LocalExecutor`. Also, set the `sql_alchemy_conn` to have the correct database credentials. 
   ```
   executor = LocalExecutor
   sql_alchemy_conn = mysql://airflow:INSERT_PASSWORD_CHOSEN_IN_STEP_FIVE@localhost:3306/airflow
   ```
4. Initialize the Airflow DB again to reflect the changes you made. This will make `mysql/mariadb` the primary db and allow you to have multiple dags running at the same time. 
    ```
    airflow initdb
    ```
    
<a name="db_config"/>

### Setting up the correct DB configurations
After the Airflow DB is initialized, you will most likely be prompted to set the global variable explicit_defaults_for_timestamp. Make the following changes to the `my.cnf` file. 
1. Open up the MariaDB configuration file in a text editor of your choice. 
    ```
    vim /etc/mysql/my.cnf
    ```
2. Under the section `[mysqld]`, add the following settings: 
    ```
    wait_timeout = 604800
    interactive_timeout = 604800 
    max_allowed_packet=2GB
    explicit_defaults_for_timestamp = 1
    default-time-zone='-7:00'
    ```
    If the section doesn't exist, add it to the file and put the settings below it. 
3. Under the section `[mysqldump]`, add the following settings: 
    ```
    [mysqldump]
    max_allowed_packet=2GB
    ```
4. Restart MariaDB.
    ```
    systemctl restart mariadb.service
    ```
    
<a name="dags_to_create"/>    
    
### Add the Dags_to_create table
1. Refer to the table_create.sql file under goldberry/scripts/valar. Create the dags_to_create table in the valar database. Import it or just run the command from mysql. 
    ```
    mysql -u root
    mysql>CREATE TABLE `dags_to_create` (
  	`id` mediumint(8) unsigned NOT NULL AUTO_INCREMENT,
  	`submission_hash` char(12) NOT NULL,
  	`dag_created` tinyint(1) NOT NULL default 0,
  	`created` timestamp NOT NULL DEFAULT current_timestamp(),
  	PRIMARY KEY (`id`),
  	UNIQUE KEY `id_hash_hex` (`submission_hash`)
	)
    ```

<a name="goldberry"/>    

### Set Airflow configs for use with Goldberry
1. (OPTIONAL, but recommended) Get rid of airflow example dags with https://stackoverflow.com/questions/43410836/how-to-remove-default-example-dags-in-airflow. 
2. Run the webserver command on Celebrant/Valinor. 
    ```
    airflow webserver -p 8080  #ANY PORT is fine
    ```
3. Set up an ssh tunnel from your machine to valinor.
    ```
    ssh -L 7777:localhost:8080 valinor
    ```
4. Navigate to the following URL `http://localhost:7777/admin/connection/` and you will see the airflow UI. 
5. Go to Admin > Connections > Create and Create a connection called `airflow_db` with the settings shown in the picture below. 
![Screen Shot 2019-09-26 at 6 18 23 PM](https://user-images.githubusercontent.com/10649054/65734962-32914280-e08a-11e9-9c6d-d3242c2a5252.png)
6. Create another connection called `dag_db`. 
![Screen Shot 2019-09-26 at 6 22 00 PM](https://user-images.githubusercontent.com/10649054/65735064-8bf97180-e08a-11e9-9dfc-45b108d11e08.png)
Fill out the `login` field with the mysql user and `password` field with the password for the user. 
7. Create the last connection called `slack`. 
![Screen Shot 2019-09-26 at 6 23 28 PM](https://user-images.githubusercontent.com/10649054/65735099-c6630e80-e08a-11e9-8595-b5d8dab5ce42.png)
Fill out the `password` field with the slack token.
8. Go to Admin > Pools > Create and add the following Pools:
Add the following pools under admin/pools:
	- insertion_pool (6 slots)
	- archive_pool (3 slots)

Congrats! Goldberry-airflow should now be ready-to-go!
