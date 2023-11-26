# Ansible Dynamic Inventory Script
Overview

This dynamic inventory script is designed to fetch host information from a specified database and generate an Ansible inventory dynamically. It's particularly useful for environments where hosts and their configurations are stored in a database and need to be retrieved for Ansible automation tasks. This script is compatible with Ansible Tower or AWX.

Requirements

    Ansible Tower or AWX environment for deployment.
    Python 3.x installed on the execution environment where the script will run.
    psycopg2 library installed for PostgreSQL database interaction.
    Access to a PostgreSQL database where host data is stored.

Setup and Configuration

    Install psycopg2 Library:
    Ensure psycopg2 is installed in your execution environment used on Ansible Tower/AWX.

    Environment Variables:
    The script uses environment variables for database connection parameters. Set the following environment variables:
        DB_NAME: Name of the database.
        DB_USERNAME: Username for the database.
        DB_PASSWORD: Password for the database.
        DB_HOSTNAME: Hostname of the database server.
        DB_PORT: Port number for the database.

    These variables should be configured in the Ansible Tower or AWX as custom credentials.

    Add the Script to Ansible Tower/AWX:
        Create a new project in Ansible Tower/AWX and link it to your repository where the script is stored.
        Add the script file to the project.

    Configure Inventory Source:
        In Ansible Tower/AWX, create a new inventory.
        Add a new inventory source to this inventory.
        Select "Sourced from a Project" as the source.
        Choose the project you created and select the script file as the inventory file.
        Save the inventory source configuration.

Usage

Once configured, the script will run within the Ansible Tower/AWX environment to dynamically generate the inventory from the specified database. The inventory will include hosts categorized based on the specified logic in the script, along with their relevant variables.

The script can be executed as part of an Ansible playbook or job template in Ansible Tower/AWX to utilize the dynamically generated inventory.

Troubleshooting

    Ensure all required environment variables are correctly set in the Ansible Tower/AWX.
    Verify database connectivity and permissions.
    Check the script logs for any errors during execution.

Contributing

For any enhancements, bug fixes, or contributions, please open an issue or a pull request in the repository where the script is hosted.
