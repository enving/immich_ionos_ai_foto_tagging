
https://docs.immich.app/install/docker-compose

Skip to main content
Immich Logo
Latest

Docs
Roadmap
API
Merch
GitHub
Discord

    Overview
    Install
        Requirements
        Install script [Experimental]
        Docker Compose [Recommended]
        Kubernetes
        Portainer
        Unraid
        One-Click [Cloud Service]
        All-In-One [Community]
        TrueNAS [Community]
        Synology [Community]
        Environment Variables
        Post installation steps
        Upgrading
        Config File
    Features
    Administration
    Developer
    Guides
    FAQ

    InstallDocker Compose [Recommended]

Docker Compose [Recommended]

Docker Compose is the recommended method to run Immich in production. Below are the steps to deploy Immich with Docker Compose.
Step 1 - Download the required files

Create a directory of your choice (e.g. ./immich-app) to hold the docker-compose.yml and .env files.
Move to the directory you created

mkdir ./immich-app
cd ./immich-app

Download docker-compose.yml and example.env by running the following commands:
Get docker-compose.yml file

wget -O docker-compose.yml https://github.com/immich-app/immich/releases/latest/download/docker-compose.yml

Get .env file

wget -O .env https://github.com/immich-app/immich/releases/latest/download/example.env

You can alternatively download these two files from your browser and move them to the directory that you created, in which case ensure that you rename example.env to .env.
Step 2 - Populate the .env file with custom values
Default environmental variable content

# You can find documentation for all the supported env variables at https://docs.immich.app/install/environment-variables

# The location where your uploaded files are stored
UPLOAD_LOCATION=./library

# The location where your database files are stored. Network shares are not supported for the database
DB_DATA_LOCATION=./postgres

# To set a timezone, uncomment the next line and change Etc/UTC to a TZ identifier from this list: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List
# TZ=Etc/UTC

# The Immich version to use. You can pin this to a specific version like "v2.1.0"
IMMICH_VERSION=v2

# Connection secret for postgres. You should change it to a random password
# Please use only the characters `A-Za-z0-9`, without special characters or spaces
DB_PASSWORD=postgres

# The values below this line do not need to be changed
###################################################################################
DB_USERNAME=postgres
DB_DATABASE_NAME=immich

    Populate UPLOAD_LOCATION with your preferred location for storing backup assets. It should be a new directory on the server with enough free space.
    Consider changing DB_PASSWORD to a custom value. Postgres is not publicly exposed, so this password is only used for local authentication. To avoid issues with Docker parsing this value, it is best to use only the characters A-Za-z0-9. pwgen is a handy utility for this.
    Set your timezone by uncommenting the TZ= line.
    Populate custom database information if necessary.

Step 3 - Start the containers

From the directory you created in Step 1 (which should now contain your customized docker-compose.yml and .env files), run the following command to start Immich as a background service:
Start the containers

docker compose up -d

Docker version

If you get an error such as unknown shorthand flag: 'd' in -d or open <location of your .env file>: permission denied, you are probably running the wrong Docker version. (This happens, for example, with the docker.io package in Ubuntu 22.04.3 LTS.) You can correct the problem by following the complete Docker Engine install procedure for your distribution, crucially the "Uninstall old versions" and "Install using the apt/rpm repository" sections. These replace the distro's Docker packages with Docker's official ones.

Note that the correct command really is docker compose, not docker-compose. If you try the latter on vanilla Ubuntu 22.04, it will fail in a different way:

The Compose file './docker-compose.yml' is invalid because:
'name' does not match any of the regexes: '^x-'

See the previous paragraph about installing from the official Docker repository.
Health check start interval

If you get an error can't set healthcheck.start_interval as feature require Docker Engine v25 or later, it helps to comment out the line for start_interval in the database section of the docker-compose.yml file.
Next Steps

Read the Post Installation steps and upgrade instructions.
Edit this page
Last updated on Sep 25, 2025 by Zack Pollard
Previous
Install script [Experimental]
Next
Kubernetes

    Step 1 - Download the required files
    Step 2 - Populate the .env file with custom values
    Step 3 - Start the containers
    Next Steps

Overview

    Quick start
    Installation
    Contributing
    Privacy Policy

Documentation

    Roadmap
    API
    Cursed Knowledge

Links

    GitHub
    YouTube
    Discord
    Reddit

Immich is available as open source under the terms of the GNU AGPL v3 License.
